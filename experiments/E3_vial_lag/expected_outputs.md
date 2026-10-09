# Expected outputs: E3_vial_lag

Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`:

- lag_verification.json
- lag_verification_table

Every table carries an evidence class (SIMULATED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
