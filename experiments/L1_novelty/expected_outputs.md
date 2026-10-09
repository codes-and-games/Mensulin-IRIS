# Expected outputs: L1_novelty

Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`:

- search_log
- near_neighbours

Every table carries an evidence class (COMPUTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
