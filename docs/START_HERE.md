# START HERE

IRIS is built so that **nothing is invented**: an experiment either runs on verified inputs or reports `BLOCKED` with the exact input it needs.
This is the one sequence to follow. Everything not listed as *your action* is already prepared in this repository.

**Keep these two apart at all times**

| "Pipeline works" | "Scientific evidence exists" |
|---|---|
| The code ran to the end | Inputs were verified, signed off, registered with hashes, and the run was made in `production` mode |
| Shown by `pytest` and `--mode test` | Only by `--mode production` on verified inputs, judged against criteria frozen in advance |

## The route

**Phase 1** uses open data and published papers: it is the claim IRIS can make now. **Phase 2** (controlled-access and cycle-labelled data) is *requested on day 1* because of long lead times, but nothing in Phase 1 waits for it. Without cycle labels IRIS may not make any menstrual-cycle skill claim (project document), so Phase 1 concludes about thermal exposure, potency loss, population heterogeneity, method plausibility and leakage-free evaluation.

| Step | What | Open |
|---|---|---|
| 0 | Set up the environment; prove the code works (about 10 minutes) | `docs/runbook/02_environment_setup.md` |
| 1 | Submit the Phase 2 access requests (the clock starts now) | `docs/data/03_diatrend.md`, `05_t1dexi.md`, `06_ohiot1dm.md` |
| 2 | Verify source **S1** (Hossmann) and its parameters: the biggest unblocker | `docs/literature/01_source_verification_runbook.md`, then `S1_hossmann_evidence.md` |
| 3 | Verify the remaining sources | same runbook |
| 4 | Fill the literature tables L2, L5 and the L1 search log | same runbook, section "Literature tables" |
| 5 | Download HUPA-UCM and BrisT1D-Open; register, audit, map, ingest | `docs/data/00_acquisition_master.md`, `01_hupa_ucm.md`, `02_bristol_brist1d.md`, `04_ingestion_and_mapping.md` |
| 6 | Climate and context data for E1/E2 | `docs/data/07_climate_and_context.md` |
| 7 | **Freeze the pre-registration before any production fusion run** | `docs/prereg/freeze_procedure.md` |
| 8 | Production runs in dependency order | `docs/runbook/05_production_runbook.md` |
| 9 | Scientific validation checklist | `docs/validation/scientific_validation_checklist.md` |
| 10 | Assemble results, reproducibility package, release | `docs/runbook/07_final_result_assembly.md`, `docs/release/release_checklist.md` |

Optional online compute (Kaggle): `docs/ml/kaggle_and_ml_guide.md`. It is **not required**; the only ML in IRIS is a small Random Forest / Gradient Boosting benchmark that runs in seconds.

## Where to look

- Only the things you must do yourself: `docs/HUMAN_ACTIONS.md`
- Why each of the 27 experiments is blocked and what removes it: `docs/experiments/readiness_matrix.md`
- Every resource needed: `docs/RESOURCES.md` (machine-readable: `manifests/resource_manifest.csv`)
- Why each scientific choice was made: `docs/decisions/DECISION_LOG.md`
- When something fails: `docs/runbook/06_troubleshooting.md`

## Rules that protect the science

1. Never edit a number in a config to make a run pass. A BLOCKED message names the one thing that removes the block.
2. Never mark a source verified unless you opened the primary source yourself and recorded where the value is.
3. Never create cycle labels. A dataset without them leaves the cycle experiments at `NOT YET JUSTIFIED`.
4. Freeze `docs/prereg/conclusions.yaml` before looking at production fusion results.
5. Controlled-access data (DiaTrend, T1DEXI, OhioT1DM) never goes into Git, Kaggle or any public place.
