# L5_thermal_context

| Field | Content |
| --- | --- |
| Purpose | Validate extracted thermal-context parameters. |
| Hypothesis | n/a |
| Inputs | literature/thermal_context_parameters.csv. |
| Source / evidence class | COMPUTED |
| Procedure | Check source/citation/page/conditions/units completeness. |
| Variables | context |
| Controls | incomplete rows must not be used |
| Metrics | completeness |
| Expected outputs | context_parameters |
| Interpretation | Every parameter needs full provenance. |
| Failure conditions | missing source or units |

Run: `python -m iris.tools.run_experiment L5_thermal_context [--mode production|provisional|test] [--smoke]`.
A `ScientificBlocker` is recorded as a blocked run (with the missing dependency); it is never replaced by a default value.
