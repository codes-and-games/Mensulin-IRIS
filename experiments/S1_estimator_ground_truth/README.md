# S1_estimator_ground_truth

| Field | Content |
| --- | --- |
| Purpose | Check that the EKF/smoother recovers a known injected sensitivity cycle. |
| Hypothesis | Recovery error is small at A>=0.05; false-detection rate at A=0 stays near alpha. |
| Inputs | None (virtual people; constants are declared ASSUMPTION levels). |
| Source / evidence class | SIMULATED |
| Procedure | Simulate -> EKF -> RTS -> harmonic fit across amplitude, cycle length, noise, carb error, missingness. |
| Variables | A, Lc, sensor SD, carb error, gap fraction |
| Controls | A=0 no-signal control; misspecified time-constant control |
| Metrics | amplitude bias/RMSE, detection rate, 95% coverage |
| Expected outputs | recovery_trials, recovery_summary |
| Interpretation | The estimator must not invent a cycle when none exists. |
| Failure conditions | false-detection rate above tolerance |

Run: `python -m iris.tools.run_experiment S1_estimator_ground_truth [--mode production|provisional|test] [--smoke]`.
A `ScientificBlocker` is recorded as a blocked run (with the missing dependency); it is never replaced by a default value.
