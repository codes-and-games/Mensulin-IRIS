# S1: Hossmann et al.: evidence record for the sign-off

**Not a verification.** Prepared on 2026-10-07 from search-engine renderings of the publisher/PMC text. The PMC page and doi.org refused automated access, so **no page, table or figure number below was confirmed by the preparer**. Your job is to open the paper and either confirm or correct each line.

**Paper:** Hossmann S, et al. (first author Stefanie Hossmann, Diabetes Center Berne). *Diabetes Care* 2026 Jul 22 (online); 49(9):1673-1680. DOI 10.2337/dc26-0692. Open access: PMC13493352 (PubMed 42482329). 77 participants, 380 cycles, AID users, self-tracked cycles, hierarchical Bayesian state-space model of insulin sensitivity.
**Licence/access:** open access article; record the licence printed on the page (it is a journal article: cite only).

## What the captured text says (for IRIS's `literature/biological_evidence.csv` rows)
| IRIS parameter | IRIS value | Captured evidence | Status of evidence |
|---|---|---|---|
| `tdd_mean_u` | 37.3 U | Results text: dosing data for 64 participants, mean TDD 37.3 U; overall-column row "TDD 37.3 (12.2)" of the diabetes-management table | consistent, **table number and page not captured** |
| `tdd_sd_u` | 12.2 U | same sentence/row | consistent, location not captured |
| `cycle_length_mean_d` | 28.4 d | "mean cycle length 28.4 days (SD 3.1)", citing Supplementary Table 3 | consistent, page not captured |
| `cycle_length_sd_d` | 3.1 d | same | consistent; check it is between-person SD |
| `share_consistent_with_population_trend` | 0.847 | "84.7% of participants" follow the population trajectory | consistent |
| `sensitivity_contrast_early_follicular` | +0.026 [0.003, 0.050] | text for the 84.7% group: **+2.7% (CrI 0.4, 5.0)**; secondary reports state +2.6% population-level | **AMBIGUOUS: possible mismatch** |
| `sensitivity_contrast_midluteal` | -0.026 [-0.052, -0.001] | text: -2.7% for the 84.7% group; secondary reports -2.6% | **AMBIGUOUS** |
| `sensitivity_contrast_periovulatory` | UNRESOLVED | text: +1.9% (CrI 0.3, 3.4) in the same sentence | candidate value; confirm quantity |
| `sensitivity_contrast_late_follicular` | UNRESOLVED | secondary report: "above average through the late follicular phase"; no number captured | not captured |
| `luteal_length_mean_d`, `_sd_d` | 14.0 / 1.7 | not found in captured text | not captured |
Other captured context (not IRIS inputs): bolus 20 U (SD 9.7) and basal 17.5 U (SD 8.4); phase TDD means 34.9, 36.6, 37.2, 38.1, 38.5, 38.8 U (P<0.001).

## Questions only you can settle
1. Are the +2.7%/-2.7% in the 84.7% sentence the same quantity as IRIS's population-level +/-0.026, or a subgroup mean? Which table/figure reports the population-level estimate and its interval? If they differ, follow "When the paper disagrees with IRIS" in `01_source_verification_runbook.md`.
2. Where are the late-follicular, periovulatory and early-luteal/late-luteal contrasts, anovulatory prevalence and luteal-length statistics?
3. Is TDD the mean of person means or the mean over days? (affects the lognormal `tdd` marginal in S3)

## Expected effect on the project (tested in a scratch simulation, not on real sign-offs)
`S3_virtual_population` runs in production as soon as **these nine rows are RESOLVED** and synced (`sync_population_status`): `tdd_mean_u`, `tdd_sd_u`, `cycle_length_mean_d`, `cycle_length_sd_d`, `luteal_length_mean_d`, `luteal_length_sd_d`, `share_consistent_with_population_trend`, `sensitivity_contrast_early_follicular`, `sensitivity_contrast_midluteal`; plus the S1 source row itself verified. The other S1 anchors (late-follicular, periovulatory, early/late-luteal contrasts, anovulatory prevalence) stay declared analyst completions (STRESS_TEST) and are reported as such; they do **not** block S3.
**If the paper does not report luteal length (not found in the captured text):** stop. S3 cannot run without a verified luteal length. Do not keep 14.0 +/- 1.7 on the strength of the `[VERIFY]` note. Find a primary source for it (record it as a new registry source with its own verification) and write the decision in `docs/decisions/`.
F2, F1, F3, F4, F6, R1-R3 then still need **potency draws**, which need L2 (degradation literature S7-S14, verified rows) and E4.
