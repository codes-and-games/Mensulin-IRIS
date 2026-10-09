# L4_isf_tdd

| Field | Content |
| --- | --- |
| Purpose | Examine the between-person ISF-TDD relationship in public data. |
| Hypothesis | ln ISF vs ln TDD slope near -1 as a SETTINGS relationship. |
| Inputs | Public dataset with pump ISF settings (clinician-set). |
| Source / evidence class | COMPUTED |
| Procedure | HC3 OLS of person-level ln ISF on ln TDD. |
| Variables | person |
| Controls | settings are not physiology |
| Metrics | slope, CI, residual SD |
| Expected outputs | isf_tdd_between_person |
| Interpretation | ISF settings are not measured sensitivity. |
| Failure conditions | no ISF column => BLOCKED; glucose-equivalent analysis stays model-conditional |

Run: `python -m iris.tools.run_experiment L4_isf_tdd [--mode production|provisional|test] [--smoke]`.
A `ScientificBlocker` is recorded as a blocked run (with the missing dependency); it is never replaced by a default value.
