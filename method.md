# Methodology: Sea of Cortez CTD Analytical Pipeline

This document provides a comprehensive technical breakdown of the mathematical, physical, and chemical transformations applied to the raw Sea-Bird Electronics (SBE) data within the `wf_ctd_build` pipeline.

---

## 1. Temporal Alignment & Phase Correction
In high-resolution CTD profiling, sub-second timing is critical. Because sensors are physically distributed across the rosette frame and water is drawn through a plumbing circuit by a pump, different sensors sample the same parcel of water at different times.

* **Conductivity Thermal Alignment:** The conductivity cell has a slight thermal inertia compared to the ultra-fast thermistor. By shifting conductivity by **1 scan**, we synchronize the salinity calculation to the exact temperature of the water parcel. This prevents "salinity spikes"—artificial fluctuations caused by mismatched T-C response times when passing through sharp gradients.
* **The SBE-43 Oxygen Lag:** The dissolved oxygen sensor relies on a chemical reaction across a polarographic membrane. This diffusion process creates a physical delay in signal response. We apply a forward shift of **8 scans** (~3–4 seconds). Failure to apply this shift results in vertical "hysteresis," where the oxygen profile appears deeper or shallower than the corresponding temperature and density features.

---

## 2. Geophysical Thermodynamics (TEOS-10)
This pipeline abandons the legacy EOS-80 (Practical Salinity) standard in favor of the **TEOS-10 (Thermodynamic Equation of Seawater - 2010)**. TEOS-10 uses the **Gibbs Function** of seawater to derive all properties, ensuring energy-consistent calculations of heat, entropy, and density.

### 2.1 The Salinity Hierarchy
Salinity is no longer treated as a simple ratio of conductivity. We process it through a multi-stage correction:
1.  **Practical Salinity ($S_P$):** Calculated via the ratio of seawater conductivity to a standard $KCl$ solution. This represents the ionic conductivity of the water but ignores non-conducting dissolved solids.
2.  **Absolute Salinity ($S_A$):** This is the actual mass fraction of salt in seawater. Because the "recipe" of salt changes globally, we use the **Global Composition Anomaly** database. By providing the exact Latitude and Longitude of the *Western Flyer*, the pipeline adjusts for local mineral variations unique to the Sea of Cortez.
    $$S_A = S_P + \delta S_A(x, y, p)$$



### 2.2 Conservative Temperature ($\Theta$)
Standard "in-situ" temperature changes simply because water is compressed as it sinks (adiabatic compression). To track the true heat content of a water mass, we convert to **Conservative Temperature**. Unlike Potential Temperature, Conservative Temperature is proportional to the **Enthalpy** of seawater, making it a more accurate tracer for heat-budget studies and water mass mixing.

### 2.3 Potential Density ($\sigma_0$) & Stability
* **Density Anomaly ($\sigma_0$):** Calculated as the in-situ density minus $1000 \, \text{kg/m}^3$ if the water were moved to the sea surface. This allows us to identify water mass boundaries, such as the transition between Tropical Surface Water and Gulf of California Water.
* **Brunt-Väisälä Frequency ($N^2$):** This measures the "stiffness" of the stratification. A high $N^2$ value indicates a strong pycnocline where vertical mixing is suppressed. In the Sea of Cortez, this is critical for identifying the depth of the "Nutricline."
    $$N^2 = \frac{g}{\rho} \frac{\partial \rho}{\partial z}$$

---

## 3. Biogeochemical Normalization
The CTD measures Dissolved Oxygen ($O_2$) in volume-based units ($\mu\text{mol/L}$). However, because water is compressible, a "liter" at 500m depth contains more molecules than a "liter" at the surface, even if the concentration relative to the water mass is the same.

To allow for meaningful comparison across the vertical water column, we normalize by **mass**. By dividing the concentration by the calculated in-situ density ($\rho$), we derive the mass-normalized value:
$$O_{2\text{mass}} = O_{2\text{vol}} \times \frac{1000}{\rho}$$
This transformation is essential for accurately calculating the boundaries of **Oxygen Minimum Zones (OMZ)**, a dominant feature of the Sea of Cortez ecology.

---

## 4. Signal Processing: The "Silk" Filter
Raw CTD data is inherently "noisy" due to ship heave, pump vibrations, and electronic interference. The `wf_ctd_build` applies a multi-stage digital signal processing (DSP) suite.

### 4.1 Ship Heave & Loop Filtering
As the research vessel rolls in the swell, the CTD rosette may momentarily decelerate or even move upward during a downcast. This causes the sensors to measure "dirty" water that has been agitated by the rosette's own frame and wake.
* **The Logic:** We calculate the instantaneous descent rate ($v = dp/dt$). If $v < 0.01$ dbar/scan, the data is flagged and removed. This ensures only "fresh" water entering the pump from below the package is recorded.

### 4.2 Savitzky-Golay Smoothing
Unlike a standard "Moving Average" which rounds off sharp features and blurs real biological layers, we use a **Savitzky-Golay filter**. This algorithm performs a local least-squares polynomial fit (Order 3) over a sliding window (15 scans). This preserves the sharp, high-gradient "step" features in the thermocline while stripping away high-frequency digitizer noise.



---

## 5. Automated Quality Control (QC) & Binning
The final stage of the pipeline performs a "Sanity Audit" on every data point based on UNESCO and IOC standards:

* **Density Inversions:** The ocean is generally stable. If the pipeline detects a significant decrease in density with depth ($\Delta \sigma_0 < -0.03$), it suggests the data is contaminated by ship heave and flags it as **Suspect (3)**.
* **Physical Envelopes:** Data is checked against regional extremes for the Baja/Cortez region:
    * **Temperature:** $-2^\circ\text{C}$ to $35^\circ\text{C}$
    * **Salinity:** $2.0$ to $42.0$ PSU
* **Vertical Binning:** To make the data digestible for the Dashboard App and DuckDB backend, the 24Hz data is averaged into **0.1 dbar bins**. This maintains ultra-high vertical resolution (approx. 10cm) while reducing the database footprint by over 90%.