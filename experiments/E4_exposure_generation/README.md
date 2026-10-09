# E4_exposure_generation

| Field | Content |
| --- | --- |
| Purpose | Generate scenario temperature histories, exposure summaries and potency draws (Layer 2 output). |
| Hypothesis | n/a (generation experiment). |
| Inputs | Scenario definitions (configs/fusion/scenarios.yaml); kinetics from L2; tau range from lag.yaml. |
| Source / evidence class | SIMULATED/COMPUTED |
| Procedure | Generate air temperature, apply vial lag (interval-mean), K-model hazard, transfer discrepancy; M draws per scenario/duration/transfer level. |
| Variables | scenario S0-S8, duration, transfer SD |
| Controls | S5/S8 blocked unless inputs are registered; assumptions listed per scenario |
| Metrics | hours above 25/30/35/40 C, degree-hours, max, MKT (descriptor), imputed fraction, potency draws |
| Expected outputs | thermal_exposure, exposure_summaries, potency_draws (+ provenance) |
| Interpretation | MKT is an exposure descriptor, not potency. |
| Failure conditions | potency increasing with time; K0 not exactly 1; missing kinetics (=> potency BLOCKED, exposure still produced) |

Run: `python -m iris.tools.run_experiment E4_exposure_generation [--mode production|provisional|test] [--smoke]`.
A `ScientificBlocker` is recorded as a blocked run (with the missing dependency); it is never replaced by a default value.
