# IRIS data book (generated; do not edit)

## Limitations
- IRIS is a research simulation/inference framework, not a clinical dosing system or medical device; no output is a dosing or treatment recommendation.
- Virtual individuals are SIMULATED; they are not an observed cohort. PROJECTED outputs are model-based extrapolations, not empirical findings.
- Computational robustness is conditional on the declared admissible set and adversarial search budget; it is not proof of real-world truth.
- Parameters tagged unresolved/pending-verification are not production inputs; provisional and test runs are stamped accordingly.
- Glucose-equivalent quantities are model-conditional and secondary.

## Sources
| source_id | class | title | licence | verified_by |
| --- | --- | --- | --- | --- |
| S1 | PUBLISHED | Hossmann et al. Effects of menstrual cycle on insulin sensitivity in type 1 diabetes (AID cohort) | — | UNVERIFIED |
| S10 | PUBLISHED | Isophane insulin at 5, 25, 40 C | — | UNVERIFIED |
| S11 | PUBLISHED | Cochrane review CD015385: Thermal stability and storage of human insulin | — | UNVERIFIED |
| S12 | PUBLISHED | Forsander et al. Insulin thermostability in a real-world setting | — | UNVERIFIED |
| S13 | PUBLISHED | Brange et al. Chemical stability of insulin 1. Hydrolytic degradation during storage | — | UNVERIFIED |
| S14 | PUBLISHED | Oliva et al. Influence of temperature and shaking on stability of insulin preparations | — | UNVERIFIED |
| S15 | PUBLIC_DATASET | HUPA-UCM diabetes dataset | — | UNVERIFIED |
| S16 | PUBLIC_DATASET | DiaTrend | — | UNVERIFIED |
| S17 | PUBLIC_DATASET | BrisT1D dataset | — | UNVERIFIED |
| S18 | PUBLIC_DATASET | OhioT1DM dataset | — | UNVERIFIED |
| S19 | PUBLIC_DATASET | T1DEXI / T1DEXIP | — | UNVERIFIED |
| S2 | PUBLISHED | Brown et al. Fluctuations of hyperglycemia and insulin sensitivity linked to menstrual cycle phases in T1D | — | UNVERIFIED |
| S26 | PUBLISHED | Menstrual Cycle, Glucose Control and Insulin Sensitivity in T1D: A Systematic Review | — | UNVERIFIED |
| S27 | PUBLIC_DATASET | ERA5-Land hourly reanalysis (Munoz-Sabater et al. 2021) | — | UNVERIFIED |
| S28 | PUBLIC_DATASET | ERA5 global reanalysis (Hersbach et al. 2020) | — | UNVERIFIED |
| S29 | PUBLIC_DATASET | NASA POWER daily climate data | — | UNVERIFIED |
| S3 | PUBLISHED | T1DEXI menstrual-cycle analysis: Changing glucose levels during the menstrual cycle (Type 1 Diabetes Exercise Initiative) | — | UNVERIFIED |
| S30 | PUBLIC_DATASET | IMD high-resolution daily gridded temperature (Srivastava et al. 2009) | — | UNVERIFIED |
| S31 | PUBLIC_DATASET | ASHRAE Global Thermal Comfort Database II | — | UNVERIFIED |
| S32 | PUBLISHED | Manu et al. India Model for Adaptive Comfort (IMAC) | — | UNVERIFIED |
| S33 | PUBLISHED | Beck et al. Koppen-Geiger climate classification maps | — | UNVERIFIED |
| S34 | PUBLISHED | Parton & Logan. A model for diurnal variation in soil and air temperature | — | UNVERIFIED |
| S35 | OPEN_RESOURCE | Heat-transfer handbook correlations; glass-vial dimension standard; national standards body water/glass tables | — | UNVERIFIED |
| S36 | PUBLISHED | Published validation studies of ERA5 / ERA5-Land / NASA POWER 2 m temperature | — | UNVERIFIED |
| S38 | OPEN_RESOURCE | TIMES programme (Diabetes Center Berne with Tidepool) funder summary; NCT06282055 | — | UNVERIFIED |
| S4 | PUBLISHED | Rojas Lopez et al. Glycemic control during the menstrual cycle in women with T1D: AID performance | — | UNVERIFIED |
| S5 | PUBLISHED | Adolescent AID menstrual-cycle study | — | UNVERIFIED |
| S7 | PUBLISHED | Vimalavathini & Gitanjali. Effect of temperature on the potency and pharmacological action of insulin | — | UNVERIFIED |
| S8 | PUBLISHED | Effect of temperature on the stability of in-use insulin pens | — | UNVERIFIED |
| S9 | PUBLISHED | Insulin pen stability under fluctuating 25-37 C | — | UNVERIFIED |

## Runs
| run_id | experiment | status | mode | tables | figures |
| --- | --- | --- | --- | --- | --- |
| 20261009_001156a+cbb7be_09da9318 | S1_estimator_ground_truth | completed | test | 2 | 1 |
| 20261009_001156a+cbb7be_1171cb39 | R2_definition_robustness | completed | test | 2 | 0 |
| 20261009_001156a+cbb7be_13701170 | S2_thermal_kinetics | completed | test | 2 | 0 |
| 20261009_001156a+cbb7be_174873c5 | L2_degradation | completed | test | 4 | 0 |
| 20261009_001156a+cbb7be_1761cd18 | E4_exposure_generation | completed | test | 5 | 0 |
| 20261009_001156a+cbb7be_33dfa0c5 | F6_dependence_transport | completed | test | 2 | 1 |
| 20261009_001156a+cbb7be_368c8e1d | M6_circadian_recovery | completed | test | 4 | 0 |
| 20261009_001156a+cbb7be_445ac67b | E3_vial_lag | completed | test | 1 | 0 |
| 20261009_001156a+cbb7be_44c97ba6 | S3_virtual_population | completed | test | 4 | 0 |
| 20261009_001156a+cbb7be_47120716 | M1_baseline | completed | test | 1 | 0 |
| 20261009_001156a+cbb7be_51b64109 | R3_structural_robustness | completed | test | 2 | 0 |
| 20261009_001156a+cbb7be_51de48fd | M3_generalisation | completed | test | 1 | 0 |
| 20261009_001156a+cbb7be_5c5ebb69 | L5_thermal_context | blocked | test | 0 | 0 |
| 20261009_001156a+cbb7be_5dbd716e | F3_compounding | completed | test | 1 | 0 |
| 20261009_001156a+cbb7be_70c1c5b9 | L1_novelty | blocked | test | 0 | 0 |
| 20261009_001156a+cbb7be_7fb033d8 | R1_sensitivity | completed | test | 4 | 1 |
| 20261009_001156a+cbb7be_80c4b5a1 | M4_leakage | completed | test | 1 | 0 |
| 20261009_001156a+cbb7be_81984305 | L4_isf_tdd | completed | test | 1 | 0 |
| 20261009_001156a+cbb7be_8fd7e406 | L3_biological_evidence | completed | test | 1 | 0 |
| 20261009_001156a+cbb7be_8fe6edf5 | F4_ablation | completed | test | 2 | 0 |
| 20261009_001156a+cbb7be_b85633fa | E2_reconstruction_context | completed | test | 2 | 0 |
| 20261009_001156a+cbb7be_b93d6c87 | F2_tail | completed | test | 3 | 0 |
| 20261009_001156a+cbb7be_c1013acf | M2_cycle_estimation | completed | test | 1 | 0 |
| 20261009_001156a+cbb7be_e95a20c9 | E1_climate_agreement | completed | test | 2 | 0 |
| 20261009_001156a+cbb7be_ea5768b2 | F1_central | completed | test | 5 | 1 |
| 20261009_001156a+cbb7be_f5bb62b9 | M5_empirical_isf_tdd | completed | test | 1 | 0 |
| 20261009_001156a+cbb7be_f5f6e1ff | F5_admissible_set | completed | test | 4 | 1 |
| 20261010_1024429+0b8bdc_c6d3ebf7 | M6_circadian_recovery | completed | provisional | 4 | 0 |
| 20261010_1024429+93a2b9_7024849c | M4_leakage | completed | provisional | 1 | 0 |
| 20261010_1024429+93a2b9_e9455bf2 | M1_baseline | completed | provisional | 1 | 0 |
| 20261010_1024429+a33259_5f01a6c2 | M1_baseline | completed | provisional | 1 | 0 |
| 20261010_1024429+a33259_da895a2d | M4_leakage | completed | provisional | 1 | 0 |
