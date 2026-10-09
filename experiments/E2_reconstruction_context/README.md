# E2_reconstruction_context

| Field | Content |
| --- | --- |
| Purpose | Evaluate sub-daily reconstruction and outdoor-to-context mapping on held-out buildings. |
| Hypothesis | Sinusoid/Parton-Logan reconstruction beats the naive daily-mean baseline on hourly truth; mapping generalises to unseen buildings. |
| Inputs | Hourly truth (S27), comfort database (S31), published mappings (S32), Parton-Logan (S34). |
| Source / evidence class | COMPUTED |
| Procedure | Reconstruct from Tmax/Tmin; compare with hourly truth; fit mapping on training buildings, evaluate on held-out buildings. |
| Variables | method, hour-of-max, building |
| Controls | naive baseline; building-level hold-out (no building in both sets) |
| Metrics | bias, RMSE, residual autocorrelation |
| Expected outputs | reconstruction_errors, context_mapping.json, context_validation |
| Interpretation | Residual autocorrelation is carried into the mapping noise model. |
| Failure conditions | building leakage; Parton-Logan used before form verification; unregistered inputs |

Run: `python -m iris.tools.run_experiment E2_reconstruction_context [--mode production|provisional|test] [--smoke]`.
A `ScientificBlocker` is recorded as a blocked run (with the missing dependency); it is never replaced by a default value.
