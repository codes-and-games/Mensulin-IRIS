# S3_virtual_population

| Field | Content |
| --- | --- |
| Purpose | Check the virtual population against declared published moments. |
| Hypothesis | Moments reproduce anchors within tolerance. |
| Inputs | Anchors from S1 (PUBLISHED; PENDING_VERIFY). |
| Source / evidence class | SIMULATED |
| Procedure | Generate populations at three heterogeneity levels; compare moments. |
| Variables | heterogeneity multiplier |
| Controls | centring checks (mean S = mean rho = 1) |
| Metrics | moment differences, concordance (reference level only) |
| Expected outputs | population_checks, virtual_population_h* |
| Interpretation | Targets that are unresolved report BLOCKED, never PASS. |
| Failure conditions | moment failure; rho constructed as 1/S |

Run: `python -m iris.tools.run_experiment S3_virtual_population [--mode production|provisional|test] [--smoke]`.
A `ScientificBlocker` is recorded as a blocked run (with the missing dependency); it is never replaced by a default value.
