# Expected outputs: L3_biological_evidence

Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`:

- parameter_sheet

Every table carries an evidence class (COMPUTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
