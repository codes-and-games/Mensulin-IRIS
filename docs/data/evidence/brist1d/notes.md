# BrisT1D mapping notes

Source: BrisT1D-Open README.txt and LICENCE.txt in the registered download.
Licence text identifies Creative Commons Attribution 4.0 International.

- `timestamp`: source timestamp column; mixed-frequency event rows are aggregated to a 5-minute grid.
- `bg`: blood glucose in mmol/L; converted by IRIS to mg/dL.
- `insulin`: total insulin dose received in the previous five minutes; mapped as u_per_step.
- `carbs`: carbohydrate intake in grams.
- Participant ID: processed CSV filename stem.
- Timezone: Europe/London is an operational assumption based on the UK study location; source files do not establish timezone semantics here.
- Timestamp alignment/end-of-interval behavior needs further verification.
- Only the 20 processed-state participant CSVs audited here are ingested. No menstrual-cycle labels are supplied.

This ingest is provisional. Verify source metadata, timezone, timestamp alignment, and licence/version in the source worksheet before production use.
