# M7_next_day_tdd_ml

| Field | Content |
| --- | --- |
| Purpose | First supervised ML benchmark: can past-only information predict a person's NEXT-DAY observed TDD better than trivial baselines on participants never seen in training? |
| Hypothesis | n/a (benchmark; no cycle or thermal claim) |
| Inputs | Combined person-day table (HUPA-UCM + BrisT1D-Open), cycle fields NOT used. |
| Source / evidence class | COMPUTED |
| Target | TDD(t) / mean TDD of the previous 7 calendar days (needs >= 3 valid days); scored back in units/day. |
| Features | Past-only: yesterday's and the day before's TDD relative to the trailing mean, trailing TDD variability, yesterday's carbohydrate (relative to trailing mean), entries, mean glucose, TIR/TBR/TAR; plus `is_weekend` of the target date. |
| Models | M0 naive mean, P1 persistence (yesterday), P7 trailing 7-day mean, R1 ridge, R2 random forest, R3 gradient boosting (fixed hyperparameters, no tuning). |
| Controls | Participant-disjoint CV (LeaveOneGroupOut primary, GroupKFold secondary); leakage guard; person-clustered bootstrap; within-person shuffled-target placebo. |
| Fixed verdict rule | An ML model "beats" the better of P1/P7 only if the 95% clustered-bootstrap CI of MAE skill is entirely > 0 AND skill >= `min_skill` (2%, declared before any real run). |
| Data rule | A day with TDD <= 0 is treated as *insulin not recorded* (HUPA-UCM people 0011P/0015P/0018P have all-zero insulin columns in the raw files), never as a physiological zero; those days are excluded and counted in `cohort_flow`. Raw data are untouched. |
| Expected outputs | cohort_flow, feature_audit, scores, verdict, scores_by_dataset, scores_by_person, predictions, placebo_control |
| Interpretation | A model that does not beat a trailing mean is a legitimate finding. Under automated insulin delivery TDD reflects controller behaviour as well as physiology; beating persistence is not evidence of any biological mechanism. |
| Failure conditions | placebo shows skill (FAILED_CONTROL in the log); fewer than 6 usable participants (BLOCKED); row-level splitting. |

Run: `python -m iris.tools.run_experiment M7_next_day_tdd_ml --mode provisional` (add `--smoke` for a plumbing check on synthetic data with `--mode test`).
