# R3_structural_robustness

| Field | Content |
| --- | --- |
| Purpose | Robustness to kinetic structure. |
| Hypothesis | n/a |
| Inputs | Stored potency draws. |
| Source / evidence class | PROJECTED |
| Procedure | Each study alone, envelopes, K0, K1. |
| Variables | structure |
| Controls | flip reporting |
| Metrics | hold flags, flips |
| Expected outputs | structural_results, structural_flips |
| Interpretation | If conclusions flip the flip is reported; no preferred result is chosen. |
| Failure conditions | flip not reported |

Run: `python -m iris.tools.run_experiment R3_structural_robustness [--mode production|provisional|test] [--smoke]`.
A `ScientificBlocker` is recorded as a blocked run (with the missing dependency); it is never replaced by a default value.
