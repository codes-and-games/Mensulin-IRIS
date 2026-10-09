# 02 BrisT1D-Open (registry S17, dataset id `brist1d`)

**Purpose:** second Phase 1 dataset with smartwatch covariates (M6, M4, M1 naive). **No cycle labels, no biological claim.**
**What it is (registry and project document; confirm on the page):** University of Bristol, young adults with T1D in the UK using smartwatches; data paper arXiv 2507.17757; stored in the Bristol data repository in two parts (BrisT1D-Open and BrisT1D-Restricted). Open part reported under CC BY 4.0 (about 19 usable participants **[VERIFY]**); insulin recorded as units per 5 minutes.
**Use only the open part, from the Bristol repository.** The Restricted part needs approval and is out of scope. A Kaggle competition built on this data uses a different (lagged, wide) file layout; **do not mix it with the repository files** unless the verified source record states they are the same version.

## Steps
1. Find the dataset through the paper (arXiv 2507.17757) and the Bristol data repository record it cites. Record: repository URL/DOI, version, the **licence line verbatim**, which files make up the Open part.
2. Download only the Open files into `data/raw/brist1d/`, original names.
3. Common procedure steps 3-6 with **D = brist1d, S = S17**:
   ```powershell
   python -m iris.tools.register_raw brist1d S17
   python -m iris.tools.source_verification apply-sources docs/literature/source_verification_worksheet.csv
   python -m iris.tools.audit_data data/raw/brist1d data/dictionaries/audit_brist1d.json
   python -m iris.tools.inspect_grid data/raw/brist1d <timestamp column from the audit> --glob "*.csv"
   ```
4. From the paper's data description note: one file per person or a combined file with a person column; glucose unit; insulin column semantics (total insulin per 5-min step: map as `insulin_total` with unit `u_per_step`; do not map basal and bolus as well); time zone.
5. Continue with `04_ingestion_and_mapping.md` (dataset `brist1d`).

**Limitations:** small number of usable participants, young adults only, smartwatch-derived covariates not used by IRIS.
**Next:** `04_ingestion_and_mapping.md`.
