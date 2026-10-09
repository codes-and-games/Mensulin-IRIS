# 05 T1DEXI (registry S19, dataset id `t1dexi`): Phase 2, access by request

**Purpose:** the only candidate for cycle-labelled analysis (M2, M3, cycle baselines in M1). Whether it holds usable menstrual-cycle variables, and how they are coded, is **[VERIFY]** and must be read in the Vivli data dictionary before any request is justified on that basis. **No cycle-skill claim is possible without such labels, and none will be inferred.**
**How access works (from Vivli's published process):** request through Vivli -> administrative check -> feasibility review by the data contributor -> Independent Review Panel -> a data use agreement **signed per team member** (institution signatory where required) -> analysis inside Vivli's secure research environment. Timelines are measured in months. **Assume the data cannot be downloaded or sent to GitHub/Kaggle until your signed DUA says otherwise.**

## Request steps
1. Create a Vivli account and find the T1DEXI study page(s); record the study identifier(s) and read the data dictionary variables list (look for menstrual-cycle, cycle day/phase, period start).
2. Confirm who can sign for you (a student usually needs the supervisor/institution). This cannot be prepared for you.
3. Submit the request using `templates/vivli_request_template.md` (research question, analysis plan, variables, statement that no re-identification will be attempted, no redistribution).
4. Record: request id, dates, approver, DUA signature dates (keep the DUA itself private).
## After approval
5. Work inside the Vivli environment. Prepare it with the **portable bundle**: the repository at a tagged release (`git archive` or the release zip) plus `requirements-lock.txt`; confirm with Vivli what packages can be installed. Copy only the outputs Vivli permits out (aggregate results), never row-level data.
6. Run the common procedure steps 5-7 there (audit, mapping, ingest with `dataset: t1dexi`). Cycle columns map to `cycle_day`/`cycle_len` **only if the dictionary defines them**.
**If access is denied or the data have no cycle variables:** M2/M3 remain `NOT YET JUSTIFIED`; the project concludes without a cycle-skill claim and says why.
**Next:** `04_ingestion_and_mapping.md`.
