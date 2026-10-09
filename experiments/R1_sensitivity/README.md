# R1_sensitivity

| Field | Content |
| --- | --- |
| Purpose | Global sensitivity and thermal variance share. |
| Hypothesis | n/a |
| Inputs | Stored population + potency draws. |
| Source / evidence class | COMPUTED |
| Procedure | Sobol (several seeds) + tornado. |
| Variables | h, eta, r_PB, st, model choice |
| Controls | index stability across seeds |
| Metrics | S1, ST, thermal share |
| Expected outputs | sobol_by_seed, sobol_summary, thermal_variance_share, tornado |
| Interpretation | Unstable indices are flagged; climate share not applicable while S5 blocked. |
| Failure conditions | unstable indices not flagged |

Run: `python -m iris.tools.run_experiment R1_sensitivity [--mode production|provisional|test] [--smoke]`.
A `ScientificBlocker` is recorded as a blocked run (with the missing dependency); it is never replaced by a default value.
