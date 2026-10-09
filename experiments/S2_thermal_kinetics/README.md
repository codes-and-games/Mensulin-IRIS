# S2_thermal_kinetics

| Field | Content |
| --- | --- |
| Purpose | Verify kinetics code on simulated data. |
| Hypothesis | Known K1 parameters are recoverable in prediction space; forward closed forms reproduced. |
| Inputs | None (simulation truth). |
| Source / evidence class | SIMULATED |
| Procedure | Fit noisy synthetic observations; compare predictions with truth. |
| Variables | replicate |
| Controls | Arrhenius ratio = 1 at reference |
| Metrics | abs error, 95% coverage |
| Expected outputs | k1_recovery, forward_checks |
| Interpretation | Parameters are strongly correlated; compare predictions, not raw parameters. |
| Failure conditions | coverage far from nominal; ratio != 1 |

Run: `python -m iris.tools.run_experiment S2_thermal_kinetics [--mode production|provisional|test] [--smoke]`.
A `ScientificBlocker` is recorded as a blocked run (with the missing dependency); it is never replaced by a default value.
