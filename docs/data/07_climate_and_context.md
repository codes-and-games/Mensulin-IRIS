# 07 Climate and context data (E1, E2; scenario S5 of E4)

## Read this first: what climate data can and cannot do today
- Scenarios S0-S4, S6, S7 are **parametric (SIMULATED)** and need no climate data. Only **S5 (reanalysis-driven real weather)** and experiments **E1/E2** need climate records.
- **Code limitation:** `E1_climate_agreement` and `E2_reconstruction_context` currently have **no production code path**. In any non-test mode they stop with a blocker; only the synthetic TEST path exists. Obtaining the data does not by itself make them runnable. A reader for the registered series plus the location/threshold rules must be written first, against one real downloaded file (planned: decision D-12).
- **Research decisions still open (pre-registration):** the location-selection rule (Koppen-Geiger classes and coordinate rule), the 28-day window rule, and the agreement thresholds. `configs/thermal/locations.yaml` says "freeze in docs/prereg **before downloading records**". Do not download records for E1 before that freeze.
- **Consequence:** the Phase 1 core result (potency, population, fusion, robustness) does **not** depend on this branch. It is scheduled last ("Phase 1b"). If skipped, S5 is reported as `blocked` and the write-up says so.

## Sources (registry S27-S31; every access route below must be confirmed on the provider's page and recorded, none has been verified by the preparer)
| Id | Resource | Likely route (to confirm) | Account | What to record |
|---|---|---|---|---|
| S27 | ERA5-Land hourly | Copernicus Climate Data Store, `cdsapi` | free CDS account + licence acceptance | dataset DOI/version, licence, request JSON, retrieval date |
| S28 | ERA5 hourly | Copernicus CDS | same | same |
| S29 | NASA POWER | public API | none | API version, query, date |
| S30 | IMD gridded temperature | India Meteorological Department data portal | possibly registration | format, version, terms |
| S31 | ASHRAE Global Thermal Comfort Database II | public release | none expected | version, licence |
Install extras for CDS: `python -m pip install -e ".[climate]"`.

## Steps (after the pre-registration freeze of the location rule)
1. Write the exact retrieval request into `docs/data/evidence/climate/requests/<source>.json` **before** running it.
2. Download only the pre-registered locations/period into `data/raw/climate/<source>/`.
3. Common procedure steps 3-4 in `00_acquisition_master.md` per source (register, verify row, digest).
4. Then ask for the E1/E2 production reader (D-12).
**Next:** `docs/prereg/freeze_procedure.md`.
