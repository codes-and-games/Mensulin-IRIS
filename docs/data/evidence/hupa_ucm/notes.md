# HUPA-UCM mapping audit

Source: Hidalgo et al., *HUPA-UCM diabetes dataset*, Data in Brief 55 (2024), 110559.
Paper: https://doi.org/10.1016/j.dib.2024.110559
Dataset: https://doi.org/10.17632/3hbcscwz44.1

- `time`: source timestamp column; native preprocessed grid inspected at 5 minutes.
- `glucose`: mg/dL, as specified in the dataset paper.
- `basal_rate`: insulin amount per 5-minute interval, not a rate per hour; mapped as `u_per_step`.
- `bolus_volume_delivered`: bolus insulin delivered per interval; mapped as `u`.
- `carb_input`: servings; the paper defines 1 serving as 10 g. The ingest pipeline converts servings to grams.
- Participant ID: each preprocessed CSV is one participant; use its filename stem.
- Timezone caveat: the source describes timestamps without an explicit timezone. `Europe/Madrid` is an operational assumption based on the Spanish study site, not a timezone explicitly stated in the paper. Circadian results must be treated as provisional until timestamp semantics are verified.
- Scope: this dataset has no menstrual-cycle labels and cannot support a cycle-linked claim.

The source licence and version must still be confirmed in the source-verification worksheet before production ingestion.

## Unresolved carbohydrate-unit discrepancy

Carbohydrate mapping is intentionally disabled for initial ingestion.
The paper describes `carb_input` in 10 g servings, but preprocessed files
contain participant records with values such as 90?130. These may reflect
inconsistent units or preprocessing; this has not been established.
No raw values were changed and no threshold-based conversion was applied.
Carbohydrate analyses remain blocked pending source-level clarification.
