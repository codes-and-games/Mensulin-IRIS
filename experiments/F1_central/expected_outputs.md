# Expected outputs: F1_central

Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`:

- fusion_out
- fusion_summary
- controls
- primary_endpoints
- product_tail_envelope

Every table carries an evidence class (PROJECTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
