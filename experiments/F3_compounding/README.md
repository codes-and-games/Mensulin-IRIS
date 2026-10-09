# F3_compounding

| Field | Content |
| --- | --- |
| Purpose | Secondary compounding analysis. |
| Hypothesis | Joint exceedance exceeds the product of marginals only with dependence. |
| Inputs | Stored population + potency draws. |
| Source / evidence class | PROJECTED |
| Procedure | Joint vs product by swing band and r_PB. |
| Variables | r_PB, swing band |
| Controls | independence => ratio ~ 1 |
| Metrics | joint, product, ratio |
| Expected outputs | compounding |
| Interpretation | The null is reported. |
| Failure conditions | none |

Run: `python -m iris.tools.run_experiment F3_compounding [--mode production|provisional|test] [--smoke]`.
A `ScientificBlocker` is recorded as a blocked run (with the missing dependency); it is never replaced by a default value.
