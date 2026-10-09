# 01 HUPA-UCM (registry S15, dataset id `hupa_ucm`)

**Purpose:** pipeline test and 24-hour pattern check (M6, M4, M1 naive). **Not** for any biological or cycle claim. **Phase 1.**
**What it is (project document; confirm on the page):** about 25 people with type 1 diabetes, at least 14 days each, FreeStyle Libre 2 glucose, insulin bolus and basal, carbohydrates in grams; no cycle labels. Data paper: Data in Brief, doi:10.1016/j.dib.2024.110559. Repository: Mendeley Data, doi:10.17632/3hbcscwz44.1 (version 1 per registry).
**Variables needed:** timestamp, glucose, basal and/or bolus insulin, carbohydrate. Heart-rate / activity columns are not used by IRIS.
**Quality concerns to check in the audit:** short series per person (about two weeks), possible gaps, native CGM spacing (Libre 2 measures every 15 minutes: confirm whether the files are resampled), units of basal (rate per hour or amount per step), time zone.

## Steps
1. Open `https://doi.org/10.17632/3hbcscwz44.1` (Mendeley Data). The dataset is described as openly downloadable. If a login is requested a free account is enough; do not use any "request access" route (none is expected).
2. On the page record: dataset **version number**, **licence line** (a third-party listing reports CC BY 4.0: **read it yourself on the page and quote it**), publication date, and the download link. Take the screenshot (common procedure step 2).
3. Download all files (use "Download all"). Place them in `data/raw/hupa_ucm/`, original names, unzipped.
4. Run the common procedure steps 3-6 with **D = hupa_ucm, S = S15**:
   ```powershell
   python -m iris.tools.register_raw hupa_ucm S15
   python -m iris.tools.source_verification apply-sources docs/literature/source_verification_worksheet.csv
   python -m iris.tools.audit_data data/raw/hupa_ucm data/dictionaries/audit_hupa_ucm.json
   python -m iris.tools.inspect_grid data/raw/hupa_ucm <timestamp column from the audit> --glob "*.csv"
   ```
5. Read the **Data in Brief paper's data-description table** for: time zone of the timestamps, unit of glucose, whether basal is a rate (U/h) or an amount, whether bolus is units per record, whether files are one per person.
6. Continue with `04_ingestion_and_mapping.md` (dataset `hupa_ucm`).

**Expected:** `register_raw` prints `registered N new file(s)` and a 64-hex digest; `audit_data` prints `audited N tabular files`. If `N` or the file layout differs from the paper, note it and continue with the audit as the source of truth.
**Limitations to state in any write-up:** about 25 people, about two weeks each, no cycle labels, single-centre.
**Next:** `02_bristol_brist1d.md`, then `04_ingestion_and_mapping.md`.
