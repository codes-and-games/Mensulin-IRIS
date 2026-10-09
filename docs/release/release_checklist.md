# Release checklist (GitHub, Pages, optional Zenodo)

## A. Repository (once)
1. github.com -> New repository (e.g. `iris`), **Private** until step D. Do not add a README/licence there (the repo has them).
2. In the project folder: `git init`, `git add .`, `git commit -m "IRIS execution package"`, `git branch -M main`, `git remote add origin <url>`, `git push -u origin main`. Check on GitHub that **no file under `data/raw/`** was pushed (the `.gitignore` excludes it).
3. Actions tab: confirm the `ci` workflow is green.

## B. Before the first production run
`git status` must be clean (otherwise run ids are marked dirty). Commit verified registry/mappings first.

## C. Final package (after validation checklist is complete)
1. README: fill project summary, **what is and is not claimed**, dataset attribution (name, DOI, licence, version for each dataset used), licence section (code MIT; datasets keep their own terms), how to reproduce (link to `docs/START_HERE.md`).
2. `CITATION.cff`: fill authors, date, repository URL.
3. `CHANGELOG.md`: copy `templates/release_notes_template.md`.
4. Commit only verified production run folders under `results/runs/` (each passes `verify_run_dir.py`).
5. `python -m pytest tests -q` and `python -m iris.tools.claims_lint README.md docs/decisions/*.md` pass.
6. Tag and release: `git tag v1.0.0 && git push --tags`; GitHub -> Releases -> Draft new release -> choose tag -> paste release notes -> attach `iris_results.zip` (made from `results/`, `docs/databook/`, `manifests/`; no raw data) -> Publish.

## D. GitHub Pages (documentation site)
Settings -> Pages -> Source: **GitHub Actions**. Push to `main` runs `.github/workflows/pages.yml`, which builds `site/` with `python scripts/build_site.py` (docs and README only; no data, no run folders). The URL appears in the Actions run. Make the repository public only after step C is complete and you have confirmed no controlled data is in the history (`git log --stat | findstr data/raw`).

## E. Optional DOI
Zenodo -> log in with GitHub -> enable the repository -> publish a GitHub release; Zenodo mints a DOI. Add it to `CITATION.cff`.

## F. Artifact-upload checklist
- [ ] `iris_results.zip` has no raw or controlled data and no person-level derived tables.
- [ ] Dataset attributions present. - [ ] Limitations present. - [ ] Pre-registration tag referenced.

## Publication supplement structure
`supplement/` = pre-registration (frozen file + tag), source registry + verification log, mappings + QC reports, run tables, figures, decision log, limitations, reproducibility checklist.
