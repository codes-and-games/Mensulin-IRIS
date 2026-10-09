# Human-action checklist: only what you must do yourself

Format per action: **what / where / which resource / keep as evidence / put it here / run afterwards / then open**.

| # | Action | Where | Resource | Keep as evidence | Destination | Command afterwards | Then open |
|---|---|---|---|---|---|---|---|
| 1 | Put the project under Git, push, make CI run | github.com (your account) | repo without data | green CI run | GitHub | `git init; git add .; git commit -m "IRIS execution package"; git branch -M main; git remote add origin <url>; git push -u origin main` | `docs/runbook/02_environment_setup.md` |
| 2 | Request DiaTrend access | synapse.org -> DOI 10.7303/syn38187184 | access request | request id, dates | resource manifest note (not Git) | none | `docs/data/03_diatrend.md` |
| 3 | Request T1DEXI access | vivli.org | request + DUA | request id, signed DUA (private) | note only | none | `docs/data/05_t1dexi.md` |
| 4 | Request OhioT1DM (optional) | official dataset page | DUA | agreement date | note only | none | `docs/data/06_ohiot1dm.md` |
| 5 | Open the Hossmann paper and complete the 9 critical parameter rows + the S1 source row | PMC13493352 / doi:10.2337/dc26-0692 | the paper | page/table refs written in the worksheet | `docs/literature/*_worksheet.csv` | `python -m iris.tools.source_verification apply-sources ...`, `apply-params ...`, `python -m iris.tools.sync_population_status` | `docs/literature/S1_hossmann_evidence.md` |
| 6 | Verify the other 29 sources; extract L2, L5; run and log L1 search | publisher pages | papers | worksheet rows, CSV rows with page refs | `docs/literature/`, `literature/*.csv` | `apply-sources`, then production `L2`,`L5`,`L1` | `docs/literature/01_source_verification_runbook.md` |
| 7 | Download HUPA-UCM, BrisT1D-Open; screenshot licence page | Mendeley Data; Bristol repository | open files | screenshot + licence quote + version | `data/raw/hupa_ucm/`, `data/raw/brist1d/` | `register_raw`, `apply-sources`, `audit_data`, `inspect_grid` | `docs/data/04_ingestion_and_mapping.md` |
| 8 | Fill and mark the mappings AUDITED | editor | `configs/mappings/*.yaml` | notes with paper pages | `docs/data/evidence/<id>/notes.md` | `ingest_dataset <id> --mode production`, `validate_person_day` | `docs/runbook/05_production_runbook.md` |
| 9 | Freeze the pre-registration; tag | editor + Git | `docs/prereg/conclusions.yaml` | decision note | repo, tag `prereg-v1` | `git tag prereg-v1; git push --tags` | `docs/prereg/freeze_procedure.md` |
| 10 | Run production runbook; complete the validation checklist | terminal | commands in the runbook | `results/status_production.md` | `results/runs/` (production only) | `python scripts/verify_run_dir.py results/runs/<id>` | `docs/validation/scientific_validation_checklist.md` |
| 11 | (Optional) Kaggle repeat run | kaggle.com | open datasets only | notebook version, outputs zip | `results/runs/` | `python scripts/verify_run_dir.py ...` | `docs/ml/kaggle_and_ml_guide.md` |
| 12 | (Optional, Phase 1b) climate data after the location rule is frozen | CDS, NASA, IMD, ASHRAE | records | request JSON, licences | `data/raw/climate/` | ask for the E1/E2 production reader | `docs/data/07_climate_and_context.md` |
| 13 | Release: tag, GitHub release, Pages, optional Zenodo DOI | github.com | repo | release URL | GitHub | see checklist | `docs/release/release_checklist.md` |

Everything else (readiness matrix, worksheets with prepared evidence, templates, notebook, runbooks, CI, site builder, tools) is already in the repository.
