# Expected outputs: M7_next_day_tdd_ml

Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars):

- cohort_flow, feature_audit, scores, verdict, scores_by_dataset, scores_by_person, predictions, placebo_control

Every table carries evidence class COMPUTED and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
Read `verdict` (primary = LeaveOneGroupOut) and `placebo_control` first; check `log.txt` for FAILED_CONTROL.
