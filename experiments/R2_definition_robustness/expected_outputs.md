# Expected outputs: R2_definition_robustness

Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`:

- stability_matrix
- stability_summary

Every table carries an evidence class (PROJECTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
