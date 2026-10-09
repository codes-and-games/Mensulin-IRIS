#!/bin/sh
# End-to-end pipeline in TEST mode (TEST_ONLY fixtures, smoke sizes). Never publishable. Order mirrors the dependency flow.
set -e
for e in E3_vial_lag S2_thermal_kinetics S3_virtual_population E4_exposure_generation F1_central F2_tail F3_compounding F4_ablation F5_admissible_set F6_dependence_transport R1_sensitivity R2_definition_robustness R3_structural_robustness; do
  PYTHONPATH=src python3 -m iris.tools.run_experiment $e --mode test --smoke
done
