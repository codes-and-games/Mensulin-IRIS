# M5_empirical_isf_tdd

| Field | Content |
| --- | --- |
| Purpose | Examine empirical ISF x TDD. |
| Hypothesis | Settings follow ISF∝1/TDD as a rule. |
| Inputs | Public dataset with ISF settings. |
| Source / evidence class | COMPUTED |
| Procedure | ln-ln regression. |
| Variables | person |
| Controls | settings are not physiology |
| Metrics | slope, CI |
| Expected outputs | isf_tdd_fit |
| Interpretation | Do not treat settings as measured sensitivity. |
| Failure conditions | no ISF data (=> BLOCKED) |

Run: `python -m iris.tools.run_experiment M5_empirical_isf_tdd [--mode production|provisional|test] [--smoke]`.
A `ScientificBlocker` is recorded as a blocked run (with the missing dependency); it is never replaced by a default value.
