# 05 Production execution runbook

**Always run from the repository root with the virtual environment active.** Mode `production` accepts only RESOLVED parameters, verified registry sources, hash-registered files and verified literature rows; anything else produces `BLOCKED` naming the missing input. Run IDs are derived from the date, git hash and config. A **completed** run is immutable: re-running the same experiment on the same day with unchanged config raises `RunExistsError` (protection, not a failure; use the existing run). A BLOCKED or failed run is discarded automatically and can be re-run as soon as the missing input is supplied.

## Pipeline works vs scientific evidence exists

`python -m iris.tools.run_all --mode production` writes `results/status_production.md` with two columns: `pipeline_status` (did the code finish) and `evidence_status` (is the result evidence). Verification experiments (E3, S1, S2, M4) can finish and still carry **no evidence about the world**. A completed run is judged against the experiment's validation criteria and the checklist in `docs/validation/`, never by completion alone.

## Runtime classes (measured)

All experiments finish in **under about one minute** at their configured sizes on a single CPU core (measured on synthetic TEST-mode inputs in a scratch copy: F1 47 s, M6 36 s, R1 31 s, F4 17 s, M2 12 s, E4 11 s, all others under 10 s). Real-data M6 scales with the number of people and days ingested (expect minutes, not hours). No GPU and no cloud compute are needed.

## Dependency order and commands

Run in this order (also what `run_all` does). In the table `...` abbreviates `python -m iris.tools.run_experiment`; the complete, copy-paste commands are in the block below the table.

| # | Command | Needs | Output (under `results/runs/<run_id>/`) | Validate with | Interpretation | Common errors |
|---|---|---|---|---|---|---|
| 1 | `python -m iris.tools.run_experiment L3_biological_evidence --mode production` | S1 verified; rows RESOLVED | `tables/biological_evidence_status` | all rows RESOLVED | which anchors are verified | `UnregisteredSourceError`: S1 not verified |
| 2 | `... L5_thermal_context ...` | verified S31, S32, S35 rows | context table | rows verified | context parameters | empty CSV |
| 3 | `... L2_degradation ...` | verified rows S7–S14 | kinetic fits, LOSO | LOSO error, CIs | which kinetic forms the data support | empty CSV / unverified rows |
| 4 | `... L1_novelty ...` | `literature/novelty_search_log.csv` | log validation | log complete | novelty statement support | no searches logged |
| 5 | `... E3_vial_lag ...` | none | `lag_verification.json` | all cases within tolerance | solver correct (verification only) | none |
| 6 | `... E1_climate_agreement ...` | S27–S30 registered+verified, thresholds frozen | agreement tables | thresholds applied as frozen | climate input uncertainty | `climate_sources unresolved` |
| 7 | `... E2_reconstruction_context ...` | E1, S31 | reconstruction/context tables | hold-out vs fit error | context-mapping accuracy | `hourly_truth_and_comfort_db unresolved` |
| 8 | `... S2_thermal_kinetics --mode test` | none | recovery table | recovery within tolerance | code verification only; **TEST mode by design** | `TestOnlyDataError` in production is correct |
| 9 | `... E4_exposure_generation ...` | L2 (and E1/E2 for scenario S5), S35 | `thermal_exposure`, `potency_draws`, `scenario_status` | schemas; `scenario_status` | exposure and potency scenarios; blocked scenarios listed, never filled | `degradation_literature unresolved` |
| 10 | `... S3_virtual_population ...` | S1 verified; the nine rows in `S1_hossmann_evidence.md` RESOLVED and `sync_population_status` run | `data/derived/virtual_population_h*.parquet` | marginals vs anchors | population | `parameter 'tdd'/'cycle'/'luteal' unresolved` |
| 11 | `... F1_central`, `F2_tail`, `F3_compounding`, `F4_ablation`, `F6_dependence_transport` (each `--mode production`) | S3, E4 draws | fusion tables | F4 control passes | central/tail/compounding results | `virtual_population not found` |
| 12 | `... F5_admissible_set ...` | **frozen** `conclusions.yaml`, F1/F2/F4 | margins vs frozen thresholds | thresholds untouched | confirmatory conclusions | `not frozen` |
| 13 | `... R1_sensitivity`, `R2_definition_robustness`, `R3_structural_robustness` | F-series | sensitivity/robustness tables | indices sane | robustness | `potency_draws not found` |
| 14 | `... S1_estimator_ground_truth --mode test` | none | recovery | recovery error small | estimator code verification; **TEST by design** | production refusal is correct |
| 15 | `... M4_leakage ...` | any ingested+registered person-day | leakage tests | all `passed` | evaluation design leak-free | `person_day unresolved` |
| 16 | `... M1_baseline ...` | person-day | baseline scores | grouped CV only | naive baseline (no cycle claim without labels) | same |
| 17 | `... M6_circadian_recovery ...` | HUPA + BrisT1D ingested | profile, amplitude, placebo, split-half | split-half agreement, placebo exceeded | method plausibility only | `events_grid unresolved` |
| 18 | `... M2_cycle_estimation`, `M3_generalisation` | **cycle-labelled** person-day | | placebo null exceeded | cycle estimation (Phase 2 only) | refuse without labels |
| 19 | `... L4_isf_tdd`, `M5_empirical_isf_tdd` | DiaTrend ingested | | | ISF/TDD; spectral negative control (Phase 2) | `person_day unresolved` |

## Complete commands (copy-paste, in order)

```powershell
python -m iris.tools.run_experiment L3_biological_evidence --mode production
python -m iris.tools.run_experiment L5_thermal_context --mode production
python -m iris.tools.run_experiment L2_degradation --mode production
python -m iris.tools.run_experiment L1_novelty --mode production
python -m iris.tools.run_experiment E3_vial_lag --mode production
python -m iris.tools.run_experiment E1_climate_agreement --mode production
python -m iris.tools.run_experiment E2_reconstruction_context --mode production
python -m iris.tools.run_experiment E4_exposure_generation --mode production
python -m iris.tools.run_experiment S3_virtual_population --mode production
python -m iris.tools.run_experiment F1_central --mode production
python -m iris.tools.run_experiment F2_tail --mode production
python -m iris.tools.run_experiment F3_compounding --mode production
python -m iris.tools.run_experiment F4_ablation --mode production
python -m iris.tools.run_experiment F6_dependence_transport --mode production
python -m iris.tools.run_experiment F5_admissible_set --mode production
python -m iris.tools.run_experiment R1_sensitivity --mode production
python -m iris.tools.run_experiment R2_definition_robustness --mode production
python -m iris.tools.run_experiment R3_structural_robustness --mode production
python -m iris.tools.run_experiment M4_leakage --mode production
python -m iris.tools.run_experiment M1_baseline --mode production
python -m iris.tools.run_experiment M6_circadian_recovery --mode production
python -m iris.tools.run_experiment M2_cycle_estimation --mode production
python -m iris.tools.run_experiment M3_generalisation --mode production
python -m iris.tools.run_experiment L4_isf_tdd --mode production
python -m iris.tools.run_experiment M5_empirical_isf_tdd --mode production
# verification experiments: TEST mode by design (production refuses synthetic lineage)
python -m iris.tools.run_experiment S2_thermal_kinetics --mode test
python -m iris.tools.run_experiment S1_estimator_ground_truth --mode test
python -m iris.tools.make_report
```

`python -m iris.tools.run_all --mode production` does the same in one go and never stops on BLOCKED. `--only F1_central,F2_tail` selects a subset.

Then: `python -m iris.tools.make_report` (figures from **stored** tables and the data book; never recomputes).

**Recovery:** a blocked run needs no clean-up; fix the named input and re-run. A `failed` run is a bug; keep the run folder and report it with its `log.txt`.
**Never** pass `--smoke` for a result; smoke runs are plumbing checks and are stamped as such.
