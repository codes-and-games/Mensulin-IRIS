# Scientific validation checklist

Complete after the production runs. Every line is answered **Yes / No / Not applicable (with reason)**, with the run ID or file that proves it. A "No" is written into the limitations; it is never deleted.

## 1. Input integrity
- [ ] `python -m iris.tools.verify_registry` exits 0 (every used source verified; hashes registered).
- [ ] Every parameter used by a cited run is RESOLVED, or listed as a declared completion (STRESS_TEST/ASSUMPTION) in the report.
- [ ] Verification log `docs/literature/verification_log.csv` has an entry (who, when, where in the source) for every verified source/value.
- [ ] No TEST_ONLY/provisional/smoke lineage in any cited run: `python scripts/verify_run_dir.py results/runs/<id>` prints OK for each.

## 2. Reproducibility
- [ ] Two clean runs of the same experiment from the tagged commit give identical table hashes (delete the run folder first in a scratch clone).
- [ ] Seeds are the config seeds; environment recorded (`requirements-lock.txt`, Python version).

## 3. Numerical sanity and verification
- [ ] E3 lag verification within tolerance; S1/S2 recovery (TEST mode) within tolerance. Reported as **code verification**, not evidence.
- [ ] Fusion invariants and unit tests pass at the cited commit (`python -m pytest tests -q`).

## 4. Sensitivity, robustness, uncertainty
- [ ] R1 sensitivity indices with intervals; R2/R3 robustness tables including blocked cells (reported, not dropped).
- [ ] Monte Carlo error reported for tail quantities (F2).
- [ ] The assumption/stress-test levels used are listed next to every conclusion.

## 5. Statistical validity and leakage
- [ ] M4: grouped splits disjoint; row-wise split demonstrably leaks; canary not predictable under grouped CV.
- [ ] All performance statements use subject-grouped CV only.

## 6. Calibration, baselines, ablations, failure cases
- [ ] M1 naive baseline reported next to any model; no "improvement" claim without it.
- [ ] F4 ablations incl. A4 control passed (else the dependent claim is withdrawn).
- [ ] Failure/BLOCKED cases listed with reasons.

## 7. External validity
- [ ] Which datasets were used, their sizes and limits (HUPA-UCM about 25 people x about 2 weeks; BrisT1D-Open small; no cycle labels).
- [ ] No cycle-skill claim unless M2/M3 ran on dataset-supplied labels with the placebo null exceeded.

## 8. Claims
- [ ] Each conclusion is labelled confirmatory (frozen, tag `prereg-v1`), exploratory, or not supported.
- [ ] Deterministic-scenario F5/F6/R* results are labelled with the assignment-mode caveat unless task T-01 is done (decision D-19).
- [ ] `python -m iris.tools.claims_lint README.md docs/decisions/*.md` passes.
- [ ] Limitations template filled (`templates/limitations_template.md`).
