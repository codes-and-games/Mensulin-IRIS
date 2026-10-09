# M3_generalisation

| Field | Content |
| --- | --- |
| Purpose | Test generalisation to unseen subjects. |
| Hypothesis | Harmonic model beats naive on held-out subjects. |
| Inputs | Person-day table with cycle labels. |
| Source / evidence class | COMPUTED |
| Procedure | Leave-one-subject-out CV. |
| Variables | model |
| Controls | LOGO |
| Metrics | RMSE, R2 |
| Expected outputs | loso_scores |
| Interpretation | Benchmarks are secondary to calibration/interpretability. |
| Failure conditions | subject leakage |

Run: `python -m iris.tools.run_experiment M3_generalisation [--mode production|provisional|test] [--smoke]`.
A `ScientificBlocker` is recorded as a blocked run (with the missing dependency); it is never replaced by a default value.
