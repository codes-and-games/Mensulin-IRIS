# 01 Source and literature verification runbook

**Objective:** turn each `PENDING_VERIFY`/unverified source and parameter into a signed, located, dated record. **No source, no number.**
**Principle:** the tool never fills evidence, dates, licences or sign-offs; it copies only complete, consistent rows you entered and appends an audit line to `docs/literature/verification_log.csv`. Everything under `prepared_*` is a reviewer aid collected from search-engine renderings, **not** a verification; the preparer could not open PMC or doi.org directly and recorded no page numbers.

## Two worksheets (already generated, with prepared evidence)
- `docs/literature/source_verification_worksheet.csv`: 30 rows, one per registry source.
- `docs/literature/parameter_verification_worksheet.csv`: 16 rows, one per biological anchor (S1).
Regenerate blank ones any time: `python -m iris.tools.source_verification sources-worksheet` / `params-worksheet` (overwrites; copy yours first). Edit in a spreadsheet and **save as CSV (UTF-8)**.

## A. Source rows (columns you fill)
`doi_or_url_confirmed` (open the DOI yourself), `version`, `access_date` (`YYYY-MM-DD`, the day you opened it), `licence_or_access` (quote the page, or "journal copyright; cited only" for papers), `claim_location` (page + table/figure/section for each value IRIS takes from it), `evidence_note`, `evidence_type` (`direct` = value stated; `derived` = computed from stated values; `assumption`), `ambiguity_note`, `dataset_sha256` (datasets only: from `register_raw`), `status` = `VERIFIED`, `verified_by`, `verified_on`.
```powershell
python -m iris.tools.source_verification apply-sources docs/literature/source_verification_worksheet.csv
python -m iris.tools.verify_registry --lenient
```
Output `applied N row(s)` plus `NOT APPLIED:` lines for incomplete rows. Re-run as you progress; applying is idempotent.

## B. Parameter rows (S1 anchors)
For `PENDING_VERIFY` rows: open the paper, find the value, fill `value_in_paper`, `page_table_ref` (e.g. "Table 2, row TDD, p. 1675"), `matches` = `yes`/`no`, `verified_by`, `verified_on`. For `UNRESOLVED` rows: fill `value_in_paper`, `page_table_ref`, and put the extractor's name in `verified_by` (this makes it `PENDING_VERIFY`); a **second person** then verifies it in a second pass. One reader only: add `--allow-single-reader` (recorded in the log as a limitation).
```powershell
python -m iris.tools.source_verification apply-params docs/literature/parameter_verification_worksheet.csv
python -m iris.tools.sync_population_status --dry-run      # shows what would change
python -m iris.tools.sync_population_status
```
`apply-params` records the sign-off in `literature/biological_evidence.csv`. The production gate, however, reads each parameter's `status` in `configs/population/population_default.yaml`; ordinary `sync_population_status` sets `status: RESOLVED` there only for rows that are RESOLVED in the CSV and whose value equals the config value. It reports a mismatch and changes nothing by default.

If a fully verified source correction intentionally changes an existing config value, add a numbered decision note with an explicit machine-checkable section listing the exact parameter names and verified numeric values, for example:
```markdown
## Approved sync values
- luteal_length_mean_d: 12.5
- luteal_length_sd_d: 1.2
```
Preview the explicit update (do not edit YAML by hand):
```powershell
python -m iris.tools.sync_population_status --dry-run --approve-mismatch luteal_length --decision-note docs/decisions/0005-s1-luteal-length-source-mismatch.md
```
The command verifies that the evidence rows are already `RESOLVED` and that the decision note lists the exact values recorded in those rows. Only after the dry run shows the intended update should you repeat the command without `--dry-run`. Do not use this override for undocumented or unverified differences.
**Start with S1** (`docs/literature/S1_hossmann_evidence.md`): `tdd_mean_u` and `tdd_sd_u` unblock S3, F2 and everything downstream.

## When the paper disagrees with IRIS
`matches = no` produces `MISMATCH_REPORTED` and **changes nothing**. Then: (1) decide with the paper in hand which quantity IRIS needs (population-level posterior vs a subgroup mean, etc.) and write the reasoning in `docs/decisions/` as a numbered note; (2) in `literature/biological_evidence.csv` clear that row's `value`, `ci_low`, `ci_high`, `page_table_ref`, `extracted_by`, `verified_by` and set `status` to `UNRESOLVED`; (3) re-extract via the worksheet (`value_in_paper`, `page_table_ref`, your name in `verified_by`); (4) second-reader verify. Also update `configs/population/population_default.yaml` only through this chain, never first. This procedure applies when the worksheet extraction disagrees with its cited paper. If the evidence has already been corrected and second-reader verified but the YAML retains the old value, use the approved synchronization path above; do not erase verified evidence merely to make the configuration match.

## C. Literature tables (inputs of L1, L2, L5)
Each needs primary-source extraction with a page/table reference and a second reader. **Never copy numbers from abstracts of secondary summaries.**
| Table | Columns | Sources | Rule |
|---|---|---|---|
| `literature/degradation_literature.csv` (L2) | `study_id, source_id, product, formulation, container, temp_c, time_days, potency, sd, assay, extracted_by, verified_by, page_table_ref` | S7-S14 | one row per (temperature, time) potency observation; potency as a fraction of label or initial; if only a figure is available, digitise it and say so in `page_table_ref`; note S8 disagrees with S7/S11 and keep both |
| `literature/thermal_context_parameters.csv` (L5) | `parameter, context_id, value, unit, source_id, citation, page_table_ref, conditions, extracted_by, verified_by` | S31, S32, S35 | context parameters (indoor/outdoor offsets, swing damping, heat-transfer constants) |
| `literature/novelty_search_log.csv` (L1) | `date, database, query, n_results, screened, closest_prior_study, closeness, notes, searched_by` | search | log every query, even empty ones; closest prior studies recorded with their DOI |
`verified_by` must differ from `extracted_by` unless you accept a documented single-reader limitation. After filling run the experiment (`python -m iris.tools.run_experiment L2_degradation --mode production`); the experiment itself refuses unverified rows.

## D. Order of work
S1 -> S2-S5 (clinical context, no model input except S1) -> S7-S14 (L2) -> S31, S32, S34, S35 (L5; S34 Parton-Logan form/parameters stay fail-closed until verified) -> S12 (S8 benchmark scenario) -> S33, S36 -> datasets as acquired (S15-S19) -> climate S27-S30 only if Phase 1b -> S38 context.
**Next:** `docs/START_HERE.md` step 4.
