# westernflyer-seaofcortez-2025
Analytical pipeline and reactive dashboard for forensic oceanographic analysis of the Sea of Cortez (Baja 2025). Powered by DuckDB, HoloViews, and TEOS-10.

Welcome to the data processing and visualization archive for the **Western Flyer Foundation - Sea of Cortez Expedition (2025)**.

## ⚓ Project Mission
This repository provides a high-performance analytical pipeline designed to transform raw instrument data from Sea-Bird Scientific SBE19plus units into research-grade datasets. By utilizing a **DuckDB** backend and **HoloViews** frontend, we provide oceanographers with a reactive, forensic-grade environment to explore the complex water column of the Gulf of California.

## 🧬 Core Features
* **High-Performance Backend:** Uses DuckDB for lightning-fast querying of vertical binned data.
* **Silk-Smoothing Engine:** Implements Savitzky-Golay filtering to remove sensor noise while preserving sharp physical gradients.
* **TEOS-10 Standards:** On-the-fly thermodynamic calculations via the Gibbs SeaWater (GSW) library.
* **Interactive Analytics:** A multi-tab dashboard featuring Vertical Profiles, T-S Diagrams, Metabolic Index ($\Phi$), and Geolocation with bathymetry.

## 📂 Repository Structure
* `wf_environment.ipynb`: Automated environment auditor and library installer.
* `wf_ctd_build.ipynb`: The ETL engine that processes raw `.cnv` files into the DuckDB archive.
* `sea_of_cortez_app.py`: The HoloViews/Panel dashboard application.
* `/cnv`: Sub-directory for raw instrument data.
* `/processed`: Home of the `sea_of_cortez.duckdb` database.

## 🚀 Getting Started
Please refer to the [Installation and Operations Guide](./INSTALL_GUIDE.md) for full instructions on setting up your Anaconda environment and serving the dashboard.
________________________________________

