# M4_leakage

| Field | Content |
| --- | --- |
| Purpose | Verify leakage safeguards. |
| Hypothesis | Grouped CV prevents identity leakage; row-level CV does not. |
| Inputs | Person-day table. |
| Source / evidence class | COMPUTED |
| Procedure | Split disjointness, row-level leak demonstration, feature rejection, identity canary. |
| Variables | scheme |
| Controls | canary must detect the row-level leak |
| Metrics | pass/fail per test |
| Expected outputs | leakage_tests |
| Interpretation | A canary that cannot detect leakage is itself a failure. |
| Failure conditions | any test fails |

Run: `python -m iris.tools.run_experiment M4_leakage [--mode production|provisional|test] [--smoke]`.
A `ScientificBlocker` is recorded as a blocked run (with the missing dependency); it is never replaced by a default value.
