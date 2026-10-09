# R2_definition_robustness

| Field | Content |
| --- | --- |
| Purpose | Robustness to definitions. |
| Hypothesis | n/a |
| Inputs | Stored inputs. |
| Source / evidence class | PROJECTED |
| Procedure | Vary thresholds, eta, dosing case, ISF constant. |
| Variables | definition |
| Controls | three-phase and boundary shifts BLOCKED until windows extracted |
| Metrics | hold/stable flags |
| Expected outputs | stability_matrix, stability_summary |
| Interpretation | Fragile conclusions are shown. |
| Failure conditions | hidden fragility |

Run: `python -m iris.tools.run_experiment R2_definition_robustness [--mode production|provisional|test] [--smoke]`.
A `ScientificBlocker` is recorded as a blocked run (with the missing dependency); it is never replaced by a default value.
