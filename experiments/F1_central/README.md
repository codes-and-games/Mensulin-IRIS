# F1_central

| Field | Content |
| --- | --- |
| Purpose | Central two-level Monte Carlo and primary endpoints. |
| Hypothesis | H3-H5 (document 16): tails and concentration beyond algebra. |
| Inputs | Stored virtual_population + potency_draws. |
| Source / evidence class | PROJECTED |
| Procedure | Two-level MC (J outer, N inner); controls C1/C2; P1 variance decomposition; P2 HP; product-tail envelope; phi. |
| Variables | scenario, phase, dosing case, threshold |
| Controls | C1 no loss => zero shortfall; C2 no cycle => no phase difference |
| Metrics | exceedance, M+, TCI, CI, HP, MC SE |
| Expected outputs | fusion_out, fusion_summary, controls, primary_endpoints, product_tail_envelope |
| Interpretation | Outputs are PROJECTED, never empirical. |
| Failure conditions | failed control; MC SE not reported |

Run: `python -m iris.tools.run_experiment F1_central [--mode production|provisional|test] [--smoke]`.
A `ScientificBlocker` is recorded as a blocked run (with the missing dependency); it is never replaced by a default value.
