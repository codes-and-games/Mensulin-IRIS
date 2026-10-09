# 00 Dataset acquisition: master guide

## What each dataset is for (decided from the project document, not from size)

| Dataset | Registry id / folder id | Phase | Experiments it can support | Cycle labels? | Access | Use in production research |
|---|---|---|---|---|---|---|
| HUPA-UCM | S15 / `hupa_ucm` | 1 | M6, M4, M1 (naive), pipeline checks | No | Open (Mendeley Data) | Yes, for method plausibility and leakage tests only; ~25 people, >=14 days each: **no biological claim** |
| BrisT1D-Open | S17 / `brist1d` | 1 | M6, M4, M1 (naive) | No | Open part (Bristol repository) | Same as above |
| DiaTrend | S16 / `diatrend` | 2 | L4, M5 (spectral negative control) | No (sex recorded) | Controlled (Synapse) | Yes, once approved; long series (CGM and pump days) |
| T1DEXI | S19 / `t1dexi` | 2 | M2, M3, M1 (cycle baselines) if cycle variables exist | Reported to exist; **[VERIFY]** | Vivli request + DUA | Only the dataset that can support a cycle-skill claim; analysis inside Vivli's environment |
| OhioT1DM | S18 / `ohiot1dm` | 2 | method checks | No | Data use agreement | Small (12 people); optional |

Phase 1 needs only the first two rows. **A dataset without cycle labels can never support a cycle-skill claim**, and no label is inferred for it. If T1DEXI turns out to have no usable cycle variables, M2/M3 stay `NOT YET JUSTIFIED` and the write-up says so.

## Order

1. Today: submit the three Phase 2 requests (`03_diatrend.md`, `05_t1dexi.md`, `06_ohiot1dm.md`). Waiting time is the only cost.
2. Download HUPA-UCM (`01`) and BrisT1D-Open (`02`).
3. Apply the common procedure below to each; then `04_ingestion_and_mapping.md`.

## Common procedure (dataset id **D**, registry id **S**; the dataset guides give the exact values)

1. **Download** the files into `data/raw/D/` and keep the original file names. Unzip archives there. Do not edit, re-save in Excel, or re-encode any file.
2. **Evidence:** take a screenshot of the page showing title, version/DOI, licence and date, and the download link. Save it as `docs/data/evidence/D/<yyyy-mm-dd>_landing.png` (open datasets only; for controlled datasets keep it privately, outside Git).
3. **Register and hash:** `python -m iris.tools.register_raw D S`. It lists every file in `data/manifest.csv`, makes the files read-only, and prints a **dataset digest**. Copy the digest.
4. **Verify the source row:** in `docs/literature/source_verification_worksheet.csv` fill the row for S: `doi_or_url_confirmed`, `version` (as printed on the page), `access_date` (today, `YYYY-MM-DD`), `licence_or_access` (quote the licence line verbatim), `dataset_sha256` (the digest), `status` = `VERIFIED`, `verified_by` (your name). Then:
   `python -m iris.tools.source_verification apply-sources docs/literature/source_verification_worksheet.csv`
   Output must say `applied 1 row(s)`; any `NOT APPLIED:` line names what is missing.
5. **Audit:** `python -m iris.tools.audit_data data/raw/D data/dictionaries/audit_D.json`. It lists every tabular file, column, type, range and missingness. It changes nothing.
6. **Time grid:** `python -m iris.tools.inspect_grid data/raw/D <timestamp column> --glob "*.csv"` (the column name is in the audit). Note the native spacing.
7. **Mapping and ingest:** follow `04_ingestion_and_mapping.md`.
8. **Next guide:** the one named at the end of each dataset guide.

Check at any time: `python -m iris.tools.verify_registry --lenient` (reports problems, never fails) and without a flag (strict, the default: exits non-zero unless everything used is verified).

## If the structure differs from the guide

Trust the audit, not the guide. Record the difference in `docs/data/evidence/D/notes.md`, keep the mapping `DRAFT`, and stop at any role you cannot tie to a data dictionary or the dataset paper. Ambiguity is resolved by reading the paper, never by guessing from a column name.
