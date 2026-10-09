# M1_baseline

| Field | Content |
| --- | --- |
| Purpose | Provide reference baselines for relative TDD. |
| Hypothesis | n/a |
| Inputs | Person-day table (registered public dataset). |
| Source / evidence class | COMPUTED |
| Procedure | Naive and harmonic baselines under subject-grouped CV. |
| Variables | model |
| Controls | subject-disjoint folds |
| Metrics | RMSE, MAE, R2 |
| Expected outputs | baseline_scores |
| Interpretation | Cycle baselines need real cycle labels. |
| Failure conditions | row-level splitting; no labels yet cycle claim |

Run: `python -m iris.tools.run_experiment M1_baseline [--mode production|provisional|test] [--smoke]`.
A `ScientificBlocker` is recorded as a blocked run (with the missing dependency); it is never replaced by a default value.
