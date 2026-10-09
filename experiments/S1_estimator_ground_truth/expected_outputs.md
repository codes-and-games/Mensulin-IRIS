# Expected outputs: S1_estimator_ground_truth

Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`:

- recovery_trials
- recovery_summary

Every table carries an evidence class (SIMULATED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
