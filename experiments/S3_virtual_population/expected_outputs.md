# Expected outputs: S3_virtual_population

Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`:

- population_checks
- virtual_population_h*

Every table carries an evidence class (SIMULATED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
