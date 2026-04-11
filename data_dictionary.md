# Sea of Cortez (2025): Data Dictionary

**File Name:** `data_dictionary.md`  
**Version:** 1.0.0  
**Project:** Western Flyer - Sea of Cortez (Baja 2025)  
**Database Table:** `wf_ctd_binned`

---

## 1. Overview
This data dictionary describes the schema for the `wf_ctd_binned` table within the `sea_of_cortez.duckdb` database. This table contains high-resolution, processed oceanographic data derived from Sea-Bird Scientific SBE19plus `.cnv` files. 

All physical parameters have been calculated using the **TEOS-10** (Thermodynamic Equation of Seawater 2010) standard. The data has been quality-controlled for ship heave, filtered via Savitzky-Golay smoothing, and vertically binned to a resolution of **0.1 dbar**.

---

## 2. Core Metadata & Geospatial Identifiers
These columns identify the specific research event, temporal context, and geographic location.

| Column Name | Data Type | Units | Description |
| :--- | :--- | :--- | :--- |
| `station_id` | VARCHAR | - | Unique identifier (e.g., `PuntaMarciel_C4`). A combination of the Station Name and Cast Number. |
| `station_name` | VARCHAR | - | Descriptive name of the deployment site. |
| `cast_no` | INTEGER | - | Sequential number of the deployment (Cast) at a specific station. |
| `lat` | DOUBLE | Decimal Deg | Decimal Latitude (North is positive). |
| `lon` | DOUBLE | Decimal Deg | Decimal Longitude (East is positive; West is negative). |
| `time_iso` | TIMESTAMP | ISO 8601 | The UTC timestamp of the observation. |
| `time_elapsed` | DOUBLE | Seconds | Seconds elapsed since the start of the CTD cast. |

---

## 3. Primary Physical Oceanography
Fundamental physical variables calculated via the Gibbs SeaWater (GSW) toolbox.

| Column Name | Data Type | Units | Description |
| :--- | :--- | :--- | :--- |
| `dbar_bin` | DOUBLE | dbar | **Primary Coordinate.** The pressure bin (0.1 resolution). Roughly equivalent to meters in the upper water column. |
| `depth_m` | DOUBLE | meters | Calculated vertical coordinate (positive downward) derived from pressure and latitude. |
| `CT` | DOUBLE | °C | **Conservative Temperature.** Represents the true heat content of the water parcel (Enthalpy). |
| `SA` | DOUBLE | g/kg | **Absolute Salinity.** The mass fraction of salt, including corrections for local composition anomalies. |
| `SP` | DOUBLE | PSU | **Practical Salinity.** Calculated from conductivity ratios (Legacy EOS-80 standard). |
| `rho` | DOUBLE | kg/m³ | **In-situ Density.** The actual density of the water at its current pressure and temperature. |
| `sigma0` | DOUBLE | kg/m³ | **Potential Density Anomaly.** Density if raised to the surface (0 dbar), minus 1000. Used for water mass identification. |

---

## 4. Derived Dynamics & Biogeochemicals
Columns representing the biological and structural properties of the water column.

| Column Name | Data Type | Units | Description |
| :--- | :--- | :--- | :--- |
| `o2_final` | DOUBLE | µmol/kg | **Dissolved Oxygen.** Mass-normalized concentration (corrected for in-situ density). |
| `ph_final` | DOUBLE | Total Scale | **pH.** Ocean acidity measured on the total hydrogen ion scale. |
| `chl_final` | DOUBLE | mg/m³ | **Chlorophyll-a.** Estimates of phytoplankton biomass (corrected for sensor dark-count offsets). |
| `n2` | DOUBLE | rad²/s² | **Brunt-Väisälä Frequency.** The square of the buoyancy frequency; a measure of water column stability. |
| `spice` | DOUBLE | - | **Spiciness.** State variable for water masses with identical densities but different T/S signatures. |
| `sound_speed` | DOUBLE | m/s | Speed of sound at depth, calculated for acoustic propagation modeling. |

---

## 5. Quality Control & Pipeline Integrity
Internal markers used to ensure data validity and track processing lineage.

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `dp` | DOUBLE | **Descent Rate.** The change in pressure per scan. Used to identify and filter ship heave/wake contamination. |
| `qc_flag` | INTEGER | **Quality Flag.** (1 = Pass, 3 = Suspect/Density Inversion, 4 = Fail/Out of Physical Range). |
| `pipeline_version` | VARCHAR | The specific version of the `wf_ctd_build` processing engine used to generate the row. |

---

## 6. Usage Notes
* **Missing Values:** Represented as `NULL` or `NaN`.
* **Deployment Direction:** This dataset consists exclusively of **Downcast** data. Upcast data is removed to avoid turbulence artifacts from the rosette frame.
* **Geodetic Datum:** All geospatial coordinates refer to the **WGS84** ellipsoid.