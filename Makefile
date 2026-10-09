# IRIS: dependency flow  audit -> sources -> thermal -> population -> fusion -> evaluation -> figures/tables -> databook
# Production scientific inputs missing => experiments report BLOCKED (never fabricate). Use `make pipeline-test` for the TEST-ONLY end-to-end check.
PY      ?= python3
export PYTHONPATH := src
MODE    ?= $(shell $(PY) -c "import yaml;print(yaml.safe_load(open('configs/base.yaml'))['run_mode'])")
RUN      = $(PY) -m iris.tools.run_experiment

.PHONY: readiness all audit sources thermal population fusion evaluation literature estimator figures databook test pipeline-test lint clean-derived

all: audit sources literature thermal population fusion evaluation estimator figures

audit:
	$(PY) -m iris.tools.audit_data
	$(PY) -m iris.tools.verify_registry --lenient

sources:
	$(PY) -m iris.tools.fetch_sources

literature:
	-$(RUN) L1_novelty --mode $(MODE)
	-$(RUN) L2_degradation --mode $(MODE)
	-$(RUN) L3_biological_evidence --mode $(MODE)
	-$(RUN) L4_isf_tdd --mode $(MODE)
	-$(RUN) L5_thermal_context --mode $(MODE)

thermal:
	-$(RUN) E1_climate_agreement --mode $(MODE)
	-$(RUN) E2_reconstruction_context --mode $(MODE)
	$(RUN) E3_vial_lag --mode $(MODE)
	-$(RUN) S2_thermal_kinetics --mode $(MODE)
	-$(RUN) E4_exposure_generation --mode $(MODE)

population:
	-$(RUN) S3_virtual_population --mode $(MODE)

fusion:
	-$(RUN) F1_central --mode $(MODE)
	-$(RUN) F2_tail --mode $(MODE)
	-$(RUN) F3_compounding --mode $(MODE)
	-$(RUN) F4_ablation --mode $(MODE)
	-$(RUN) F5_admissible_set --mode $(MODE)
	-$(RUN) F6_dependence_transport --mode $(MODE)

evaluation:
	-$(RUN) R1_sensitivity --mode $(MODE)
	-$(RUN) R2_definition_robustness --mode $(MODE)
	-$(RUN) R3_structural_robustness --mode $(MODE)

estimator:
	-$(RUN) S1_estimator_ground_truth --mode $(MODE)
	-$(RUN) M1_baseline --mode $(MODE)
	-$(RUN) M2_cycle_estimation --mode $(MODE)
	-$(RUN) M3_generalisation --mode $(MODE)
	-$(RUN) M4_leakage --mode $(MODE)
	-$(RUN) M5_empirical_isf_tdd --mode $(MODE)
	-$(RUN) M6_circadian_recovery --mode $(MODE)

figures:
	$(PY) -m iris.tools.make_report

databook:
	$(PY) -c "from iris.report.databook import write_databook; print(write_databook('.'))"

test:
	$(PY) -m pytest tests -q

pipeline-test:
	sh scripts_pipeline_test.sh

lint:
	$(PY) -m iris.tools.claims_lint README.md docs/decisions/*.md experiments/*/README.md experiments/*/expected_outputs.md

clean-derived:
	rm -f data/derived/*.parquet data/derived/*.json

status:
	$(PY) -m iris.tools.run_all --mode $(MODE)

ingest:
	@echo "usage: $(PY) -m iris.tools.ingest_dataset <dataset> --mode provisional|production --combine"

readiness:
	$(PY) scripts/build_readiness_matrix.py
