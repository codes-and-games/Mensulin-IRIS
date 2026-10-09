# Expected outputs: E4_exposure_generation

Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`:

- thermal_exposure
- exposure_summaries
- potency_draws (+ provenance)

Every table carries an evidence class (SIMULATED/COMPUTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
