# 01 Master execution plan

Dependency order from the repository's current state to the final scientifically defensible result. Each stage lists what it needs and what it must leave behind. Stages marked **parallel** may run at the same time as others.

```
S1 verified ─► tdd RESOLVED ─► S3 population ┐
S7–S14 extracted+verified ─► L2 ─► E4 potency ┼─► F1 F2 F3 F4 F6 ─► (prereg frozen) ─► F5 ─► R1 R2 R3
S27–S31 registered+verified ─► E1 ─► E2 ─────┘
HUPA-UCM + BrisT1D ─► ingest ─► M4, M1, M6            DiaTrend ─► L4, M5        T1DEXI ─► M2, M3  (Phase 2)
```

| # | Stage | Objective | Prerequisites | Files / commands | Inputs → outputs | Success | Failure | Next |
|---|---|---|---|---|---|---|---|---|
| 0 | Environment | Prove code works | Python, Git | `02_environment_setup.md` | repo → green tests | all tests pass | import error | 1 |
| 1 | Access requests (parallel) | Start long lead times | institution, accounts | `docs/data/03,05,06` + `templates/` | forms → pending requests, recorded in the resource manifest | request IDs recorded | rejected → Phase 1 unaffected | 2 |
| 2 | Verify S1 | Unblock S3, L3, F2 | Hossmann paper open | `docs/literature/S1_hossmann_evidence.md`; `source_verification apply-sources` / `apply-params`, then `python -m iris.tools.sync_population_status` | worksheets → registry + `biological_evidence.csv` rows RESOLVED, `verification_log.csv` | `verify_registry --lenient` shows S1 complete; `L3` completes in production | mismatch rows listed as NOT APPLIED | 3 |
| 3 | Verify other sources (parallel) | Complete registry | primary sources | `01_source_verification_runbook.md` | worksheets → registry | 0 warnings for needed sources | see runbook | 4 |
| 4 | Literature tables (parallel) | L2, L5, L1 inputs | verified S7–S14, S31, S32, S35 | CSVs in `literature/`; run `L2`, `L5`, `L1` | extraction rows → verified rows | `L2`,`L5`,`L1` completed (production) | blockers cite empty tables | 8 |
| 5 | Phase-1 datasets (parallel) | Real person-level data | HUPA, BrisT1D downloaded | `docs/data/00,01,02,04` | files → `data/processed/<id>/` + combined `person_day.parquet` | `validate_person_day` exit 0; `register_raw` manifest entries | schema/mapping errors → troubleshooting | 8 |
| 6 | Climate data (parallel) | E1/E2 inputs | CDS account etc. | `docs/data/07_climate_and_context.md` | records → registered, verified S27–S31 | `E1` completed (production) | unresolved address/version/licence | 8 |
| 7 | **Freeze pre-registration** | Fix confirmatory criteria | none; must precede any production F1–F6 results | `docs/prereg/freeze_procedure.md` | `conclusions.yaml` → frozen + git tag | tag `prereg-v1` exists before first production fusion run | frozen after results seen → exploratory only | 8 |
| 8 | Production runs | Produce results | stages 2–7 as applicable | `05_production_runbook.md` (`python -m iris.tools.run_all --mode production`) | inputs → `results/runs/<id>/` | per-experiment criteria | BLOCKED messages | 9 |
| 9 | Validation | Decide what is supported | runs complete | `docs/validation/scientific_validation_checklist.md` | runs → validation record | every box answered | unsupported claims listed | 10 |
| 10 | Assembly + release | Reproducible package | validation record | `07_final_result_assembly.md`, `docs/release/*` | runs → figures, tables, data book, release | checklist complete | see checklist | done |

**What the final claim is allowed to be** is decided by stage 9, never earlier. If stage 5 or 6 cannot be completed, the affected experiments stay BLOCKED and the write-up says so.
