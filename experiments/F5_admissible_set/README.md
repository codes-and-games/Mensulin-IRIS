# F5_admissible_set

| Field | Content |
| --- | --- |
| Purpose | Classify pre-registered conclusions over Theta_E and Theta_S. |
| Hypothesis | See docs/prereg/conclusions.yaml. |
| Inputs | Stored population + potency draws; frozen conclusions. |
| Source / evidence class | PROJECTED |
| Procedure | Factorial + LHS + adversarial search per set. |
| Variables | theta components |
| Controls | Theta_E and Theta_S never pooled |
| Metrics | classification, controlling component, counterexample |
| Expected outputs | conclusion_classes, theta_evaluations, adversarial_search, design_coverage |
| Interpretation | Robust means robust under the declared design and budget, not proof. |
| Failure conditions | unfrozen conclusions outside test mode (=> BLOCKED) |

Run: `python -m iris.tools.run_experiment F5_admissible_set [--mode production|provisional|test] [--smoke]`.
A `ScientificBlocker` is recorded as a blocked run (with the missing dependency); it is never replaced by a default value.
