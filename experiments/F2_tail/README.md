# F2_tail

| Field | Content |
| --- | --- |
| Purpose | Tail analysis at N=100,000. |
| Hypothesis | n/a |
| Inputs | Stored potency draws; N=100k population. |
| Source / evidence class | PROJECTED |
| Procedure | Direct tail probabilities; Makarov bounds; convergence. |
| Variables | scenario, threshold |
| Controls | bounds must bracket the estimate |
| Metrics | tail prob, MC SE, bounds |
| Expected outputs | tail_exceedance, product_tail_envelope_*, mc_convergence |
| Interpretation | Tails are never inferred from means. |
| Failure conditions | bounds violated |

Run: `python -m iris.tools.run_experiment F2_tail [--mode production|provisional|test] [--smoke]`.
A `ScientificBlocker` is recorded as a blocked run (with the missing dependency); it is never replaced by a default value.
