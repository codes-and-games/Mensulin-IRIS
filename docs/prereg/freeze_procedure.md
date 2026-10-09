# Pre-registration and conclusions freeze

**What is frozen:** `docs/prereg/conclusions.yaml` (the list of confirmatory conclusions with their margins and thresholds, C1, C2 ...), plus `configs/fusion/admissible_set.yaml`, `configs/fusion/scenarios.yaml`, `configs/population/population_default.yaml` as they stand, plus (for the climate branch) the location rule, window rule and agreement thresholds.
**When:** after S1 verification and L2 extraction (so the anchors and kinetic families are known), and **before any production run of F1-F6, R1-R3 or E1**. The repository's own gate (`F5` refuses an unfrozen file) enforces the last part for F5 only; the rest depends on you following this order.

## Procedure
1. Open `docs/prereg/conclusions.yaml`. It currently holds two conclusions, each with `metric`, `threshold_units`, `comparator`, `value` and `frozen: false`:
   - **C1_heterogeneity_penalty:** `hp` at `threshold_units: 2.0` is `> 1.0`. The value 1.0 is the null boundary (no heterogeneity penalty), so it is not a tuned number.
   - **C2_excess_concentration:** `excess_tci` at `threshold_units: 2.0` is `> 0.0`; zero is the value predicted under independence (null boundary), so again not tuned.
   The file itself calls `threshold_units: 2.0` a placeholder from the threshold grid. **This is the one number the owner must justify** in writing (what a shortfall of 2 insulin units means clinically for the chosen reference dose; cite where the grid comes from in the project document). Without that justification, state in the freeze note that 2.0 is a convention and report the whole threshold grid as the primary result.
2. Record the reasoning in a numbered note under `docs/decisions/`. Decide this **without having seen production fusion results**; test-mode output is synthetic and must not influence the choice.
3. For each conclusion set `frozen: true` and add `frozen_on: <YYYY-MM-DD>`.
4. Commit and tag: `git add docs/prereg configs && git commit -m "Freeze pre-registration" && git tag prereg-v1 && git push --tags`.
5. After the tag: any change creates `prereg-v2` with a written amendment (what changed, why, whether results had been seen). Conclusions whose criteria changed after seeing results are labelled **exploratory** in every report.

## Confirmatory vs exploratory
- **Confirmatory:** conclusions in the frozen file, evaluated by F5 against the frozen thresholds on production runs.
- **Exploratory:** everything else (F6 axes not listed, M6, subgroup views, any threshold changed after freezing). Reported as exploratory, never as confirmation.
- **Verification only (no evidence):** E3, S1, S2, M4. Reported under "code verification".

## Never
Change a threshold, a hypothesis, or the admissible set after seeing production results to obtain a stronger statement. If a result is disappointing it is reported as it is.
