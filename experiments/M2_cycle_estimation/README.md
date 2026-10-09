# M2_cycle_estimation

| Field | Content |
| --- | --- |
| Purpose | Estimate cycle effects with a mixed harmonic model and placebo control. |
| Hypothesis | Cycle amplitude exceeds the placebo distribution. |
| Inputs | Person-day table with cycle labels. |
| Source / evidence class | COMPUTED |
| Procedure | Mixed model; placebo cycle offsets. |
| Variables | K harmonics |
| Controls | placebo-cycle permutation |
| Metrics | amplitude, placebo p95, p-value |
| Expected outputs | cycle_amplitude |
| Interpretation | No cycle claim from unlabelled data. |
| Failure conditions | claim without labels |

Run: `python -m iris.tools.run_experiment M2_cycle_estimation [--mode production|provisional|test] [--smoke]`.
A `ScientificBlocker` is recorded as a blocked run (with the missing dependency); it is never replaced by a default value.
