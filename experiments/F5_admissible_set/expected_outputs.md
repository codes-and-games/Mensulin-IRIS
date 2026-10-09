# Expected outputs: F5_admissible_set

Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`:

- conclusion_classes
- theta_evaluations
- adversarial_search
- design_coverage

Every table carries an evidence class (PROJECTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
