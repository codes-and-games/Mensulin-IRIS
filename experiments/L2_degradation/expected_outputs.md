# Expected outputs: L2_degradation

Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`:

- fit_diagnostics
- loso_predictions
- loso_summary
- ensemble_weights

Every table carries an evidence class (COMPUTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
