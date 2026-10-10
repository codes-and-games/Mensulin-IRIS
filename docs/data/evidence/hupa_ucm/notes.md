# HUPA-UCM mapping audit

Dataset source: https://data.mendeley.com/datasets/3hbcscwz44/1
DOI: 10.17632/3hbcscwz44.1
Official dataset record: Version 1, published 25 April 2024; dataset page lists CC BY 4.0.

- `time`: source timestamp column; the inspected preprocessed grid is 5 minutes.
- `glucose`: mg/dL.
- `basal_rate`: currently mapped as insulin amount per 5-minute step; confirm this interpretation against the paper before production.
- `bolus_volume_delivered`: insulin amount per record.
- `carb_input`: carbohydrate intake in grams, according to the official Mendeley dataset description. No serving conversion is applied.
- Participant ID: preprocessed CSV filename stem.
- Timezone: `Europe/Madrid` is an operational assumption, not explicitly verified from the source timestamp specification.
- No menstrual-cycle labels are supplied.

Correction note: an earlier draft treated `carb_input` as 10-gram servings. The official dataset description states grams; this mapping now uses grams directly. Raw files remain unchanged.

Use remains provisional until source metadata, timestamp semantics, and insulin field definitions are verified.
