# Expected outputs: R1_sensitivity

Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`:

- sobol_by_seed
- sobol_summary
- thermal_variance_share
- tornado

Every table carries an evidence class (COMPUTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
