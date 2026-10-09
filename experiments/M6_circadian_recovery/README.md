# M6_circadian_recovery

| Field | Content |
| --- | --- |
| Purpose | Test on real physiology and real noise that the EKF/RTS estimator recovers a reproducible 24 h sensitivity profile (project document V2, "M2. Circadian recovery on real data"). |
| Hypothesis | H1 (document): the estimator recovers a reproducible circadian pattern from public CGM/insulin/carb data; no claim about the menstrual cycle. |
| Inputs | Ingested 5-min event grids (`data/processed/<dataset>/events_grid.parquet`) for HUPA-UCM (S15) and BrisT1D-Open (S17). |
| Source / evidence class | COMPUTED |
| Procedure | Longest run of analysable days per person -> EKF + RTS -> hourly relative ln S -> population profile; person-bootstrap CI; placebo (per-person circular shifts); split-half (even/odd days); nuisance-scale sensitivity. |
| Variables | dataset, person, hour of day, nuisance scale |
| Controls | placebo shifts; split-half; nuisance scale x0.7/1/1.4; simulated recovery in `tests/stat/test_circadian_recovery.py` (null + injected amplitude) |
| Metrics | 24 h amplitude (ln units), peak hour, bootstrap intervals, placebo p, split-half r and peak difference, `reproducible` flag |
| Expected outputs | circadian_person, circadian_population, circadian_profile, circadian_nuisance_sensitivity |
| Interpretation | `reproducible = true` means the pipeline recovers a stable pattern; amplitude is attenuated under the correct model (see test), so it is a LOWER bound on the true amplitude. Direction vs literature is a separate [VERIFY] item. |
| Failure conditions | no reproducible profile -> report it and restrict method validation to simulation (document); fewer than 3 analysable persons -> BLOCKED for that dataset |

Run: `python -m iris.tools.run_experiment M6_circadian_recovery [--mode production|provisional|test] [--smoke]`.
