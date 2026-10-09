# E1_climate_agreement

| Field | Content |
| --- | --- |
| Purpose | Establish cross-source climate agreement and the climate-input uncertainty sigma_data. |
| Hypothesis | Registered reanalysis/gridded sources agree within a pre-registered tolerance at the same coordinates/period. |
| Inputs | Registered, verified climate series S27-S31 (PUBLIC_DATASET); sigma_val from S36 (PUBLISHED). |
| Source / evidence class | COMPUTED |
| Procedure | Align sources on UTC index; mean difference, RMSE, correlation; cross-source SD; sigma_data = sqrt(sigma_cross^2 + sigma_val^2). |
| Variables | source pair, location, period |
| Controls | source-vs-itself = exactly 0; timezone/unit mismatch rejected |
| Metrics | mean_diff, rmse, corr, sigma_cross, sigma_data |
| Expected outputs | cross_source_agreement, sigma_data tables; agreement figures |
| Interpretation | A source failing the pre-registered threshold is REPORTED and its sensitivity case run; never silently dropped. |
| Failure conditions | self-comparison non-zero; misaligned conventions accepted; sources unregistered (=> BLOCKED) |

Run: `python -m iris.tools.run_experiment E1_climate_agreement [--mode production|provisional|test] [--smoke]`.
A `ScientificBlocker` is recorded as a blocked run (with the missing dependency); it is never replaced by a default value.
