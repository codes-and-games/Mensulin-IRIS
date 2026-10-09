"""Write the two human sign-off worksheets with PRE-COLLECTED evidence (columns prefixed `prepared_`).

Prepared evidence is a *reviewer aid*. It is never copied into the registry by `apply-*`; only the human-entered columns are.
Evidence below was captured on 2026-10-07 from search-engine renderings of the publisher/PubMed/PMC/Synapse/Vivli pages, NOT from a
direct read of each primary page (PMC/doi.org blocked automated fetch). Page/table/figure numbers are therefore deliberately absent.
    PYTHONPATH=src python scripts/prepare_verification_worksheets.py
"""
from pathlib import Path

from iris.tools.source_verification import params_worksheet, sources_worksheet

ROOT = Path(__file__).resolve().parents[1]

S1 = ("Open-access article: Diabetes Care 2026 Jul 22 (online); 49(9):1673-1680; DOI 10.2337/dc26-0692; PMC13493352; PubMed 42482329. "
      "First author Stefanie Hossmann (Diabetes Center Berne). 77 participants, 380 cycles; AID users who self-tracked cycles; hierarchical Bayesian "
      "state-space model of insulin sensitivity. TDD reported for 64 participants: 37.3 U (SD 12.2) = bolus 20 (9.7) + basal 17.5 (8.4). "
      "Mean cycle length 28.4 d (SD 3.1) cites Supplementary Table 3. Overall-column TDD 37.3 (12.2) appears in the diabetes-management-metrics table "
      "(table number not captured); phase TDD means 34.9/36.6/37.2/38.1/38.5/38.8 U (early follicular ... late luteal), P<0.001. "
      "84.7% of participants follow the population trajectory. Carbohydrate 118.8 g/day (n=61) is from a secondary report (Healio), not the paper text.")
S1_OPEN = ("(1) PMC/doi.org could not be opened by the preparer: confirm every value on the page/PDF and record table/figure numbers. "
           "(2) Phase-effect wording: the paper sentence on the 84.7% group gives early follicular +2.7% (CrI 0.4, 5.0) and periovulatory +1.9% (0.3, 3.4); "
           "secondary reports and IRIS use +/-2.6% with CI 0.003..0.050 / -0.052..-0.001. Decide whether these are the same quantity (population posterior vs a subgroup mean) "
           "and record which table/figure each comes from. (3) Registry lists luteal length 14.0 (SD 1.7), anovulatory prevalence and late-follicular/periovulatory/early-luteal/late-luteal contrasts "
           "as [VERIFY]/[TO EXTRACT]: not found in the captured text; search main text, Supplementary Tables and Supplementary Figs. (4) Check whether TDD is arithmetic mean over days then people.")

SOURCES = {
 "S1": dict(evidence=S1, open=S1_OPEN),
 "S2": dict(evidence="PubMed 26468135: 'Fluctuations of Hyperglycemia and Insulin Sensitivity Are Linked to Menstrual Cycle Phases in Women With T1D'. 12 subjects (age 33.1+/-7.0), Kalman-filter nocturnal SI; SI lower in luteal vs early follicular (P<=.05); total daily insulin, carbohydrates and calories showed no significant fluctuation.",
            open="Confirm author list (registry says Brown et al.), journal volume/pages (registry says J Diabetes Sci Technol 2015), DOI, and licence."),
 "S3": dict(evidence="Registry flags [VERIFY authors/journal]. Project document quotes median TDD 37.4 U (early follicular) to 38.5 U (late luteal), p=0.02, and N described as 179 participants. Not independently checked this session.",
            open="Confirm full citation, N for the TDD analysis, phase definitions, and the exact TDD figures."),
 "S4": dict(evidence="PubMed 41877361: 'Glycemic Control During the Menstrual Cycle in Women With T1D: Performance of an AID System'. 48 cycles from 17 women, MiniMed 780G; late luteal (days -7..-1) vs early follicular (days 1-7); TDD higher in late luteal (33.1 vs 32.0 U, p<0.05 in the abstract snippet).",
            open="Registry DOI doi:10.1111/dom.70673 not checked; confirm DOI, author list, and that the TDD values are as stated (snippet was truncated)."),
 "S5": dict(evidence="Found DOI 10.1515/jpem-2026-0309: adolescents 12.0-17.9 y, >=1 y postmenarche, AID >=6 months, app-tracked cycles, nine complete cycles per participant; luteal-phase insulin demand and hyperglycaemia.",
            open="Confirm title/authors/volume (registry says J Pediatr Endocrinol Metab 2026 [VERIFY]) and licence."),
 "S15": dict(evidence="Registry: Data in Brief doi:10.1016/j.dib.2024.110559; Mendeley Data doi:10.17632/3hbcscwz44.1. Project document: 25 people, >=14 days, FreeStyle Libre 2, bolus/basal/carbs, no cycle labels. A third-party benchmark listing reports CC BY 4.0 (secondary, not authoritative).",
             open="Read the licence line on the Mendeley Data page itself and the dataset version number; record both."),
 "S16": dict(evidence="Scientific Data 2023;10:556 (arXiv 2304.06506). 54 people with T1D; 27,561 CGM days; 8,220 pump days; 54 Excel files (one per subject); controlled access via Synapse; access DOI 10.7303/syn38187184 (listed by the authors' lab page). Participants consented to open sharing but access is controlled.",
             open="Record the Synapse access conditions and approval date; version/date of the downloaded files."),
 "S17": dict(evidence="Registry: arXiv 2507.17757 and Bristol repository. Project document: BrisT1D-Open ~19 usable [VERIFY], CC BY 4.0 for the open part. A third-party listing also reports BrisT1D-Open as CC BY 4.0 (secondary).",
             open="Confirm the open-part licence, version and participant count on the Bristol repository page."),
 "S18": dict(evidence="Registry: Marling & Bunescu 2020 [NOT VERIFIED]. Project document: 12 people, ~8 weeks, data use agreement.",
             open="Locate the official OhioT1DM page and DUA; record who signed and when. Phase 2 only."),
 "S19": dict(evidence="T1DEXI datasets are listed on Vivli (a Helmsley Charitable Trust grant funds a Vivli data-sharing platform for T1-DEXI datasets). Vivli process (from Vivli pages): request -> administrative check -> contributor feasibility review -> Independent Review Panel -> DUA executed per team member -> analysis inside Vivli secure research environment; typically 'a few months'.",
             open="Confirm the exact study identifier on Vivli and whether menstrual-cycle variables exist and how they are coded (project document: [VERIFY]). Phase 2 only."),
 "S38": dict(evidence="ClinicalTrials.gov NCT06282055: 'Trajectories in Insulin Sensitivity Across MEnstrual cycleS in Women With Type 1 Diabetes' (TIMES). Context only; never a model input.",
             open="Confirm funder page citation and access date."),
}
PARAMS = {
 "tdd_mean_u": "Results text: 'Information on insulin doses was available for 64 participants, with a mean TDD of 37.3 units (SD 12.2)'. Table row 'TDD | 37.3 (12.2)' in the diabetes-management-metrics table. Table number and page NOT captured.",
 "tdd_sd_u": "Same sentence/table row: SD 12.2 U. Page/table not captured.",
 "cycle_length_mean_d": "Results text: 'The mean menstrual cycle length was 28.4 days (SD 3.1)' citing Supplementary Table 3. Page not captured.",
 "cycle_length_sd_d": "Same sentence: SD 3.1 d (between-cycle SD across participants as reported; check definition).",
 "sensitivity_contrast_early_follicular": "AMBIGUOUS: paper text for the 84.7% group gives +2.7% (CrI 0.4, 5.0); secondary reports give +2.6% for the population-level effect. IRIS stores 0.026 [0.003, 0.050]. Reviewer must read which quantity each number is.",
 "sensitivity_contrast_midluteal": "Paper text: -2.7% for the 84.7% group (CrI not captured); secondary reports: -2.6% population-level. IRIS stores -0.026 [-0.052, -0.001]. Reviewer must reconcile.",
 "share_consistent_with_population_trend": "Paper text: 84.7% of participants showed a consistent trajectory (above-average sensitivity early follicular and periovulatory; below-average midluteal).",
 "luteal_length_mean_d": "Not found in captured text. Search main text and Supplementary Table 3.",
 "luteal_length_sd_d": "Not found in captured text.",
 "sensitivity_contrast_late_follicular": "Secondary report: sensitivity 'remained above average through the late follicular phase'. Numeric value not captured: extract from the paper's figure/supplement.",
 "sensitivity_contrast_periovulatory": "Paper text: +1.9% (CrI 0.3, 3.4) appears in the sentence on the 84.7% group; confirm it is the population-level estimate.",
}

if __name__ == "__main__":
    out = ROOT / "docs/literature"
    n1 = sources_worksheet(ROOT, out / "source_verification_worksheet.csv", SOURCES)
    n2 = params_worksheet(ROOT, out / "parameter_verification_worksheet.csv", PARAMS)
    print(n1, "source rows;", n2, "parameter rows")
