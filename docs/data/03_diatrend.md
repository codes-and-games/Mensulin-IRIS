# 03 DiaTrend (registry S16, dataset id `diatrend`): Phase 2, controlled access

**Purpose:** long series for L4 (clinician ISF vs TDD) and M5 (spectral negative control: is a 21-35 day periodicity detectable in unlabelled TDD, females vs males, at least 150 pump days). **No cycle labels** (sex is recorded).
**Facts verified from the data descriptor (Scientific Data 2023;10:556):** 54 people with type 1 diabetes; 27,561 days of CGM and 8,220 days of pump data; CGM about every 5 minutes (Dexcom, Abbott, Medtronic); pump basal, bolus, carbohydrate logs and settings (insulin-carbohydrate ratio etc.); 54 Excel files, one per subject; baseline data only; **controlled access via Synapse** (access DOI 10.7303/syn38187184). Participants consented to open sharing, but access is controlled to limit re-identification.
**Caution:** only 8,220 pump days exist across 54 people, so TDD is available for far fewer person-days than CGM; M5's group sizes depend on the audit.

## Request (do this on day 1)
1. Create a free Synapse account at synapse.org and complete the profile.
2. Open `https://doi.org/10.7303/syn38187184`, choose **Request access** and follow every access-requirement prompt shown (these may include accepting terms of use and approval by the data custodian). Use `templates/synapse_access_request_notes.md` for the intended-use statement.
3. Record in the resource manifest: date requested, request/reference number, approver, date approved.
## After approval
4. Download the 54 `.xlsx` files into `data/raw/diatrend/` (this folder is git-ignored; **never** upload, commit or share them).
5. `python -m pip install openpyxl`, then the common procedure with **D = diatrend, S = S16** (guide 00).
6. The existing loader module `src/iris/ingest/loaders/diatrend.py` and the mapping workflow in `04_ingestion_and_mapping.md` apply; map `isf_clinician` only if the audit shows a pump-setting ISF column.
**If denied or delayed:** L4 uses published ISF/TDD reports (document fallback) and M5 stays `READY AFTER DATA ACQUISITION`; nothing in Phase 1 changes.
**Next:** `04_ingestion_and_mapping.md`.
