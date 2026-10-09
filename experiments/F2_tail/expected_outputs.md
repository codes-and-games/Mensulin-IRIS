# Expected outputs: F2_tail

Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`:

- tail_exceedance
- product_tail_envelope_*
- mc_convergence

Every table carries an evidence class (PROJECTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
