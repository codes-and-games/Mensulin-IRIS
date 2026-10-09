# 06 OhioT1DM (registry S18, dataset id `ohiot1dm`): Phase 2, optional

**Purpose:** small (12 people, about 8 weeks each) method check. Not needed for any Phase 1 or Phase 2 claim. **The registry marks the citation `[NOT VERIFIED]`.**
**Access:** a data use agreement with the dataset custodians (Ohio University). Locate the **official** dataset page yourself (search the dataset name and the Marling and Bunescu 2020 paper), confirm the request procedure there, and use `templates/ohiot1dm_request_email.md`. Do not use any mirror.
**Steps:** request -> sign DUA -> download into `data/raw/ohiot1dm/` (git-ignored) -> common procedure with **D = ohiot1dm, S = S18** -> `04_ingestion_and_mapping.md`. The data are XML in their original release; the audit/mapping pipeline reads tabular files, so the first step after approval is a documented XML-to-CSV conversion kept in `scripts/` (not a guess: write it against the real files). **Next:** `04_ingestion_and_mapping.md`.
