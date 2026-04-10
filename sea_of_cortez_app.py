import pandas as pd
import numpy as np
import duckdb
import holoviews as hv
import panel as pn
import geoviews as gv
import geoviews.tile_sources as gvts
import gsw  
import cartopy.crs as ccrs 
from io import BytesIO

# 1. ENGINE INITIALIZATION
pn.extension('tabulator', ready_notification=True)
hv.extension('bokeh')
gv.extension('bokeh')

# 2. DATABASE CONNECTION
DB_PATH = "processed/sea_of_cortez.duckdb"
con = duckdb.connect(DB_PATH, read_only=True)

# Metadata - Fetch only valid station names and SORT ALPHABETICALLY
raw_stations = con.execute("""
    SELECT DISTINCT station_id FROM wf_ctd_binned 
    WHERE station_id IS NOT NULL AND station_id != ''
""").df()['station_id'].tolist()

stations = sorted(raw_stations) # Alphabetical sort applied here

all_coords = con.execute("""
    SELECT DISTINCT station_id, lat, lon FROM wf_ctd_binned 
    WHERE station_id IS NOT NULL AND station_id != ''
""").df()

# 3. GLOBAL WIDGETS
station_select = pn.widgets.Select(name='⚓ Station ID', options=stations, value=stations[0])
depth_slider = pn.widgets.RangeSlider(name='📏 Depth Range (m)', start=0, end=600, value=(0, 500), step=1)
qc_toggle = pn.widgets.Toggle(name='🛡️ Filter QC (Flag < 3)', value=True, button_type='success', sizing_mode='stretch_width')

# 4. DATA LOGIC (TEOS-10 Engine with QC Filtering)
@pn.depends(station_select, depth_slider, qc_toggle)
def get_clean_df(target_id, z_range, filter_qc):
    qc_clause = "AND qc_flag < 3" if filter_qc else ""
    query = f"""
        SELECT * FROM wf_ctd_binned 
        WHERE station_id='{target_id}' 
        AND depth_m BETWEEN {z_range[0]} AND {z_range[1]}
        {qc_clause}
        ORDER BY depth_m ASC
    """
    df = con.execute(query).df()
    if df.empty: return pd.DataFrame()
        
    cols = ['CT', 'SA', 'o2_final', 'ph_final', 'chl_final', 'n2', 'depth_m', 'lat', 'lon']
    # Ensure columns exist before applying numeric conversion
    existing_cols = [c for c in cols if c in df.columns]
    df[existing_cols] = df[existing_cols].apply(pd.to_numeric, errors='coerce')
    df = df.dropna(subset=['depth_m', 'CT', 'SA'])
    
    # Physics Engine (TEOS-10)
    df['sigma'] = gsw.sigma0(df['SA'], df['CT'])
    df['sat_o2'] = gsw.O2sol_SP_pt(df['SA'], df['CT']) 
    df['AOU'] = df['sat_o2'] - df['o2_final'] 
    
    # Metabolic Index (Habitability)
    k, Eo = 8.617e-5, 0.45    
    df['phi'] = (df['o2_final'] / np.exp(-Eo / (k * (df['CT'] + 273.15)))) / 1e6 
    return df

def download_csv():
    df = get_clean_df(station_select.value, depth_slider.value, qc_toggle.value)
    sio = BytesIO()
    df.to_csv(sio, index=False)
    sio.seek(0)
    return sio

csv_button = pn.widgets.FileDownload(
    callback=download_csv, filename='western_flyer_research_export.csv', 
    label='📥 Export CSV', button_type='primary', sizing_mode='stretch_width'
)

# 5. TAB FUNCTIONS

def view_cruise_summary():
    """Master Mission Log with Health Progress Bars"""
    query = """
        SELECT 
            station_id as "Station ID", 
            MIN(time_iso)::TIMESTAMP as "Start Time (UTC)",
            CAST(MAX(depth_m) AS DECIMAL(10,1)) as "Max Depth (m)",
            ROUND((SUM(CASE WHEN qc_flag = 1 THEN 1 ELSE 0 END) * 100.0) / COUNT(*), 1) as "Health %",
            ROUND((SUM(CASE WHEN qc_flag = 3 THEN 1 ELSE 0 END) * 100.0) / COUNT(*), 1) as "Suspect %",
            ROUND((SUM(CASE WHEN qc_flag = 4 THEN 1 ELSE 0 END) * 100.0) / COUNT(*), 1) as "Bad %"
        FROM wf_ctd_binned 
        WHERE station_id IS NOT NULL AND station_id != ''
        GROUP BY station_id
        ORDER BY "Start Time (UTC)" ASC
    """
    df = con.execute(query).df()
    df['Date'] = df['Start Time (UTC)'].dt.strftime('%Y-%m-%d')
    df['Time'] = df['Start Time (UTC)'].dt.strftime('%H:%M')
    df = df[['Station ID', 'Date', 'Time', 'Max Depth (m)', 'Health %', 'Suspect %', 'Bad %']]
    
    return pn.widgets.Tabulator(
        df, theme='midnight', sizing_mode='stretch_width', show_index=False,
        configuration={
            'columnDefaults': {'headerSort': True},
            'columns': [
                {'field': 'Health %', 'formatter': 'progress', 'formatterParams': {'color': ['#ff4d4d', '#ffa64d', '#00f2ff'], 'min': 0, 'max': 100}}
            ]
        }
    )

@pn.depends(station_select, depth_slider, qc_toggle)
def view_profiles(target_id, z_range, filter_qc):
    df = get_clean_df(target_id, z_range, filter_qc)
    if df.empty: return pn.pane.Alert("Data filtered out.", alert_type='warning')
    v_opts = dict(invert_yaxis=True, height=550, show_grid=True, xaxis='top', tools=['hover'], 
                  yticks=5, xticks=3, fontsize={'labels': '9pt', 'xticks': '7pt'}, padding=0.05)
    p1 = hv.Curve(df, 'CT', 'depth_m', label='Temp').opts(**v_opts, color='blue', width=165, xlabel='°C')
    p2 = hv.Curve(df, 'SA', 'depth_m', label='Salinity').opts(**v_opts, color='red', width=135, yaxis=None, xlabel='g/kg')
    p3 = hv.Curve(df, 'o2_final', 'depth_m', label='Oxygen').opts(**v_opts, color='black', width=145, yaxis=None, xlabel='µmol/kg')
    p4 = hv.Curve(df, 'ph_final', 'depth_m', label='pH').opts(**v_opts, color='orange', width=120, yaxis=None, xlabel='Total')
    p5 = hv.Curve(df, 'chl_final', 'depth_m', label='Chl').opts(**v_opts, color='green', width=120, yaxis=None, xlabel='mg/m³')
    return (p1 + p2 + p3 + p4 + p5).cols(5).opts(shared_axes=True, merge_tools=True)

@pn.depends(station_select, depth_slider, qc_toggle)
def view_ts_analysis(target_id, z_range, filter_qc):
    df = get_clean_df(target_id, z_range, filter_qc)
    if df.empty: return pn.pane.Alert("Data filtered out.", alert_type='warning')
    return hv.Points(df, ['SA', 'CT'], ['depth_m', 'sigma']).opts(
        color='depth_m', cmap='Viridis_r', size=8, width=600, height=500, colorbar=True,
        show_grid=True, title="T-S Analysis", xlabel="Salinity (g/kg)", ylabel="Temp (°C)")

@pn.depends(station_select, depth_slider, qc_toggle)
def view_aou(target_id, z_range, filter_qc):
    df = get_clean_df(target_id, z_range, filter_qc)
    if df.empty: return pn.pane.Alert("Data Null", alert_type='warning')
    opts = dict(invert_yaxis=True, height=550, width=600, show_grid=True)
    sat_l = hv.Curve(df, 'sat_o2', 'depth_m', label='Sat. Cap').opts(**opts, color='black', line_dash='dashed')
    o2_l = hv.Curve(df, 'o2_final', 'depth_m', label='Observed').opts(**opts, color='cyan')
    fill = hv.Area(df, ('sat_o2', 'o2_final'), 'depth_m', label='AOU').opts(**opts, color='orange', alpha=0.3)
    return (fill * sat_l * o2_l).opts(title="Apparent Oxygen Utilization (AOU)", show_legend=True)

@pn.depends(station_select, depth_slider, qc_toggle)
def view_stability(target_id, z_range, filter_qc):
    df = get_clean_df(target_id, z_range, filter_qc)
    if df.empty: return pn.pane.Alert("Data Null", alert_type='warning')
    surf = df['sigma'].iloc[0]; mld_idx = (df['sigma'] - surf > 0.03).idxmax()
    mld_v = df.loc[mld_idx, 'depth_m'] if mld_idx in df.index else 0
    v_opts = dict(invert_yaxis=True, height=500, width=400, show_grid=True)
    sig = hv.Curve(df, 'sigma', 'depth_m', label='Density').opts(**v_opts, color='white', xlabel='kg/m³')
    mld = hv.HLine(mld_v, label=f'MLD: {mld_v:.1f}m').opts(color='red', line_dash='dashed')
    n2 = hv.Area(df, 'n2', 'depth_m', label='Stability').opts(**v_opts, color='magenta', alpha=0.2)
    return pn.Row((sig * mld), n2)

@pn.depends(station_select, depth_slider, qc_toggle)
def view_metabolic_index(target_id, z_range, filter_qc):
    df = get_clean_df(target_id, z_range, filter_qc)
    if df.empty: return pn.pane.Alert("Data Null", alert_type='warning')
    p = hv.Curve(df, 'phi', 'depth_m', label='Φ').opts(color='#e67e22', invert_yaxis=True, height=550, width=500)
    l = hv.VLine(1.0, label='Limit').opts(color='red', line_dash='dashed')
    return (p * l).opts(show_legend=True, title="Habitability (Metabolic Index)")

@pn.depends(station_select)
def view_map_geolocation(target_id):
    try:
        base = gvts.EsriOceanBase.opts(width=900, height=600); labels = gvts.EsriOceanReference
    except:
        base = gvts.OSM.opts(width=900, height=600); labels = gv.Feature(gv.feature.coastline).opts(line_color='black')
    
    pts = gv.Points(all_coords, ['lon', 'lat'], vdims=['station_id'], crs=ccrs.PlateCarree()).opts(
        size=8, color='#f1c40f', alpha=0.5, tools=['hover']
    )
    
    curr = all_coords[all_coords['station_id'] == target_id]
    sel = gv.Points(curr, ['lon', 'lat'], vdims=['station_id'], crs=ccrs.PlateCarree()).opts(
        size=18, color='#ff3f34', marker='circle', line_color='white', tools=['hover']
    )
    
    return (base * labels * pts * sel).opts(title="Research Geolocation & Bathymetry", padding=0.3)

@pn.depends(station_select, depth_slider, qc_toggle)
def view_tabular_data(target_id, z_range, filter_qc):
    df = get_clean_df(target_id, z_range, filter_qc)
    return pn.widgets.Tabulator(df, pagination='remote', page_size=15, theme='midnight')

# 6. ASSEMBLY
tabs = pn.Tabs(
    ("Vertical Profiles", view_profiles),
    ("T-S Analysis", view_ts_analysis),
    ("Oxygen Utilization (AOU)", view_aou),
    ("Stability & MLD", view_stability),
    ("Metabolic Index", view_metabolic_index),
    ("Geolocation", view_map_geolocation),
    ("Tabular Data", view_tabular_data),
    ("Cruise Summary", view_cruise_summary()), 
    dynamic=True, active=0
)

dashboard = pn.template.FastListTemplate(
    title="Western Flyer - Sea of Cortez (2025)",
    sidebar=[station_select, depth_slider, qc_toggle, pn.pane.Markdown("---"), csv_button],
    main=[tabs], accent_base_color="#00f2ff", header_background="#1a1a1a",
)

dashboard.servable()