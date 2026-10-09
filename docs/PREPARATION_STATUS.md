# IRIS preparation status (2026-10-07)

## A. Current scientific state: what is actually established
- **Code verified:** the full test suite passes (100 tests); the TEST-mode pipeline runs end to end; every experiment finishes in under about a minute on one CPU core at configured size (synthetic inputs). This is **plumbing, not evidence**.
- **Production evidence: none yet.** In production mode 27 experiments were checked live (see `docs/experiments/readiness_matrix.md`): E3 completes (numerical solver verification only), E4 completes **partially** (exposure tables yes; potency draws blocked), S1 and S2 are correctly refused (synthetic truth), and 23 are BLOCKED by named inputs. No biological, cycle-skill or exposure conclusion is supported yet.
- **Critical path found by simulation:** S3 (virtual population) runs in production once nine S1 rows are verified and synced; fusion experiments then need potency draws, which need the degradation literature (S7-S14, L2). Climate data is not on the critical path.

## B. Remaining blockers (genuine only)
1. **Human sign-off:** S1 (nine parameter rows + source row), then the other sources. The preparer could not open PMC/doi.org, so nothing is verified; prepared evidence and one possible mismatch (+2.7% CrI 0.4-5.0 vs IRIS +0.026 CI 0.003-0.050) are in `docs/literature/S1_hossmann_evidence.md`. Luteal length was not found in the captured text; if the paper lacks it, S3 needs another verified source.
2. **Scientific evidence to extract:** degradation data (S7-S14), thermal-context parameters, novelty search log. Task lists and column specs are prepared; extraction is not (it needs the primary papers).
3. **External inputs:** HUPA-UCM and BrisT1D-Open files; later climate records; Phase 2 access (DiaTrend, T1DEXI, OhioT1DM).
4. **Owner decision:** freeze `docs/prereg/conclusions.yaml` (and justify `threshold_units: 2.0`).
5. **Open technical tasks (I did not do these; each is in the decision log):** T-01 evaluator assignment mode by scenario (decision D-19; affects how confirmatory F5/F6/R* conclusions on deterministic scenarios may be worded), T-02 E1/E2 production reader (code limitation; needs a frozen location rule and one real climate file), T-03 DiaTrend multi-sheet handling (needs the real audit).

## C. Files generated or changed (versus the uploaded tarball)
**Execution guides:** `docs/START_HERE.md`, `docs/HUMAN_ACTIONS.md`, `docs/RESOURCES.md`, `docs/PREPARATION_STATUS.md`, `docs/runbook/01,02,05,06,07`, `docs/data/00-07`, `docs/literature/01_source_verification_runbook.md`, `S1_hossmann_evidence.md`, `docs/ml/kaggle_and_ml_guide.md`, `docs/prereg/freeze_procedure.md`, `docs/validation/scientific_validation_checklist.md`, `docs/reproducibility/checklist.md`, `docs/release/release_checklist.md`, `docs/decisions/DECISION_LOG.md` (plus resolution notes appended to decisions 0001-0003).
**Generated tables:** `docs/experiments/readiness_matrix.{md,csv}` (27 rows, from a live run), `manifests/resource_manifest.csv`, the two verification worksheets in `docs/literature/` (with prepared evidence).
**Tools and tests:** `iris.tools.sync_population_status`, `iris.tools.inspect_grid`, optional `dataset_sha256` worksheet column, grid-consistency guard in `load_events`, `scripts/` (`build_readiness_matrix.py`, `build_resource_manifest.py`, `prepare_verification_worksheets.py`, `verify_run_dir.py`, `build_site.py`), tests for each.
**Online workflow:** `notebooks/iris_kaggle_phase1.ipynb`, `kaggle/*.json`, `.github/workflows/ci.yml`, `pages.yml`, `.gitignore`, `CITATION.cff`, `CHANGELOG.md`, `templates/` (Vivli, Synapse, OhioT1DM, results, limitations, release notes), `data/raw/` folders renamed/added (`brist1d`, `t1dexi`, `ohiot1dm`).
**Note:** the uploaded tarball predates other additions already present in the working tree when this phase began (ingest pipeline, mapping template, `register_raw`, `source_verification`, `run_all`, M6 and circadian estimator, blocked-run re-run, POSIX manifest paths); all have tests and were reviewed here.

## D. External resources required
See `docs/RESOURCES.md` (42 rows, categorised). In short: GitHub account; HUPA-UCM and BrisT1D-Open (open); the Hossmann paper and 29 other sources; Synapse, Vivli, OhioT1DM access (Phase 2); CDS/NASA/IMD/ASHRAE (optional Phase 1b); Kaggle account (optional).

## E. Exact execution order
Follow `docs/START_HERE.md` steps 0-10 (environment; Phase 2 requests; S1; other sources; literature tables; datasets; climate (optional); **freeze**; production runs; validation; release). The only-you list is `docs/HUMAN_ACTIONS.md`.

## F. Final expected outcome (if every step succeeds)
Verified registry and logs; ingested open datasets (hashes only in Git); production runs for the L, E3/E4, S3, F, R series and M4/M1/M6 with provenance; frozen pre-registration with confirmatory/exploratory labels; figures/tables/data book from stored runs; limitations; reproducibility package; GitHub release and Pages site. Menstrual-cycle skill conclusions only if a cycle-labelled dataset is obtained.

## Final gate: could someone follow START HERE to the end without hitting an undocumented decision?
**Almost, not fully.** Gaps I could not close from this environment, each named above: (1) T-01/T-02/T-03 code tasks; (2) the exact access route and terms of each climate source and of the OhioT1DM/BrisT1D pages were not verified; (3) mappings can only be completed against the real files; (4) per-source evidence for S7-S14 was not pre-collected (only S1-S5, S15-S19, S38 have prepared evidence).
