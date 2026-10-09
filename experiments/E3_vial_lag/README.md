# E3_vial_lag

| Field | Content |
| --- | --- |
| Purpose | Verify the numerical implementation of the vial thermal-lag model. |
| Hypothesis | Exponential integrator = analytic step response; finite-volume agrees with lumped model when Bi < 0.1. |
| Inputs | Verification-only physical constants in config (not scientific inputs). |
| Source / evidence class | SIMULATED |
| Procedure | Step, heat-spike, time-step refinement, tau->0, constant ambient, finite-volume comparison, Biot-number flag. |
| Variables | tau, dt, h |
| Controls | analytic solution; invalid-Biot regime must be flagged |
| Metrics | max abs error (C) |
| Expected outputs | lag_verification.json, lag_verification_table |
| Interpretation | Validates the thermal numerics ONLY; says nothing about insulin behaviour. |
| Failure conditions | any check outside tolerance; Biot flag not raised in the invalid regime |

Run: `python -m iris.tools.run_experiment E3_vial_lag [--mode production|provisional|test] [--smoke]`.
A `ScientificBlocker` is recorded as a blocked run (with the missing dependency); it is never replaced by a default value.
