# F4_ablation

| Field | Content |
| --- | --- |
| Purpose | Ablations A0-A9 with common random numbers. |
| Hypothesis | A4 pushes phi toward 1. |
| Inputs | Stored population + potency draws. |
| Source / evidence class | PROJECTED |
| Procedure | Ablate one element at a time. |
| Variables | configuration |
| Controls | A4 circularity control |
| Metrics | phi, exceedance, TCI |
| Expected outputs | ablation_rows, ablation_table |
| Interpretation | A4 must NOT be used for any reported primary result. |
| Failure conditions | A4 does not push phi toward 1 |

Run: `python -m iris.tools.run_experiment F4_ablation [--mode production|provisional|test] [--smoke]`.
A `ScientificBlocker` is recorded as a blocked run (with the missing dependency); it is never replaced by a default value.
