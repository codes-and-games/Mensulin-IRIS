# Expected outputs: S2_thermal_kinetics

Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`:

- k1_recovery
- forward_checks

Every table carries an evidence class (SIMULATED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
