# F6_dependence_transport

| Field | Content |
| --- | --- |
| Purpose | Dependence and transportability sweeps. |
| Hypothesis | n/a |
| Inputs | Stored population + potency draws. |
| Source / evidence class | PROJECTED |
| Procedure | Sweep r_PB, st, R_B at the reference theta. |
| Variables | r_PB, st, R_B |
| Controls | reference theta fixed |
| Metrics | margin, flip point |
| Expected outputs | sweeps, flip_points |
| Interpretation | A flip at the smallest non-zero dependence = conditional on exact independence. |
| Failure conditions | none |

Run: `python -m iris.tools.run_experiment F6_dependence_transport [--mode production|provisional|test] [--smoke]`.
A `ScientificBlocker` is recorded as a blocked run (with the missing dependency); it is never replaced by a default value.
