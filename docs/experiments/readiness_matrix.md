# Experiment readiness matrix

27 experiments found in `experiments/`. Production status was produced by running every experiment with `--mode production` against the repository as it stands; regenerate with `make readiness`.

A BLOCKED run is the repository refusing to invent an input. It is **not** a code failure. A run that completes is **not** scientific validation: see the last column.

## Summary by class

- **READY**: 1
- **READY AFTER SOURCE VERIFICATION**: 5
- **READY AFTER DATA ACQUISITION**: 3
- **READY AFTER MAPPING**: 3
- **READY AFTER PREREG FREEZE**: 1
- **DEPENDENT ON UPSTREAM EXPERIMENT**: 10
- **SCIENTIFICALLY REFUSED**: 2
- **NOT YET JUSTIFIED**: 2

## Matrix

| Experiment | Class | Blocker type | Production status now | What removes the blocker | Supports a final claim? |
|---|---|---|---|---|---|
| E1_climate_agreement | READY AFTER DATA ACQUISITION | code limitation (no production path); research decision (location rule, thresholds); missing external input (climate records) | BLOCKED: SCIENTIFIC BLOCKER: parameter 'climate_sources' is unresolved (no registered, verified climate series available (S27-S31 unresolved in climate_sources.yaml)). Needed: register address/version/licence, run fetch_sources, verify hashes, freeze the location rule and agreement thresholds in pre | CODE LIMITATION first: E1 has no production code path (only the synthetic TEST path). Then: freeze location rule + thresholds (prereg), download + register S27-S30 (docs/data/07_climate_and_context.md), verify sources | Yes: climate-input uncertainty for the exposure model (not a biological claim) |
| E2_reconstruction_context | DEPENDENT ON UPSTREAM EXPERIMENT | code limitation (no production path); missing external input; upstream E1 | BLOCKED: SCIENTIFIC BLOCKER: parameter 'hourly_truth_and_comfort_db' is unresolved (no registered hourly climate truth (S27) or comfort database (S31)). Needed: register, hash and verify, then re-run | CODE LIMITATION (no production path, like E1); E1 done; S31 registered; S32/S34 verified | Yes: context-temperature mapping accuracy |
| E3_vial_lag | READY | none | completed run_id=20261007_nogit_9b65d844 | Nothing for the verification; S35 constants must be verified before E4/F-series use real vial geometry | Supports ONLY 'solver is numerically correct' |
| E4_exposure_generation | DEPENDENT ON UPSTREAM EXPERIMENT | missing scientific evidence (L2 degradation rows); human sign-off (S35) | completed run_id=20261007_nogit_deaf540f / COMPLETED WITH RECORDED BLOCKERS (partial, not a full result): SCIENTIFIC BLOCKER: parameter 'degradation_literature' is unresolved (no extracted rows). Needed: extract multi-temperature potency data from primary sources | L2 (kinetic model set) and, for climate scenario S5, E1/E2; S35 verified | Yes (central to the project) once potency draws exist |
| F1_central | DEPENDENT ON UPSTREAM EXPERIMENT | upstream (E4 potency draws, S3); human sign-off | BLOCKED: SCIENTIFIC BLOCKER: parameter 'virtual_population_h1.0' is unresolved (virtual_population_h1.0.parquet not found in data/derived). Needed: run the upstream experiment that produces virtual_population_h1.0 | E4 potency draws + S3 population in production mode | Yes |
| F2_tail | DEPENDENT ON UPSTREAM EXPERIMENT | upstream (E4 potency draws, S3); human sign-off | BLOCKED: SCIENTIFIC BLOCKER: parameter 'tdd' is unresolved (status=PENDING_VERIFY, mode=production). Needed: extract/verify against the primary source and register it | S3 (nine S1 rows verified); E4 potency draws (needs L2) | Yes |
| F3_compounding | DEPENDENT ON UPSTREAM EXPERIMENT | upstream (E4, S3) | BLOCKED: SCIENTIFIC BLOCKER: parameter 'virtual_population_h1.0' is unresolved (virtual_population_h1.0.parquet not found in data/derived). Needed: run the upstream experiment that produces virtual_population_h1.0 | E4 + S3 | Yes |
| F4_ablation | DEPENDENT ON UPSTREAM EXPERIMENT | upstream (E4, S3) | BLOCKED: SCIENTIFIC BLOCKER: parameter 'virtual_population_h1.0' is unresolved (virtual_population_h1.0.parquet not found in data/derived). Needed: run the upstream experiment that produces virtual_population_h1.0 | E4 + S3 | Yes (as a control) |
| F5_admissible_set | READY AFTER PREREG FREEZE | research decision (owner freezes C1/C2); upstream F-series | BLOCKED: SCIENTIFIC BLOCKER: parameter 'preregistered_conclusions' is unresolved (not frozen: ['C1_heterogeneity_penalty', 'C2_excess_concentration']). Needed: owner must review, date and freeze docs/prereg/conclusions.yaml before any fusion output is inspected | Owner freezes conclusions.yaml (docs/prereg/freeze_procedure.md), then upstream F runs | Yes: the confirmatory conclusions |
| F6_dependence_transport | DEPENDENT ON UPSTREAM EXPERIMENT | upstream (E4, S3, F5 frozen conclusions as applicable) | BLOCKED: SCIENTIFIC BLOCKER: parameter 'potency_draws' is unresolved (potency_draws.parquet not found in data/derived). Needed: run the upstream experiment that produces potency_draws | Upstream F-series + frozen conclusions | Yes (exploratory unless pre-registered) |
| L1_novelty | READY AFTER SOURCE VERIFICATION | missing scientific evidence (search not yet run/logged) | BLOCKED: SCIENTIFIC BLOCKER: parameter 'novelty_search_log' is unresolved (no searches logged: novelty has NOT been assessed). Needed: perform and log the searches (database, query, date, result counts) | Run and log the search (docs/literature/01_source_verification_runbook.md section L1); log needs searched_by | Supports the novelty statement only |
| L2_degradation | READY AFTER SOURCE VERIFICATION | human sign-off; missing scientific evidence (extraction S7-S14) | BLOCKED: SCIENTIFIC BLOCKER: parameter 'degradation_literature' is unresolved (no extracted rows). Needed: extract multi-temperature potency data from primary sources | Extract rows from S7-S14 with page/table refs, second-reader verify | Yes (kinetics) |
| L3_biological_evidence | READY AFTER SOURCE VERIFICATION | human sign-off (S1 rows) | iris.common.exceptions.UnregisteredSourceError: source 'S1' is registered but unverified: missing ['access_date', 'licence', 'verified_by'] | S1 source verification + parameter worksheet sign-off (docs/literature/S1_hossmann_evidence.md) | Yes (provenance of the anchors) |
| L4_isf_tdd | READY AFTER DATA ACQUISITION | missing access (DiaTrend) | BLOCKED: SCIENTIFIC BLOCKER: parameter 'person_day' is unresolved (no processed person-day table). Needed: obtain a registered public dataset, audit it (make audit), write configs/mappings/<dataset>.yaml, then ingest | DiaTrend access (Phase 2) + mapping; otherwise literature fallback | Supports ISF/TDD scaling assumption |
| L5_thermal_context | READY AFTER SOURCE VERIFICATION | human sign-off; missing scientific evidence (extraction) | BLOCKED: SCIENTIFIC BLOCKER: parameter 'thermal_context_parameters' is unresolved (no extracted context parameters). Needed: extract C0-C5 parameters with source/page/conditions/units | Extract parameters with page/table refs; verify | Yes (context parameters) |
| M1_baseline | READY AFTER MAPPING | missing external input (HUPA-UCM/BrisT1D download, mapping) | BLOCKED: SCIENTIFIC BLOCKER: parameter 'person_day' is unresolved (no processed person-day table). Needed: obtain a registered public dataset, audit it (make audit), write configs/mappings/<dataset>.yaml, then ingest | Ingest HUPA-UCM/BrisT1D, --combine; cycle baselines stay blocked without labels | Naive baseline only (no cycle biology) with unlabelled data |
| M2_cycle_estimation | NOT YET JUSTIFIED | scientifically unjustified without cycle labels; missing access (T1DEXI) | BLOCKED: SCIENTIFIC BLOCKER: parameter 'person_day' is unresolved (no processed person-day table). Needed: obtain a registered public dataset, audit it (make audit), write configs/mappings/<dataset>.yaml, then ingest | Obtain a dataset with cycle labels (T1DEXI via Vivli, Phase 2); until then no cycle-skill claim is permitted | No (today) |
| M3_generalisation | NOT YET JUSTIFIED | scientifically unjustified without cycle labels; missing access (T1DEXI) | BLOCKED: SCIENTIFIC BLOCKER: parameter 'person_day' is unresolved (no processed person-day table). Needed: obtain a registered public dataset, audit it (make audit), write configs/mappings/<dataset>.yaml, then ingest | Cycle-labelled data (Phase 2) | No (today) |
| M4_leakage | READY AFTER MAPPING | missing external input (any real dataset ingested) | BLOCKED: SCIENTIFIC BLOCKER: parameter 'person_day' is unresolved (no processed person-day table). Needed: obtain a registered public dataset, audit it (make audit), write configs/mappings/<dataset>.yaml, then ingest | Ingest any one real dataset + --combine | Supports 'evaluation design is leakage-free' only |
| M5_empirical_isf_tdd | READY AFTER DATA ACQUISITION | missing access (DiaTrend); possible code limitation (multi-sheet Excel layout) | BLOCKED: SCIENTIFIC BLOCKER: parameter 'person_day' is unresolved (no processed person-day table). Needed: obtain a registered public dataset, audit it (make audit), write configs/mappings/<dataset>.yaml, then ingest | DiaTrend access (Phase 2) + mapping | Negative-control calibration only |
| M6_circadian_recovery | READY AFTER MAPPING | missing external input (HUPA-UCM, BrisT1D) | BLOCKED: SCIENTIFIC BLOCKER: parameter 'events_grid' is unresolved (no ingested dataset available for any configured dataset). Needed: ingest HUPA-UCM / BrisT1D first (docs/data guides) | Download/audit/map/ingest HUPA-UCM and BrisT1D | METHOD PLAUSIBILITY only; no menstrual-cycle claim |
| R1_sensitivity | DEPENDENT ON UPSTREAM EXPERIMENT | upstream (S3, E4) | BLOCKED: SCIENTIFIC BLOCKER: parameter 'potency_draws' is unresolved (potency_draws.parquet not found in data/derived). Needed: run the upstream experiment that produces potency_draws | S3 + E4 in production | Yes (robustness) |
| R2_definition_robustness | DEPENDENT ON UPSTREAM EXPERIMENT | upstream (F-series) | BLOCKED: SCIENTIFIC BLOCKER: parameter 'potency_draws' is unresolved (potency_draws.parquet not found in data/derived). Needed: run the upstream experiment that produces potency_draws | F-series upstream | Yes (robustness) |
| R3_structural_robustness | DEPENDENT ON UPSTREAM EXPERIMENT | upstream (F-series) | BLOCKED: SCIENTIFIC BLOCKER: parameter 'potency_draws' is unresolved (potency_draws.parquet not found in data/derived). Needed: run the upstream experiment that produces potency_draws | F-series upstream | Yes (robustness) |
| S1_estimator_ground_truth | SCIENTIFICALLY REFUSED | scientifically unjustified as production evidence (synthetic truth; verification only) | iris.common.exceptions.TestOnlyDataError: production pipeline received synthetic/TEST_ONLY lineage via source 'S1_virtual_people' | Run in test mode as a code-verification result; it cannot become production evidence by design | No: verification, not evidence |
| S2_thermal_kinetics | SCIENTIFICALLY REFUSED | scientifically unjustified as production evidence (synthetic truth; verification only) | iris.common.exceptions.TestOnlyDataError: production pipeline received synthetic/TEST_ONLY lineage via source 'S2_synthetic_truth' | Run in test mode as verification only | No: verification |
| S3_virtual_population | READY AFTER SOURCE VERIFICATION | human sign-off (nine S1 rows) | BLOCKED: SCIENTIFIC BLOCKER: parameter 'tdd' is unresolved (status=PENDING_VERIFY, mode=production). Needed: extract/verify against the primary source and register it | Nine S1 rows RESOLVED (tdd, cycle, luteal length, concordance, two phase anchors) + sync_population_status; other items stay declared completions (STRESS_TEST) | Foundation for F/R series |

## Per-experiment detail

### E1_climate_agreement

- **Purpose:** Cross-source agreement/QC of 2 m temperature records at Koppen-Geiger-selected locations
- **Question:** Do ERA5-Land, ERA5, NASA POWER and IMD agree within pre-registered thresholds; what is sigma_val?
- **Required data:** S27-S30 (climate records)
- **Required literature:** S36 (published validation of reanalysis 2 m temperature)
- **Other experiments referenced in its files:** none detected
- **Class:** READY AFTER DATA ACQUISITION
- **Blocker type:** code limitation (no production path); research decision (location rule, thresholds); missing external input (climate records)
- **Production status (checked):** BLOCKED: SCIENTIFIC BLOCKER: parameter 'climate_sources' is unresolved (no registered, verified climate series available (S27-S31 unresolved in climate_sources.yaml)). Needed: register address/version/licence, run fetch_sources, verify hashes, freeze the location rule and agreement thresholds in pre
- **What removes the blocker:** CODE LIMITATION first: E1 has no production code path (only the synthetic TEST path). Then: freeze location rule + thresholds (prereg), download + register S27-S30 (docs/data/07_climate_and_context.md), verify sources
- **Expected outputs (from `expected_outputs.md`):** # Expected outputs: E1_climate_agreement Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`: - cross_source_agreement - sigma_data tables - agreement figures Every table carries an evidence class (COMPUTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
- **Validation criteria:** Records hash-registered; thresholds frozen before inspection; agreement table + figures regenerate byte-stable from seed
- **Production vs test:** Cannot run in production until a production reader is written; then needs verified sources
- **Supports a final scientific claim:** Yes: climate-input uncertainty for the exposure model (not a biological claim)
- **Caveat:** Reanalysis is not in-vial temperature; agreement does not prove accuracy

### E2_reconstruction_context

- **Purpose:** Sub-daily reconstruction (Parton-Logan) and context mapping (IMAC/ASHRAE fit + hold-out)
- **Question:** Does the reconstruction/context mapping hold out-of-sample against ASHRAE II records?
- **Required data:** S27 (via E1), S31
- **Required literature:** S32, S34, S36
- **Other experiments referenced in its files:** none detected
- **Class:** DEPENDENT ON UPSTREAM EXPERIMENT
- **Blocker type:** code limitation (no production path); missing external input; upstream E1
- **Production status (checked):** BLOCKED: SCIENTIFIC BLOCKER: parameter 'hourly_truth_and_comfort_db' is unresolved (no registered hourly climate truth (S27) or comfort database (S31)). Needed: register, hash and verify, then re-run
- **What removes the blocker:** CODE LIMITATION (no production path, like E1); E1 done; S31 registered; S32/S34 verified
- **Expected outputs (from `expected_outputs.md`):** # Expected outputs: E2_reconstruction_context Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`: - reconstruction_errors - context_mapping.json - context_validation Every table carries an evidence class (COMPUTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
- **Validation criteria:** Hold-out error vs fit error; no leakage between fit and hold-out buildings/sites
- **Production vs test:** Production only with verified sources
- **Supports a final scientific claim:** Yes: context-temperature mapping accuracy
- **Caveat:** Indoor-context mapping is a model, not a measurement of vial temperature

### E3_vial_lag

- **Purpose:** Numerical verification of the vial thermal-lag solver (lumped vs analytic vs finite-volume)
- **Question:** Does the lag solver reproduce analytic/finite-volume benchmarks within tolerance?
- **Required data:** none (physics + configs/thermal/lag.yaml)
- **Required literature:** S35 for real-world constants (not needed for the verification itself)
- **Other experiments referenced in its files:** none detected
- **Class:** READY
- **Blocker type:** none
- **Production status (checked):** completed run_id=20261007_nogit_9b65d844
- **What removes the blocker:** Nothing for the verification; S35 constants must be verified before E4/F-series use real vial geometry
- **Expected outputs (from `expected_outputs.md`):** # Expected outputs: E3_vial_lag Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`: - lag_verification.json - lag_verification_table Every table carries an evidence class (SIMULATED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
- **Validation criteria:** lag_verification.json all cases within tolerance; tests/unit/test_thermal.py passes
- **Production vs test:** Runs in production; class SIMULATED
- **Supports a final scientific claim:** Supports ONLY 'solver is numerically correct'
- **Caveat:** Verification of code, not evidence about insulin vials

### E4_exposure_generation

- **Purpose:** Generate scenario thermal exposures and potency-loss draws
- **Question:** What potency distribution results from each scenario given kinetics K0-K5?
- **Required data:** E1/E2 outputs, climate (S5 scenario), kinetics inputs
- **Required literature:** L2 degradation literature (S7-S14), L5 context parameters, S35
- **Other experiments referenced in its files:** L2, S1, S2, S3
- **Class:** DEPENDENT ON UPSTREAM EXPERIMENT
- **Blocker type:** missing scientific evidence (L2 degradation rows); human sign-off (S35)
- **Production status (checked):** completed run_id=20261007_nogit_deaf540f | COMPLETED WITH RECORDED BLOCKERS (partial, not a full result): SCIENTIFIC BLOCKER: parameter 'degradation_literature' is unresolved (no extracted rows). Needed: extract multi-temperature potency data from primary sources
- **What removes the blocker:** L2 (kinetic model set) and, for climate scenario S5, E1/E2; S35 verified
- **Expected outputs (from `expected_outputs.md`):** # Expected outputs: E4_exposure_generation Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`: - thermal_exposure - exposure_summaries - potency_draws (+ provenance) Every table carries an evidence class (SIMULATED/COMPUTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-
- **Validation criteria:** Exposure series pass THERMAL_EXPOSURE schema; potency draws pass validate_potency_draws; blocked scenarios recorded, never filled
- **Production vs test:** PARTIAL in production today: exposure tables produced, potency draws blocked
- **Supports a final scientific claim:** Yes (central to the project) once potency draws exist
- **Caveat:** Kinetic parameters come from sparse, partly disagreeing literature (see S8/S11)

### F1_central

- **Purpose:** Central fusion: effective potency x biology -> insulin-effectiveness outcome
- **Question:** Is the central estimate of effective insulin action robust to potency loss?
- **Required data:** stored potency draws (E4), virtual population (S3)
- **Required literature:** L3
- **Other experiments referenced in its files:** E4, R1, S1, S2, S3
- **Class:** DEPENDENT ON UPSTREAM EXPERIMENT
- **Blocker type:** upstream (E4 potency draws, S3); human sign-off
- **Production status (checked):** BLOCKED: SCIENTIFIC BLOCKER: parameter 'virtual_population_h1.0' is unresolved (virtual_population_h1.0.parquet not found in data/derived). Needed: run the upstream experiment that produces virtual_population_h1.0
- **What removes the blocker:** E4 potency draws + S3 population in production mode
- **Expected outputs (from `expected_outputs.md`):** # Expected outputs: F1_central Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`: - fusion_out - fusion_summary - controls - primary_endpoints - product_tail_envelope Every table carries an evidence class (PROJECTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
- **Validation criteria:** Fusion invariants and sanity checks in tests/; seed-stable tables
- **Production vs test:** Production only from production-mode upstream tables
- **Supports a final scientific claim:** Yes
- **Caveat:** Depends on all upstream assumptions

### F2_tail

- **Purpose:** Tail-risk fusion with large virtual population
- **Question:** How large are the tails of the effectiveness distribution?
- **Required data:** S3 population (n_tail=100000), potency draws
- **Required literature:** L3
- **Other experiments referenced in its files:** S2, S3
- **Class:** DEPENDENT ON UPSTREAM EXPERIMENT
- **Blocker type:** upstream (E4 potency draws, S3); human sign-off
- **Production status (checked):** BLOCKED: SCIENTIFIC BLOCKER: parameter 'tdd' is unresolved (status=PENDING_VERIFY, mode=production). Needed: extract/verify against the primary source and register it
- **What removes the blocker:** S3 (nine S1 rows verified); E4 potency draws (needs L2)
- **Expected outputs (from `expected_outputs.md`):** # Expected outputs: F2_tail Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`: - tail_exceedance - product_tail_envelope_* - mc_convergence Every table carries an evidence class (PROJECTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
- **Validation criteria:** Tail estimates stable across seeds; MC error reported
- **Production vs test:** Production only
- **Supports a final scientific claim:** Yes
- **Caveat:** Tail quantities are sensitive to unresolved biological parameters (completion options are STRESS_TEST)

### F3_compounding

- **Purpose:** Compounding: repeated exposure across consecutive dosing days
- **Question:** Does cumulative exposure change the conclusions?
- **Required data:** potency draws, S3
- **Required literature:** L3, L2
- **Other experiments referenced in its files:** R2, S3
- **Class:** DEPENDENT ON UPSTREAM EXPERIMENT
- **Blocker type:** upstream (E4, S3)
- **Production status (checked):** BLOCKED: SCIENTIFIC BLOCKER: parameter 'virtual_population_h1.0' is unresolved (virtual_population_h1.0.parquet not found in data/derived). Needed: run the upstream experiment that produces virtual_population_h1.0
- **What removes the blocker:** E4 + S3
- **Expected outputs (from `expected_outputs.md`):** # Expected outputs: F3_compounding Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`: - compounding Every table carries an evidence class (PROJECTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
- **Validation criteria:** Matches single-day results at J=1
- **Production vs test:** Production only
- **Supports a final scientific claim:** Yes
- **Caveat:** Independence assumptions across days are modelled, not measured

### F4_ablation

- **Purpose:** Ablation controls (incl. A4 circularity control)
- **Question:** Do conclusions survive removing each modelling component; is there circularity?
- **Required data:** as F1
- **Required literature:** L3
- **Other experiments referenced in its files:** E4, R2, S2, S3
- **Class:** DEPENDENT ON UPSTREAM EXPERIMENT
- **Blocker type:** upstream (E4, S3)
- **Production status (checked):** BLOCKED: SCIENTIFIC BLOCKER: parameter 'virtual_population_h1.0' is unresolved (virtual_population_h1.0.parquet not found in data/derived). Needed: run the upstream experiment that produces virtual_population_h1.0
- **What removes the blocker:** E4 + S3
- **Expected outputs (from `expected_outputs.md`):** # Expected outputs: F4_ablation Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`: - ablation_rows - ablation_table Every table carries an evidence class (PROJECTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
- **Validation criteria:** A4 pushes phi toward 1 (else FAILED_CONTROL)
- **Production vs test:** Production only
- **Supports a final scientific claim:** Yes (as a control)
- **Caveat:** A failed control invalidates dependent claims

### F5_admissible_set

- **Purpose:** Evaluate pre-registered conclusions over the admissible set
- **Question:** Which pre-registered conclusions hold across the admissible parameter set?
- **Required data:** F1/F2/F4 outputs
- **Required literature:** docs/prereg/conclusions.yaml (C1, C2)
- **Other experiments referenced in its files:** S1
- **Class:** READY AFTER PREREG FREEZE
- **Blocker type:** research decision (owner freezes C1/C2); upstream F-series
- **Production status (checked):** BLOCKED: SCIENTIFIC BLOCKER: parameter 'preregistered_conclusions' is unresolved (not frozen: ['C1_heterogeneity_penalty', 'C2_excess_concentration']). Needed: owner must review, date and freeze docs/prereg/conclusions.yaml before any fusion output is inspected
- **What removes the blocker:** Owner freezes conclusions.yaml (docs/prereg/freeze_procedure.md), then upstream F runs
- **Expected outputs (from `expected_outputs.md`):** # Expected outputs: F5_admissible_set Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`: - conclusion_classes - theta_evaluations - adversarial_search - design_coverage Every table carries an evidence class (PROJECTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
- **Validation criteria:** Margins computed against FROZEN thresholds only
- **Production vs test:** Production only after freeze
- **Supports a final scientific claim:** Yes: the confirmatory conclusions
- **Caveat:** Thresholds may not be changed after results are seen

### F6_dependence_transport

- **Purpose:** Dependence/transport: how conclusions move along dependence axes
- **Question:** Do conclusions hold when dependence between potency and biology changes?
- **Required data:** as F5
- **Required literature:** L3
- **Other experiments referenced in its files:** S1, S3
- **Class:** DEPENDENT ON UPSTREAM EXPERIMENT
- **Blocker type:** upstream (E4, S3, F5 frozen conclusions as applicable)
- **Production status (checked):** BLOCKED: SCIENTIFIC BLOCKER: parameter 'potency_draws' is unresolved (potency_draws.parquet not found in data/derived). Needed: run the upstream experiment that produces potency_draws
- **What removes the blocker:** Upstream F-series + frozen conclusions
- **Expected outputs (from `expected_outputs.md`):** # Expected outputs: F6_dependence_transport Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`: - sweeps - flip_points Every table carries an evidence class (PROJECTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
- **Validation criteria:** Margins per axis value; blocked cells recorded
- **Production vs test:** Production only
- **Supports a final scientific claim:** Yes (exploratory unless pre-registered)
- **Caveat:** Dependence structures are analyst-defined completions

### L1_novelty

- **Purpose:** Novelty/evidence search log validation
- **Question:** Is there prior work that already answers the IRIS question?
- **Required data:** literature/novelty_search_log.csv (human search)
- **Required literature:** all
- **Other experiments referenced in its files:** none detected
- **Class:** READY AFTER SOURCE VERIFICATION
- **Blocker type:** missing scientific evidence (search not yet run/logged)
- **Production status (checked):** BLOCKED: SCIENTIFIC BLOCKER: parameter 'novelty_search_log' is unresolved (no searches logged: novelty has NOT been assessed). Needed: perform and log the searches (database, query, date, result counts)
- **What removes the blocker:** Run and log the search (docs/literature/01_source_verification_runbook.md section L1); log needs searched_by
- **Expected outputs (from `expected_outputs.md`):** # Expected outputs: L1_novelty Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`: - search_log - near_neighbours Every table carries an evidence class (COMPUTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
- **Validation criteria:** Log has dates, databases, queries, result counts, closest prior study
- **Production vs test:** Production uses the human-authored log
- **Supports a final scientific claim:** Supports the novelty statement only
- **Caveat:** Search completeness cannot be proven

### L2_degradation

- **Purpose:** Extract multi-temperature potency data -> fit kinetic models K1 -> LOSO evaluation
- **Question:** Which kinetic models are supported by the published degradation data?
- **Required data:** literature/degradation_literature.csv
- **Required literature:** S7-S14
- **Other experiments referenced in its files:** none detected
- **Class:** READY AFTER SOURCE VERIFICATION
- **Blocker type:** human sign-off; missing scientific evidence (extraction S7-S14)
- **Production status (checked):** BLOCKED: SCIENTIFIC BLOCKER: parameter 'degradation_literature' is unresolved (no extracted rows). Needed: extract multi-temperature potency data from primary sources
- **What removes the blocker:** Extract rows from S7-S14 with page/table refs, second-reader verify
- **Expected outputs (from `expected_outputs.md`):** # Expected outputs: L2_degradation Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`: - fit_diagnostics - loso_predictions - loso_summary - ensemble_weights Every table carries an evidence class (COMPUTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
- **Validation criteria:** LOSO error, parameter CIs; verified rows only in production
- **Production vs test:** Production uses verified rows only
- **Supports a final scientific claim:** Yes (kinetics)
- **Caveat:** Data are few and disagree (S8 vs S7/S11); report as such

### L3_biological_evidence

- **Purpose:** Status table of biological anchors
- **Question:** Which biological parameters are verified, pending or unresolved?
- **Required data:** literature/biological_evidence.csv
- **Required literature:** S1 (+S3, S26 context)
- **Other experiments referenced in its files:** S1
- **Class:** READY AFTER SOURCE VERIFICATION
- **Blocker type:** human sign-off (S1 rows)
- **Production status (checked):** iris.common.exceptions.UnregisteredSourceError: source 'S1' is registered but unverified: missing ['access_date', 'licence', 'verified_by']
- **What removes the blocker:** S1 source verification + parameter worksheet sign-off (docs/literature/S1_hossmann_evidence.md)
- **Expected outputs (from `expected_outputs.md`):** # Expected outputs: L3_biological_evidence Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`: - parameter_sheet Every table carries an evidence class (COMPUTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
- **Validation criteria:** Every anchor RESOLVED with page/table ref + second reader
- **Production vs test:** Production uses RESOLVED rows only
- **Supports a final scientific claim:** Yes (provenance of the anchors)
- **Caveat:** Several S1 values (phase contrasts other than 2 phases, anovulatory prevalence) are still [TO EXTRACT]

### L4_isf_tdd

- **Purpose:** Empirical ISF vs TDD relationship
- **Question:** How does clinician ISF relate to TDD?
- **Required data:** person_day with isf_clinician (DiaTrend pump settings)
- **Required literature:** published ISF/TDD reports (fallback)
- **Other experiments referenced in its files:** M5
- **Class:** READY AFTER DATA ACQUISITION
- **Blocker type:** missing access (DiaTrend)
- **Production status (checked):** BLOCKED: SCIENTIFIC BLOCKER: parameter 'person_day' is unresolved (no processed person-day table). Needed: obtain a registered public dataset, audit it (make audit), write configs/mappings/<dataset>.yaml, then ingest
- **What removes the blocker:** DiaTrend access (Phase 2) + mapping; otherwise literature fallback
- **Expected outputs (from `expected_outputs.md`):** # Expected outputs: L4_isf_tdd Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`: - isf_tdd_between_person Every table carries an evidence class (COMPUTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
- **Validation criteria:** Fit diagnostics; person-grouped uncertainty
- **Production vs test:** Production only with ingested data
- **Supports a final scientific claim:** Supports ISF/TDD scaling assumption
- **Caveat:** Pump-setting ISF is clinician-set, not measured sensitivity

### L5_thermal_context

- **Purpose:** Thermal-context parameter table
- **Question:** What published parameters define indoor/outdoor context mapping?
- **Required data:** literature/thermal_context_parameters.csv
- **Required literature:** S31, S32, S35
- **Other experiments referenced in its files:** none detected
- **Class:** READY AFTER SOURCE VERIFICATION
- **Blocker type:** human sign-off; missing scientific evidence (extraction)
- **Production status (checked):** BLOCKED: SCIENTIFIC BLOCKER: parameter 'thermal_context_parameters' is unresolved (no extracted context parameters). Needed: extract C0-C5 parameters with source/page/conditions/units
- **What removes the blocker:** Extract parameters with page/table refs; verify
- **Expected outputs (from `expected_outputs.md`):** # Expected outputs: L5_thermal_context Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`: - context_parameters Every table carries an evidence class (COMPUTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
- **Validation criteria:** Verified rows only
- **Production vs test:** Production uses verified rows only
- **Supports a final scientific claim:** Yes (context parameters)
- **Caveat:** Parameters are population/regional, not site-specific

### M1_baseline

- **Purpose:** Baseline suite for relative TDD (naive mean; harmonic regression on cycle position)
- **Question:** What accuracy does a person-free baseline achieve under subject-grouped CV?
- **Required data:** combined person_day
- **Required literature:** none
- **Other experiments referenced in its files:** R2
- **Class:** READY AFTER MAPPING
- **Blocker type:** missing external input (HUPA-UCM/BrisT1D download, mapping)
- **Production status (checked):** BLOCKED: SCIENTIFIC BLOCKER: parameter 'person_day' is unresolved (no processed person-day table). Needed: obtain a registered public dataset, audit it (make audit), write configs/mappings/<dataset>.yaml, then ingest
- **What removes the blocker:** Ingest HUPA-UCM/BrisT1D, --combine; cycle baselines stay blocked without labels
- **Expected outputs (from `expected_outputs.md`):** # Expected outputs: M1_baseline Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`: - baseline_scores Every table carries an evidence class (COMPUTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
- **Validation criteria:** Subject-grouped CV only; naive baseline reported
- **Production vs test:** Production needs verified+registered datasets
- **Supports a final scientific claim:** Naive baseline only (no cycle biology) with unlabelled data
- **Caveat:** Cycle baselines need real cycle labels (Phase 2)

### M2_cycle_estimation

- **Purpose:** Cycle-phase estimation vs placebo cycles
- **Question:** Does the estimator recover cycle-linked sensitivity beyond placebo cycles?
- **Required data:** person-day/events WITH dataset-provided cycle labels
- **Required literature:** S1 for expected effect size
- **Other experiments referenced in its files:** none detected
- **Class:** NOT YET JUSTIFIED
- **Blocker type:** scientifically unjustified without cycle labels; missing access (T1DEXI)
- **Production status (checked):** BLOCKED: SCIENTIFIC BLOCKER: parameter 'person_day' is unresolved (no processed person-day table). Needed: obtain a registered public dataset, audit it (make audit), write configs/mappings/<dataset>.yaml, then ingest
- **What removes the blocker:** Obtain a dataset with cycle labels (T1DEXI via Vivli, Phase 2); until then no cycle-skill claim is permitted
- **Expected outputs (from `expected_outputs.md`):** # Expected outputs: M2_cycle_estimation Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`: - cycle_amplitude Every table carries an evidence class (COMPUTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
- **Validation criteria:** Placebo-cycle null (n=60) must be exceeded
- **Production vs test:** Refused for unlabelled data
- **Supports a final scientific claim:** No (today)
- **Caveat:** Manufacturing labels is forbidden (project document)

### M3_generalisation

- **Purpose:** Generalisation of RF/GB benchmarks across subjects (grouped CV)
- **Question:** Do cycle-aware benchmarks generalise to held-out subjects?
- **Required data:** person_day with cycle labels
- **Required literature:** none
- **Other experiments referenced in its files:** R2
- **Class:** NOT YET JUSTIFIED
- **Blocker type:** scientifically unjustified without cycle labels; missing access (T1DEXI)
- **Production status (checked):** BLOCKED: SCIENTIFIC BLOCKER: parameter 'person_day' is unresolved (no processed person-day table). Needed: obtain a registered public dataset, audit it (make audit), write configs/mappings/<dataset>.yaml, then ingest
- **What removes the blocker:** Cycle-labelled data (Phase 2)
- **Expected outputs (from `expected_outputs.md`):** # Expected outputs: M3_generalisation Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`: - loso_scores Every table carries an evidence class (COMPUTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
- **Validation criteria:** Leave-subject-out only
- **Production vs test:** Refused without labels
- **Supports a final scientific claim:** No (today)
- **Caveat:** Same as M2

### M4_leakage

- **Purpose:** Explicit leakage tests incl. identity canary (RF)
- **Question:** Does the CV design prevent subject/time leakage; can the canary detect it?
- **Required data:** any combined person_day
- **Required literature:** none
- **Other experiments referenced in its files:** none detected
- **Class:** READY AFTER MAPPING
- **Blocker type:** missing external input (any real dataset ingested)
- **Production status (checked):** BLOCKED: SCIENTIFIC BLOCKER: parameter 'person_day' is unresolved (no processed person-day table). Needed: obtain a registered public dataset, audit it (make audit), write configs/mappings/<dataset>.yaml, then ingest
- **What removes the blocker:** Ingest any one real dataset + --combine
- **Expected outputs (from `expected_outputs.md`):** # Expected outputs: M4_leakage Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`: - leakage_tests Every table carries an evidence class (COMPUTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
- **Validation criteria:** Grouped splits disjoint; row-wise split demonstrably leaks; canary unpredictable under grouped CV
- **Production vs test:** Production needs verified+registered data
- **Supports a final scientific claim:** Supports 'evaluation design is leakage-free' only
- **Caveat:** Passing says nothing about biology

### M5_empirical_isf_tdd

- **Purpose:** Spectral negative control in unlabelled long series
- **Question:** Is a 21-35 day periodicity detectable in TDD without labels (females vs males)?
- **Required data:** DiaTrend (>=150 pump days for the female group)
- **Required literature:** none
- **Other experiments referenced in its files:** none detected
- **Class:** READY AFTER DATA ACQUISITION
- **Blocker type:** missing access (DiaTrend); possible code limitation (multi-sheet Excel layout)
- **Production status (checked):** BLOCKED: SCIENTIFIC BLOCKER: parameter 'person_day' is unresolved (no processed person-day table). Needed: obtain a registered public dataset, audit it (make audit), write configs/mappings/<dataset>.yaml, then ingest
- **What removes the blocker:** DiaTrend access (Phase 2) + mapping
- **Expected outputs (from `expected_outputs.md`):** # Expected outputs: M5_empirical_isf_tdd Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`: - isf_tdd_fit Every table carries an evidence class (COMPUTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
- **Validation criteria:** False-positive rate under shuffled data reported
- **Production vs test:** Production only with ingested DiaTrend
- **Supports a final scientific claim:** Negative-control calibration only
- **Caveat:** Absence of a peak is not absence of cycle effects

### M6_circadian_recovery

- **Purpose:** Circadian (24 h) sensitivity recovery on real CGM/insulin/carb series (V2)
- **Question:** Does the estimator recover a reproducible 24 h pattern in real data vs placebo shifts?
- **Required data:** HUPA-UCM + BrisT1D events grids
- **Required literature:** none (direction vs literature: [VERIFY])
- **Other experiments referenced in its files:** M2
- **Class:** READY AFTER MAPPING
- **Blocker type:** missing external input (HUPA-UCM, BrisT1D)
- **Production status (checked):** BLOCKED: SCIENTIFIC BLOCKER: parameter 'events_grid' is unresolved (no ingested dataset available for any configured dataset). Needed: ingest HUPA-UCM / BrisT1D first (docs/data guides)
- **What removes the blocker:** Download/audit/map/ingest HUPA-UCM and BrisT1D
- **Expected outputs (from `expected_outputs.md`):** # Expected outputs: M6_circadian_recovery Written to `results/runs/<run_id>/tables/`: - circadian_person (per person: amplitude, peak hour, split-half r) - circadian_population (per dataset: amplitude + CI, peak + CI, placebo p, split-half, `reproducible`) - circadian_profile (24 hourly values per dataset) - circadian_nuisance_sensitivity (amplitud
- **Validation criteria:** Split-half reproducibility; placebo shifts; nuisance-scale sensitivity
- **Production vs test:** Production needs verified+registered data
- **Supports a final scientific claim:** METHOD PLAUSIBILITY only; no menstrual-cycle claim
- **Caveat:** Small cohorts; HUPA-UCM is ~2 weeks per person

### R1_sensitivity

- **Purpose:** Global sensitivity (Sobol/SALib) of outcomes
- **Question:** Which inputs drive outcome variance?
- **Required data:** fusion machinery + populations
- **Required literature:** all
- **Other experiments referenced in its files:** S1, S3
- **Class:** DEPENDENT ON UPSTREAM EXPERIMENT
- **Blocker type:** upstream (S3, E4)
- **Production status (checked):** BLOCKED: SCIENTIFIC BLOCKER: parameter 'potency_draws' is unresolved (potency_draws.parquet not found in data/derived). Needed: run the upstream experiment that produces potency_draws
- **What removes the blocker:** S3 + E4 in production
- **Expected outputs (from `expected_outputs.md`):** # Expected outputs: R1_sensitivity Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`: - sobol_by_seed - sobol_summary - thermal_variance_share - tornado Every table carries an evidence class (COMPUTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
- **Validation criteria:** Indices sum sanity; bootstrap CIs
- **Production vs test:** Production only
- **Supports a final scientific claim:** Yes (robustness)
- **Caveat:** Climate input reported 'not applicable' while S5 is blocked

### R2_definition_robustness

- **Purpose:** Robustness to outcome definitions
- **Question:** Do conclusions survive alternative definitions?
- **Required data:** fusion outputs
- **Required literature:** L3
- **Other experiments referenced in its files:** F1, S1, S3
- **Class:** DEPENDENT ON UPSTREAM EXPERIMENT
- **Blocker type:** upstream (F-series)
- **Production status (checked):** BLOCKED: SCIENTIFIC BLOCKER: parameter 'potency_draws' is unresolved (potency_draws.parquet not found in data/derived). Needed: run the upstream experiment that produces potency_draws
- **What removes the blocker:** F-series upstream
- **Expected outputs (from `expected_outputs.md`):** # Expected outputs: R2_definition_robustness Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`: - stability_matrix - stability_summary Every table carries an evidence class (PROJECTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
- **Validation criteria:** Per-definition margins
- **Production vs test:** Production only
- **Supports a final scientific claim:** Yes (robustness)
- **Caveat:** Definition set fixed in advance

### R3_structural_robustness

- **Purpose:** Robustness to structural model choices
- **Question:** Do conclusions hold across structural alternatives?
- **Required data:** fusion outputs
- **Required literature:** L3
- **Other experiments referenced in its files:** S1, S3
- **Class:** DEPENDENT ON UPSTREAM EXPERIMENT
- **Blocker type:** upstream (F-series)
- **Production status (checked):** BLOCKED: SCIENTIFIC BLOCKER: parameter 'potency_draws' is unresolved (potency_draws.parquet not found in data/derived). Needed: run the upstream experiment that produces potency_draws
- **What removes the blocker:** F-series upstream
- **Expected outputs (from `expected_outputs.md`):** # Expected outputs: R3_structural_robustness Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`: - structural_results - structural_flips Every table carries an evidence class (PROJECTED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
- **Validation criteria:** Blocked structures are reported, not dropped
- **Production vs test:** Production only
- **Supports a final scientific claim:** Yes (robustness)
- **Caveat:** Structures are analyst-chosen

### S1_estimator_ground_truth

- **Purpose:** Verify the EKF/RTS estimator against known synthetic truth
- **Question:** Does the estimator recover a known sensitivity profile?
- **Required data:** none (simulator, ASSUMPTION constants)
- **Required literature:** T4 constants
- **Other experiments referenced in its files:** none detected
- **Class:** SCIENTIFICALLY REFUSED
- **Blocker type:** scientifically unjustified as production evidence (synthetic truth; verification only)
- **Production status (checked):** iris.common.exceptions.TestOnlyDataError: production pipeline received synthetic/TEST_ONLY lineage via source 'S1_virtual_people'
- **What removes the blocker:** Run in test mode as a code-verification result; it cannot become production evidence by design
- **Expected outputs (from `expected_outputs.md`):** # Expected outputs: S1_estimator_ground_truth Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`: - recovery_trials - recovery_summary Every table carries an evidence class (SIMULATED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
- **Validation criteria:** Recovery error small; calibrated intervals
- **Production vs test:** TEST only (synthetic lineage)
- **Supports a final scientific claim:** No: verification, not evidence
- **Caveat:** Synthetic truth validates code, not biology

### S2_thermal_kinetics

- **Purpose:** Verify kinetic fitting recovers known synthetic parameters
- **Question:** Does K1 fitting recover truth?
- **Required data:** none (synthetic)
- **Required literature:** none
- **Other experiments referenced in its files:** none detected
- **Class:** SCIENTIFICALLY REFUSED
- **Blocker type:** scientifically unjustified as production evidence (synthetic truth; verification only)
- **Production status (checked):** iris.common.exceptions.TestOnlyDataError: production pipeline received synthetic/TEST_ONLY lineage via source 'S2_synthetic_truth'
- **What removes the blocker:** Run in test mode as verification only
- **Expected outputs (from `expected_outputs.md`):** # Expected outputs: S2_thermal_kinetics Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`: - k1_recovery - forward_checks Every table carries an evidence class (SIMULATED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
- **Validation criteria:** Parameter recovery within tolerance
- **Production vs test:** TEST only
- **Supports a final scientific claim:** No: verification
- **Caveat:** As S1

### S3_virtual_population

- **Purpose:** Build the virtual population
- **Question:** Population of TDD/cycle/sensitivity parameters anchored to S1
- **Required data:** none
- **Required literature:** S1 (L3 table)
- **Other experiments referenced in its files:** S1
- **Class:** READY AFTER SOURCE VERIFICATION
- **Blocker type:** human sign-off (nine S1 rows)
- **Production status (checked):** BLOCKED: SCIENTIFIC BLOCKER: parameter 'tdd' is unresolved (status=PENDING_VERIFY, mode=production). Needed: extract/verify against the primary source and register it
- **What removes the blocker:** Nine S1 rows RESOLVED (tdd, cycle, luteal length, concordance, two phase anchors) + sync_population_status; other items stay declared completions (STRESS_TEST)
- **Expected outputs (from `expected_outputs.md`):** # Expected outputs: S3_virtual_population Written to `results/runs/<run_id>/tables/` (parquet + `.provenance.json` sidecars) and `figures/`: - population_checks - virtual_population_h* Every table carries an evidence class (SIMULATED) and the run's provenance. Non-production runs are stamped PROVISIONAL or TEST-ONLY.
- **Validation criteria:** Marginals match anchors; seeds reproducible
- **Production vs test:** Production needs RESOLVED anchors
- **Supports a final scientific claim:** Foundation for F/R series
- **Caveat:** Completions are analyst-defined (Theta_S)
