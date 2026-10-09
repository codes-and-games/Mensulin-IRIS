# IRIS - Dual-Variable Insulin Effectiveness Model

A **computational research repository** (Computational Biology & Bioinformatics). IRIS studies how two independently
documented phenomena propagate through a mathematical model: (A) menstrual-cycle-linked variation in insulin sensitivity /
requirement in type 1 diabetes, and (B) heat-driven loss of insulin potency under defined temperature histories.

**IRIS is a research model, a simulation / inference framework. It is not a clinical dosing system, a medical device, a
treatment-recommendation system or a patient-monitoring system. It never recommends insulin doses or dose changes, never
issues storage "safe to use" verdicts, and does not represent any real patient or any experimentally tested vial.** <!-- claims-lint: ignore -->
No physical insulin, laboratory work, hardware or human participants are involved. Everything is PUBLISHED, PUBLIC_DATASET,
OPEN_RESOURCE, COMPUTED, SIMULATED or PROJECTED, with provenance. The scientific specification is the project document
(`IRIS_Standalone_Project_Document_computation_only_citation_fixes.docx`); this repository implements it.

## Scientific question
Not "does a larger dose create a larger deficit?" (largely arithmetic) but: which conclusions survive across the biological,
thermal, dependence and modelling assumptions the evidence allows - `C_set(Theta)`. The evidence-constrained set `Theta_E`
and the wider stress-test set `Theta_S` are never pooled. A conclusion is `computationally_robust`, `conditional` or
`unsupported`; computational robustness is a statement about the declared search design and budget, **not proof**.

## Architecture (layer isolation)
```
configs/ (YAML)  data/ (registry, manifest, raw read-only)  literature/ (extraction tables)
src/iris/
  common/      schemas, provenance, registry, parameters (resolution status), rng, runs, gates, io, hashing
  ingest/      audit -> mapping -> harmonise -> loaders (blocked until audited)
  features/    person-day, cycle representations, leakage guard
  estimator/   T4 glucose-insulin model, EKF, RTS smoother, baselines, mixed models, simulator
  thermal/     lag (analytic / exponential / finite-volume), kinetics K0 K1 K3 K4 K5 + fitting/LOSO, exposure, potency draws
  population/  virtual individuals: sensitivity, requirement (NO rho = 1/S), dependence R_B, checks, calibration
  fusion/      analytic results, bounds, controls, metrics, two-level MC, admissible set, adversary, endpoints, theta evaluator
  evaluate/    grouped CV, calibration, ablations, Sobol, hypothesis tests, ISF-TDD
  report/      figures, tables, captions (refuse without provenance), databook   <- read STORED results only
  tools/       run_experiment, verify_registry, fetch_sources, audit_data, claims_lint, make_report
experiments/   E1-E4, L1-L5, S1-S3, M1-M5, F1-F6, R1-R3  (README.md, config.yaml, run.py, expected_outputs.md each)
```
Layers communicate through typed tables and files only: thermal and population never import each other; fusion consumes
`potency_draws` and `virtual_population` and **never recomputes kinetics**; report never recomputes models.

## Evidence classes and "NO SOURCE, NO NUMBER"
`PUBLISHED, PUBLIC_DATASET, OPEN_RESOURCE` (external, registry-backed) and `COMPUTED, SIMULATED, PROJECTED` (IRIS outputs).
"MEASURED" is not an IRIS class. `data/sources_registry.csv` seeds the document's source ledger **with every row unverified** <!-- claims-lint: ignore -->
(`verified_by` empty): production runs refuse them until a human verifies the primary source. `data/manifest.csv` holds
file-level hashes; `python -m iris.tools.verify_registry` rejects unregistered files, hash mismatches and TEST_ONLY lineage.

Run modes (`configs/base.yaml: run_mode`):
| mode | accepts | stamp |
| --- | --- | --- |
| `production` | RESOLVED parameters, verified sources, verified literature rows | none |
| `provisional` | PENDING_VERIFY anchors and declared ASSUMPTION/STRESS completions | PROVISIONAL |
| `test` | TEST_ONLY synthetic fixtures (`tests/data`, `iris.tools.synthetic`) | TEST-ONLY |

Parameters tagged `[VERIFY]`, `[TO EXTRACT]`, `[ASSUMPTION]` in the document are never given invented values. They are
`UNRESOLVED` in YAML; only the computation that depends on them raises `ScientificBlocker` (recorded as a *blocked* run). Analyst-defined stress levels
(heterogeneity multipliers, eta grid, dependence strengths, mixture shift, transfer-discrepancy grid, ...) are `STRESS_TEST`, live in `Theta_S`, and are never evidence.

## Non-circularity
`ln rho = ln gamma - eta ln S + xi`; `rho = 1/S` is prohibited. The degenerate case (eta = 1, constant gamma, xi = 0) raises `CircularityError`
and is available only as ablation A4, whose job is to show that circularity pins `phi` at 1.

## Installation
`python >= 3.11`; `pip install -e .[dev]` (versions tested: `requirements-lock.txt`).

## Running
```
make audit        # audit raw data + registry check
make sources      # scripted retrieval (refuses unresolved addresses/versions/licences)
make thermal population fusion evaluation estimator literature
make figures      # figures + data book from STORED results
make test         # 79 tests: unit, property (hypothesis), statistical, leakage, regression (frozen hashes), data contracts
make pipeline-test  # end-to-end TEST-mode pipeline on TEST_ONLY fixtures (smoke sizes)
make all
```
`python -m iris.tools.run_experiment F1_central --mode provisional [--smoke]`. Every run writes `results/runs/<run_id>/` (immutable;
`run_id = UTC date + short git hash (+ dirty-tree hash) + config hash`) with `config.yaml`, `provenance.json` (seed, git hash, config hash, input hashes,
software versions, warnings, exclusions, evidence-class counts, partial blockers), `log.txt`, `tables/`, `figures/`.

## Reproducibility
Every stochastic function takes a `numpy.random.Generator` derived **by name** from `seed_global` (`RngTree`), so changing the number of draws in one component never changes another component's stream.
Frozen-configuration hashes are regression-tested. Reruns create a new run_id.

## Interpretation and limitations
Outputs are PROJECTED (model-based extrapolation); virtual individuals are not an observed cohort; glucose-equivalent quantities are model-conditional and secondary; potency
kinetics are only as good as the extracted literature (none is extracted yet; fewer than 5 comparable studies means between-study variance is not estimable). Lint generated prose with `python -m iris.tools.claims_lint`.
See `docs/decisions/` for open design decisions that need the research owner's confirmation.

## Running the project end to end
Start with `docs/START_HERE.md`. Scope: IRIS makes **no** claim that a code run is scientific evidence; an experiment either runs on verified, hash-registered inputs in `production` mode or reports `BLOCKED` with the exact missing input. With the open datasets only (no cycle labels) no menstrual-cycle skill claim can be made. Experiment status: `docs/experiments/readiness_matrix.md`. Resources: `docs/RESOURCES.md`. Decisions: `docs/decisions/DECISION_LOG.md`.

## Dataset attribution and licensing
Code: MIT (`LICENSE`). Datasets keep their own licences and terms and are never redistributed through this repository; every dataset used is listed with DOI, licence and version in `data/sources_registry.csv` once verified. Controlled-access datasets (DiaTrend, T1DEXI, OhioT1DM) are not included and may not be shared.
