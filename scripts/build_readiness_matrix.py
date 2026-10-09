"""Build docs/experiments/readiness_matrix.{csv,md}.

Factual columns (current production status / exact blocker, expected outputs, upstream references) are computed from the
repository and a live `--mode production` run of every experiment. Judgement columns (purpose, class, unblock path, claim
support, caveat) are authored below and reviewed with the project document. Re-run after any change:
    PYTHONPATH=src python scripts/build_readiness_matrix.py
"""
from __future__ import annotations

import csv
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/experiments"

CLASSES = ["READY", "READY AFTER SOURCE VERIFICATION", "READY AFTER DATA ACQUISITION", "READY AFTER MAPPING",
           "READY AFTER PREREG FREEZE", "DEPENDENT ON UPSTREAM EXPERIMENT", "SCIENTIFICALLY REFUSED", "NOT YET JUSTIFIED"]

# id: (purpose, question, data, literature, klass, unblock, validation, mode_note, claim, caveat)
M = {
"E1_climate_agreement": ("Cross-source agreement/QC of 2 m temperature records at Koppen-Geiger-selected locations", "Do ERA5-Land, ERA5, NASA POWER and IMD agree within pre-registered thresholds; what is sigma_val?", "S27-S30 (climate records)", "S36 (published validation of reanalysis 2 m temperature)", "READY AFTER DATA ACQUISITION", "CODE LIMITATION first: E1 has no production code path (only the synthetic TEST path). Then: freeze location rule + thresholds (prereg), download + register S27-S30 (docs/data/07_climate_and_context.md), verify sources", "Records hash-registered; thresholds frozen before inspection; agreement table + figures regenerate byte-stable from seed", "Cannot run in production until a production reader is written; then needs verified sources", "Yes: climate-input uncertainty for the exposure model (not a biological claim)", "Reanalysis is not in-vial temperature; agreement does not prove accuracy"),
"E2_reconstruction_context": ("Sub-daily reconstruction (Parton-Logan) and context mapping (IMAC/ASHRAE fit + hold-out)", "Does the reconstruction/context mapping hold out-of-sample against ASHRAE II records?", "S27 (via E1), S31", "S32, S34, S36", "DEPENDENT ON UPSTREAM EXPERIMENT", "CODE LIMITATION (no production path, like E1); E1 done; S31 registered; S32/S34 verified", "Hold-out error vs fit error; no leakage between fit and hold-out buildings/sites", "Production only with verified sources", "Yes: context-temperature mapping accuracy", "Indoor-context mapping is a model, not a measurement of vial temperature"),
"E3_vial_lag": ("Numerical verification of the vial thermal-lag solver (lumped vs analytic vs finite-volume)", "Does the lag solver reproduce analytic/finite-volume benchmarks within tolerance?", "none (physics + configs/thermal/lag.yaml)", "S35 for real-world constants (not needed for the verification itself)", "READY", "Nothing for the verification; S35 constants must be verified before E4/F-series use real vial geometry", "lag_verification.json all cases within tolerance; tests/unit/test_thermal.py passes", "Runs in production; class SIMULATED", "Supports ONLY 'solver is numerically correct'", "Verification of code, not evidence about insulin vials"),
"E4_exposure_generation": ("Generate scenario thermal exposures and potency-loss draws", "What potency distribution results from each scenario given kinetics K0-K5?", "E1/E2 outputs, climate (S5 scenario), kinetics inputs", "L2 degradation literature (S7-S14), L5 context parameters, S35", "DEPENDENT ON UPSTREAM EXPERIMENT", "L2 (kinetic model set) and, for climate scenario S5, E1/E2; S35 verified", "Exposure series pass THERMAL_EXPOSURE schema; potency draws pass validate_potency_draws; blocked scenarios recorded, never filled", "PARTIAL in production today: exposure tables produced, potency draws blocked", "Yes (central to the project) once potency draws exist", "Kinetic parameters come from sparse, partly disagreeing literature (see S8/S11)"),
"F1_central": ("Central fusion: effective potency x biology -> insulin-effectiveness outcome", "Is the central estimate of effective insulin action robust to potency loss?", "stored potency draws (E4), virtual population (S3)", "L3", "DEPENDENT ON UPSTREAM EXPERIMENT", "E4 potency draws + S3 population in production mode", "Fusion invariants and sanity checks in tests/; seed-stable tables", "Production only from production-mode upstream tables", "Yes", "Depends on all upstream assumptions"),
"F2_tail": ("Tail-risk fusion with large virtual population", "How large are the tails of the effectiveness distribution?", "S3 population (n_tail=100000), potency draws", "L3", "DEPENDENT ON UPSTREAM EXPERIMENT", "S3 (nine S1 rows verified); E4 potency draws (needs L2)", "Tail estimates stable across seeds; MC error reported", "Production only", "Yes", "Tail quantities are sensitive to unresolved biological parameters (completion options are STRESS_TEST)"),
"F3_compounding": ("Compounding: repeated exposure across consecutive dosing days", "Does cumulative exposure change the conclusions?", "potency draws, S3", "L3, L2", "DEPENDENT ON UPSTREAM EXPERIMENT", "E4 + S3", "Matches single-day results at J=1", "Production only", "Yes", "Independence assumptions across days are modelled, not measured"),
"F4_ablation": ("Ablation controls (incl. A4 circularity control)", "Do conclusions survive removing each modelling component; is there circularity?", "as F1", "L3", "DEPENDENT ON UPSTREAM EXPERIMENT", "E4 + S3", "A4 pushes phi toward 1 (else FAILED_CONTROL)", "Production only", "Yes (as a control)", "A failed control invalidates dependent claims"),
"F5_admissible_set": ("Evaluate pre-registered conclusions over the admissible set", "Which pre-registered conclusions hold across the admissible parameter set?", "F1/F2/F4 outputs", "docs/prereg/conclusions.yaml (C1, C2)", "READY AFTER PREREG FREEZE", "Owner freezes conclusions.yaml (docs/prereg/freeze_procedure.md), then upstream F runs", "Margins computed against FROZEN thresholds only", "Production only after freeze", "Yes: the confirmatory conclusions", "Thresholds may not be changed after results are seen"),
"F6_dependence_transport": ("Dependence/transport: how conclusions move along dependence axes", "Do conclusions hold when dependence between potency and biology changes?", "as F5", "L3", "DEPENDENT ON UPSTREAM EXPERIMENT", "Upstream F-series + frozen conclusions", "Margins per axis value; blocked cells recorded", "Production only", "Yes (exploratory unless pre-registered)", "Dependence structures are analyst-defined completions"),
"L1_novelty": ("Novelty/evidence search log validation", "Is there prior work that already answers the IRIS question?", "literature/novelty_search_log.csv (human search)", "all", "READY AFTER SOURCE VERIFICATION", "Run and log the search (docs/literature/01_source_verification_runbook.md section L1); log needs searched_by", "Log has dates, databases, queries, result counts, closest prior study", "Production uses the human-authored log", "Supports the novelty statement only", "Search completeness cannot be proven"),
"L2_degradation": ("Extract multi-temperature potency data -> fit kinetic models K1 -> LOSO evaluation", "Which kinetic models are supported by the published degradation data?", "literature/degradation_literature.csv", "S7-S14", "READY AFTER SOURCE VERIFICATION", "Extract rows from S7-S14 with page/table refs, second-reader verify", "LOSO error, parameter CIs; verified rows only in production", "Production uses verified rows only", "Yes (kinetics)", "Data are few and disagree (S8 vs S7/S11); report as such"),
"L3_biological_evidence": ("Status table of biological anchors", "Which biological parameters are verified, pending or unresolved?", "literature/biological_evidence.csv", "S1 (+S3, S26 context)", "READY AFTER SOURCE VERIFICATION", "S1 source verification + parameter worksheet sign-off (docs/literature/S1_hossmann_evidence.md)", "Every anchor RESOLVED with page/table ref + second reader", "Production uses RESOLVED rows only", "Yes (provenance of the anchors)", "Several S1 values (phase contrasts other than 2 phases, anovulatory prevalence) are still [TO EXTRACT]"),
"L4_isf_tdd": ("Empirical ISF vs TDD relationship", "How does clinician ISF relate to TDD?", "person_day with isf_clinician (DiaTrend pump settings)", "published ISF/TDD reports (fallback)", "READY AFTER DATA ACQUISITION", "DiaTrend access (Phase 2) + mapping; otherwise literature fallback", "Fit diagnostics; person-grouped uncertainty", "Production only with ingested data", "Supports ISF/TDD scaling assumption", "Pump-setting ISF is clinician-set, not measured sensitivity"),
"L5_thermal_context": ("Thermal-context parameter table", "What published parameters define indoor/outdoor context mapping?", "literature/thermal_context_parameters.csv", "S31, S32, S35", "READY AFTER SOURCE VERIFICATION", "Extract parameters with page/table refs; verify", "Verified rows only", "Production uses verified rows only", "Yes (context parameters)", "Parameters are population/regional, not site-specific"),
"M1_baseline": ("Baseline suite for relative TDD (naive mean; harmonic regression on cycle position)", "What accuracy does a person-free baseline achieve under subject-grouped CV?", "combined person_day", "none", "READY AFTER MAPPING", "Ingest HUPA-UCM/BrisT1D, --combine; cycle baselines stay blocked without labels", "Subject-grouped CV only; naive baseline reported", "Production needs verified+registered datasets", "Naive baseline only (no cycle biology) with unlabelled data", "Cycle baselines need real cycle labels (Phase 2)"),
"M2_cycle_estimation": ("Cycle-phase estimation vs placebo cycles", "Does the estimator recover cycle-linked sensitivity beyond placebo cycles?", "person-day/events WITH dataset-provided cycle labels", "S1 for expected effect size", "NOT YET JUSTIFIED", "Obtain a dataset with cycle labels (T1DEXI via Vivli, Phase 2); until then no cycle-skill claim is permitted", "Placebo-cycle null (n=60) must be exceeded", "Refused for unlabelled data", "No (today)", "Manufacturing labels is forbidden (project document)"),
"M3_generalisation": ("Generalisation of RF/GB benchmarks across subjects (grouped CV)", "Do cycle-aware benchmarks generalise to held-out subjects?", "person_day with cycle labels", "none", "NOT YET JUSTIFIED", "Cycle-labelled data (Phase 2)", "Leave-subject-out only", "Refused without labels", "No (today)", "Same as M2"),
"M4_leakage": ("Explicit leakage tests incl. identity canary (RF)", "Does the CV design prevent subject/time leakage; can the canary detect it?", "any combined person_day", "none", "READY AFTER MAPPING", "Ingest any one real dataset + --combine", "Grouped splits disjoint; row-wise split demonstrably leaks; canary unpredictable under grouped CV", "Production needs verified+registered data", "Supports 'evaluation design is leakage-free' only", "Passing says nothing about biology"),
"M5_empirical_isf_tdd": ("Spectral negative control in unlabelled long series", "Is a 21-35 day periodicity detectable in TDD without labels (females vs males)?", "DiaTrend (>=150 pump days for the female group)", "none", "READY AFTER DATA ACQUISITION", "DiaTrend access (Phase 2) + mapping", "False-positive rate under shuffled data reported", "Production only with ingested DiaTrend", "Negative-control calibration only", "Absence of a peak is not absence of cycle effects"),
"M6_circadian_recovery": ("Circadian (24 h) sensitivity recovery on real CGM/insulin/carb series (V2)", "Does the estimator recover a reproducible 24 h pattern in real data vs placebo shifts?", "HUPA-UCM + BrisT1D events grids", "none (direction vs literature: [VERIFY])", "READY AFTER MAPPING", "Download/audit/map/ingest HUPA-UCM and BrisT1D", "Split-half reproducibility; placebo shifts; nuisance-scale sensitivity", "Production needs verified+registered data", "METHOD PLAUSIBILITY only; no menstrual-cycle claim", "Small cohorts; HUPA-UCM is ~2 weeks per person"),
"R1_sensitivity": ("Global sensitivity (Sobol/SALib) of outcomes", "Which inputs drive outcome variance?", "fusion machinery + populations", "all", "DEPENDENT ON UPSTREAM EXPERIMENT", "S3 + E4 in production", "Indices sum sanity; bootstrap CIs", "Production only", "Yes (robustness)", "Climate input reported 'not applicable' while S5 is blocked"),
"R2_definition_robustness": ("Robustness to outcome definitions", "Do conclusions survive alternative definitions?", "fusion outputs", "L3", "DEPENDENT ON UPSTREAM EXPERIMENT", "F-series upstream", "Per-definition margins", "Production only", "Yes (robustness)", "Definition set fixed in advance"),
"R3_structural_robustness": ("Robustness to structural model choices", "Do conclusions hold across structural alternatives?", "fusion outputs", "L3", "DEPENDENT ON UPSTREAM EXPERIMENT", "F-series upstream", "Blocked structures are reported, not dropped", "Production only", "Yes (robustness)", "Structures are analyst-chosen"),
"S1_estimator_ground_truth": ("Verify the EKF/RTS estimator against known synthetic truth", "Does the estimator recover a known sensitivity profile?", "none (simulator, ASSUMPTION constants)", "T4 constants", "SCIENTIFICALLY REFUSED", "Run in test mode as a code-verification result; it cannot become production evidence by design", "Recovery error small; calibrated intervals", "TEST only (synthetic lineage)", "No: verification, not evidence", "Synthetic truth validates code, not biology"),
"S2_thermal_kinetics": ("Verify kinetic fitting recovers known synthetic parameters", "Does K1 fitting recover truth?", "none (synthetic)", "none", "SCIENTIFICALLY REFUSED", "Run in test mode as verification only", "Parameter recovery within tolerance", "TEST only", "No: verification", "As S1"),
"S3_virtual_population": ("Build the virtual population", "Population of TDD/cycle/sensitivity parameters anchored to S1", "none", "S1 (L3 table)", "READY AFTER SOURCE VERIFICATION", "Nine S1 rows RESOLVED (tdd, cycle, luteal length, concordance, two phase anchors) + sync_population_status; other items stay declared completions (STRESS_TEST)", "Marginals match anchors; seeds reproducible", "Production needs RESOLVED anchors", "Foundation for F/R series", "Completions are analyst-defined (Theta_S)"),
}


# Blocker types requested in the brief: code limitation | missing external input | missing scientific evidence | missing access |
# human sign-off requirement | research decision | scientifically unjustified experiment
BLOCKER_TYPE = {
 "E1_climate_agreement": "code limitation (no production path); research decision (location rule, thresholds); missing external input (climate records)",
 "E2_reconstruction_context": "code limitation (no production path); missing external input; upstream E1",
 "E3_vial_lag": "none",
 "E4_exposure_generation": "missing scientific evidence (L2 degradation rows); human sign-off (S35)",
 "F1_central": "upstream (E4 potency draws, S3); human sign-off", "F2_tail": "upstream (E4 potency draws, S3); human sign-off",
 "F3_compounding": "upstream (E4, S3)", "F4_ablation": "upstream (E4, S3)", "F6_dependence_transport": "upstream (E4, S3, F5 frozen conclusions as applicable)",
 "F5_admissible_set": "research decision (owner freezes C1/C2); upstream F-series",
 "L1_novelty": "missing scientific evidence (search not yet run/logged)", "L2_degradation": "human sign-off; missing scientific evidence (extraction S7-S14)",
 "L3_biological_evidence": "human sign-off (S1 rows)", "L4_isf_tdd": "missing access (DiaTrend)",
 "L5_thermal_context": "human sign-off; missing scientific evidence (extraction)",
 "M1_baseline": "missing external input (HUPA-UCM/BrisT1D download, mapping)", "M2_cycle_estimation": "scientifically unjustified without cycle labels; missing access (T1DEXI)",
 "M3_generalisation": "scientifically unjustified without cycle labels; missing access (T1DEXI)", "M4_leakage": "missing external input (any real dataset ingested)",
 "M5_empirical_isf_tdd": "missing access (DiaTrend); possible code limitation (multi-sheet Excel layout)", "M6_circadian_recovery": "missing external input (HUPA-UCM, BrisT1D)",
 "R1_sensitivity": "upstream (S3, E4)", "R2_definition_robustness": "upstream (F-series)", "R3_structural_robustness": "upstream (F-series)",
 "S1_estimator_ground_truth": "scientifically unjustified as production evidence (synthetic truth; verification only)",
 "S2_thermal_kinetics": "scientifically unjustified as production evidence (synthetic truth; verification only)", "S3_virtual_population": "human sign-off (nine S1 rows)",
}


def prod_status(eid: str) -> str:
    """Run one experiment in production mode into a throw-away runs directory (never touches results/runs)."""
    import os
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        code = ("import sys;from pathlib import Path;from iris.tools.run_experiment import run_experiment;"
                f"run_experiment({eid!r}, 'production', runs_root=Path({tmp!r}))")
        r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True,
                           env={**os.environ, "PYTHONPATH": str(ROOT / "src")})
        last = (r.stdout.strip().splitlines() or r.stderr.strip().splitlines() or ["(no output)"])[-1]
        msg = re.sub(r"^\[[^\]]+\]\s*", "", last)[:300]
        m = re.search(r"run_id=(\S+)", msg)
        if m and "completed" in msg:                  # a completed run can still have recorded scientific blockers
            log = Path(tmp) / m.group(1) / "log.txt"
            if log.exists():
                warns = [ln.split("WARNING", 1)[1].strip() for ln in log.read_text().splitlines() if "SCIENTIFIC BLOCKER" in ln]
                if warns:
                    msg += " | COMPLETED WITH RECORDED BLOCKERS (partial, not a full result): " + warns[0][:160]
        return msg


def expected_outputs(eid: str) -> str:
    p = ROOT / "experiments" / eid / "expected_outputs.md"
    if not p.exists():
        return "see experiment folder"
    return " ".join(p.read_text().split())[:350]


def upstream(eid: str) -> str:
    ids = {d.name.split("_")[0]: d.name for d in (ROOT / "experiments").iterdir() if d.is_dir()}
    txt = ""
    for f in ("README.md", "run.py", "config.yaml"):
        q = ROOT / "experiments" / eid / f
        if q.exists():
            txt += q.read_text()
    found = sorted({k for k in re.findall(r"\b([EFLMRS]\d)\b", txt) if k in ids and ids[k] != eid})
    return ", ".join(found)


def main() -> None:
    exps = sorted(p.name for p in (ROOT / "experiments").iterdir() if p.is_dir() and p.name[0] in "EFLMRS")
    missing = [e for e in exps if e not in M]
    extra = [e for e in M if e not in exps]
    if missing or extra:
        raise SystemExit(f"matrix out of sync with experiments/: missing {missing}, extra {extra}")
    rows = []
    for e in exps:
        purpose, q, data, lit, klass, unblock, valid, mode, claim, cav = M[e]
        assert klass in CLASSES, klass
        rows.append(dict(experiment=e, scientific_purpose=purpose, question=q, required_data=data, required_literature=lit,
                         references_to_other_experiments=upstream(e), classification=klass, blocker_type=BLOCKER_TYPE[e],
                         production_status_checked=prod_status(e), what_removes_the_blocker=unblock,
                         expected_output_files=expected_outputs(e), validation_criteria=valid,
                         production_vs_test=mode, supports_final_scientific_claim=claim, caveat=cav))
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "readiness_matrix.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    counts = {c: sum(r["classification"] == c for r in rows) for c in CLASSES}
    md = ["# Experiment readiness matrix", "",
          f"{len(rows)} experiments found in `experiments/`. Production status was produced by running every experiment with "
          "`--mode production` against the repository as it stands; regenerate with `make readiness`.", "",
          "A BLOCKED run is the repository refusing to invent an input. It is **not** a code failure. A run that completes is "
          "**not** scientific validation: see the last column.", "", "## Summary by class", ""]
    md += [f"- **{c}**: {n}" for c, n in counts.items() if n]
    md += ["", "## Matrix", "", "| Experiment | Class | Blocker type | Production status now | What removes the blocker | Supports a final claim? |", "|---|---|---|---|---|---|"]
    for r in rows:
        md.append("| {experiment} | {classification} | {blocker_type} | {production_status_checked} | {what_removes_the_blocker} | {supports_final_scientific_claim} |".format(**{k: str(v).replace("|", "/") for k, v in r.items()}))
    md += ["", "## Per-experiment detail", ""]
    for r in rows:
        md += [f"### {r['experiment']}", "",
               f"- **Purpose:** {r['scientific_purpose']}", f"- **Question:** {r['question']}",
               f"- **Required data:** {r['required_data']}", f"- **Required literature:** {r['required_literature']}",
               f"- **Other experiments referenced in its files:** {r['references_to_other_experiments'] or 'none detected'}",
               f"- **Class:** {r['classification']}", f"- **Blocker type:** {r['blocker_type']}", f"- **Production status (checked):** {r['production_status_checked']}",
               f"- **What removes the blocker:** {r['what_removes_the_blocker']}",
               f"- **Expected outputs (from `expected_outputs.md`):** {r['expected_output_files']}",
               f"- **Validation criteria:** {r['validation_criteria']}", f"- **Production vs test:** {r['production_vs_test']}",
               f"- **Supports a final scientific claim:** {r['supports_final_scientific_claim']}", f"- **Caveat:** {r['caveat']}", ""]
    (OUT / "readiness_matrix.md").write_text("\n".join(md), encoding="utf-8")
    print("written", len(rows), "rows;", counts)


if __name__ == "__main__":
    main()
