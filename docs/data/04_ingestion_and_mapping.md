# 04 Ingestion and mapping

**Objective:** turn registered raw files into validated `person_day` and `events_grid` tables that experiments may read, without guessing a single column.
**Prerequisites:** the dataset guide (01/02/03/05/06) done through "audit" and "time grid"; the source row verified (`verify_registry --lenient` shows no problem for it).
**What exists:** `iris.tools.make_mapping_template` (proposes candidates from the audit, never decides), `iris.tools.ingest_dataset` (applies the mapping), `iris.tools.validate_person_day` (quality report), `iris.tools.inspect_grid` (native sampling interval).

## 1. Generate the draft mapping (example for HUPA-UCM; change `hupa_ucm`/`S15` for another dataset)
```powershell
python -m iris.tools.make_mapping_template hupa_ucm S15 --audit data/dictionaries/audit_hupa_ucm.json --raw-dir data/raw/hupa_ucm
```
This writes `configs/mappings/hupa_ucm.yaml` with `audit_status: DRAFT`, an empty `columns: {}` and `units: {}`, and a `candidates:` block listing columns that look like each role, with their ranges. Candidates are hints only.

## 2. Fill it (these are reading tasks, not methodological choices)

| Field | How to decide | If you cannot decide |
|---|---|---|
| `columns.timestamp` | The date-time column (a candidate marked `timestamp_like: true`) | stop; ask the dataset authors |
| `columns.glucose`, `units.glucose` | Glucose column; unit `mg/dl` or `mmol/l` from the data paper. Values around 70-250 mean mg/dL; around 4-14 mean mmol/L (use this only to cross-check the paper) | stop |
| `columns.basal`, `units.basal` | `u_per_h` if the column is a rate that stays constant for long stretches (typically 0.3-2.5); `u_per_step` if it is an amount per record (mostly 0, small values). **Take the paper's definition**; the value pattern only cross-checks it | stop |
| `columns.bolus`, `units.bolus` | `u` (units delivered per record) | stop |
| `columns.insulin_total`, `units.insulin_total` | Use **instead of** basal+bolus when the file has one combined insulin column; unit `u_per_step` | stop |
| `columns.carb`, `units.carb` | grams; must be `g` | stop |
| `columns.isf_clinician` | only if a pump-setting ISF column exists | leave out |
| `columns.cycle_day`, `columns.cycle_len` | **only** columns the dataset itself provides. Never derive. | leave out |
| `person_id` | `from: filename` if one file per person (the file stem is the id), `from: column` + `column: <name>` for a combined file | stop |
| `tz` | The time zone stated in the data paper (an IANA name such as `Europe/Madrid`). If the paper says timestamps are local clock time with no zone, use the participants' region and note it | stop |
| `grid_minutes` | The native spacing from `inspect_grid`; must divide 1440. Do not up-sample | stop |
| `min_cgm_coverage`, `min_insulin_coverage`, `min_days_per_person` | Defaults (0.7, 0.9, 7) are the project's pre-set inclusion rules; leave them | do not tune after seeing results |
| `basal_ffill_minutes` | 0 unless the paper says basal rate changes are logged only at change points; then the paper's maximum hold time | 0 |

Then delete the `REVIEW_REQUIRED` and `candidates` keys, set `audit_file: data/dictionaries/audit_<dataset>.json` and `audit_status: AUDITED`. Record every non-obvious reading in `docs/data/evidence/<dataset>/notes.md` with the paper page or table that supports it.

**Experiment grid rule:** `experiments/M6_circadian_recovery/config.yaml` has `grid_minutes: 5`. If a dataset's native grid differs, M6 now stops with a clear message (a grid-consistency guard) instead of silently mis-scaling. Set M6's `grid_minutes` to the ingested value and record it in `docs/decisions/DECISION_LOG.md` (a data-format setting, not a scientific parameter).

## 3. Ingest, first provisional, then production
```powershell
python -m iris.tools.ingest_dataset hupa_ucm --mode provisional
python -m iris.tools.validate_person_day data/processed/hupa_ucm/person_day.parquet --out data/processed/hupa_ucm/qc_report.json
python -m iris.tools.ingest_dataset hupa_ucm --mode production
```
Provisional output is stamped and can only feed provisional runs. Production ingest requires the source verified, every raw file registered in `data/manifest.csv`, and an AUDITED mapping, and refuses otherwise.
When all Phase 1 datasets are ingested in production mode build the combined table (used by M1, M4, L4):
```powershell
python -m iris.tools.ingest_dataset brist1d --mode production --combine
```

## 4. Built-in policies (what the pipeline does with messy data; all logged in `ingest_report.json`)
- **Timestamps:** parsed as local clock time and localised with `tz`; ambiguous/nonexistent daylight-saving times are dropped and counted, never shifted.
- **Duplicates:** several records falling in the same grid bin are aggregated (counted in the log), not double counted; duplicate (person, date) rows are a hard validation failure.
- **Glucose:** converted to mg/dL; values outside the sensor-plausibility window (20-600 mg/dL) are flagged, not deleted.
- **Missing values:** days with CGM coverage below `min_cgm_coverage` or insulin coverage below `min_insulin_coverage` are excluded with a reason (`exclude_reason`); TDD is NaN when insulin is incomplete: it is never imputed.
- **Outliers:** flagged, never removed; the validator warns on TDD > 300 U or mean glucose outside 40-400 mg/dL (usually a unit error).
- **Participant IDs:** kept as given within a dataset; in the combined table they are prefixed `dataset:` so ids cannot collide across datasets. Raw files never leave `data/raw/`; derived tables carry only these ids.
- **Cycle columns:** stay empty unless the dataset supplies them.

## 5. Validate
`validate_person_day` exits 0 and prints counts. **Hard failures** (exit 1): schema mismatch, duplicate person-days, no TDD on any included day. **Warnings** to read: fewer than 10 persons (only method checks are meaningful: expected for HUPA/BrisT1D), TDD > 300 U, glucose range.
Expected for the Phase 1 datasets: `has_cycle_labels: false`, about 20-45 persons in total, short days-per-person.

## 6. When it fails
`docs/runbook/06_troubleshooting.md`. When the audit shows a layout the pipeline cannot express (for example several sheets or an event-style table per person, which is likely for DiaTrend's Excel workbooks), the mapping stays `DRAFT` and the case is a **code limitation to fix after seeing the real audit**, not a reason to guess.
**Next:** `docs/runbook/05_production_runbook.md` rows 15-17 (M4, M1, M6).
