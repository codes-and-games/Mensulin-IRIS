# Kaggle and ML guide

## Decision first: what ML IRIS needs, and whether Kaggle is needed
- The IRIS estimator is a state-space model (extended Kalman filter with RTS smoother), **not** machine learning. The only ML is a **benchmark**: Random Forest (`n_estimators` 200, `min_samples_leaf` 5, seed from the config) and Gradient Boosting (`n_estimators` 200, `max_depth` 2, `learning_rate` 0.05) in `src/iris/estimator/ml_benchmarks.py`, used by M3 (generalisation) and, as a 40-tree Random Forest "identity canary", by M4 (leakage test). Hyperparameters are fixed in code, **not tuned**, so no search can leak or inflate results. This is proportionate to the research question and stays that way.
- With the Phase 1 data (no cycle labels) M4, the naive baseline of M1 and M6 (an EKF method check) run, and since decision D-22 so does **M7**, the first supervised ML benchmark (next-day TDD; ridge, random forest, gradient boosting against persistence and a trailing mean, participant-held-out). **M2/M3 need cycle labels** and stay `NOT YET JUSTIFIED` until a labelled dataset (T1DEXI) is obtained; no model is trained on invented labels.
- M7 is the one experiment worth running on Kaggle: `notebooks/iris_kaggle_m7_training.ipynb` (provisional mode, finds and hash-checks the attached datasets by file name). Judge it only by `verdict` and `placebo_control`; a model that does not beat the trailing mean is a legitimate finding.
- Every experiment finishes in about a minute on one CPU core, so **Kaggle is optional**. Its value is an independent, repeatable, online run that does not depend on your laptop. If you skip it, nothing is lost scientifically.

## Data governance (decides what may go to Kaggle)
| Dataset | May be uploaded to Kaggle? |
|---|---|
| HUPA-UCM, BrisT1D-Open | Only after you have **read and recorded the licence** on the original page (a third-party listing says CC BY 4.0: confirm) and only as an **unmodified copy** with attribution, set to **Private** |
| DiaTrend (Synapse), OhioT1DM (DUA), T1DEXI (Vivli) | **Never.** Their terms forbid redistribution; T1DEXI analysis stays inside Vivli |
| Derived person-level tables, any dataset | No (the notebook exports QC reports only) |
Check before uploading: no file contains names, dates of birth or free text; file names are unchanged; licence and DOI are in the dataset description.

## Steps (UI labels may differ slightly)
1. **Account:** create a Kaggle account, verify your phone number (needed to turn Internet on in notebooks). Settings -> keep notebooks private.
2. **Release first:** the repository tag you will run must contain the verified `data/sources_registry.csv`, `data/manifest.csv` and AUDITED `configs/mappings/*.yaml` (docs/release/release_checklist.md). Commit and tag on GitHub (`git tag v0.1.0 && git push --tags`). The notebook refuses to run on a moving branch by design (it checks out a tag).
3. **Datasets:** Kaggle -> Datasets -> New Dataset -> drag the **unmodified** files of one dataset -> title `iris-hupa-ucm` (and `iris-brist1d-open` for the second) -> visibility **Private**. Paste licence/attribution into the description (templates: `kaggle/dataset-metadata.*.json`).
4. **Notebook:** Code -> New Notebook -> File -> Import Notebook -> `notebooks/iris_kaggle_phase1.ipynb`. Right panel: **Add Input** -> attach both datasets; **Accelerator: None**; **Internet: On**; Persistence: Files only.
5. **Edit one cell:** `REPO_URL`, `TAG`, and the dataset folder names in `DATASETS`.
6. **Run:** Save Version -> *Save & Run All (Commit)*. Expected: ingest prints the number of persons/days; M4 `completed`; M1 `completed`; M6 `completed` or `BLOCKED` with a reason.
7. **Download:** open the finished version -> Output tab -> download `iris_kaggle_outputs.zip` (contains `runs/`, `pip_freeze.txt`, `environment.json`, QC reports; no raw data).
8. **Bring it back:** unzip; copy each `runs/<run_id>` folder into `results/runs/`; then
   ```powershell
   python scripts/verify_run_dir.py results/runs/<run_id>
   ```
   It must print `OK`. It fails on a changed table, missing provenance, synthetic lineage or a test/provisional/smoke stamp. Commit the run folders (`git add results/runs`), noting the tag and the Kaggle notebook version in the commit message.

## Leakage prevention, seeds, reporting (what the code already enforces)
- Evaluation is **subject-grouped cross-validation only**; the leakage test (M4) shows row-wise splitting leaks and that an identity canary cannot predict under grouped splits. A leakage guard (`src/iris/features/leakage_guard.py`) checks the split design and is covered by the tests in `tests/`.
- Seeds: every experiment config has a fixed seed (20261004); random streams are derived per component (`RngTree`), so results are repeatable.
- Metrics and uncertainty: reported by the experiment tables with grouped-CV spread; do **not** quote a model as "good" before M3 has run on labelled data and the checklist is complete.
- Serialisation: ML benchmarks are not stored as models; the experiment tables are the artefact. Naming: `results/runs/<UTC date>_<git hash>_<config hash>/`.

## Optional: local run instead of Kaggle
Identical commands run locally (see `docs/runbook/05_production_runbook.md`). Use Kaggle only if you want the independent repeat.
