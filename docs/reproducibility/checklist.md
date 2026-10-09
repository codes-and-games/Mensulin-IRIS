# Reproducibility checklist (another competent researcher, clean machine)

| Item | Where | Done |
|---|---|---|
| Environment: Python >= 3.11, `pip install -e ".[dev]"`; exact versions `requirements-lock.txt` | `docs/runbook/02_environment_setup.md` | [ ] |
| Code at an immutable tag; **runs made from a committed tree** (run ids contain the git hash; a dirty tree is marked) | git tag `vX.Y.Z` | [ ] |
| Source registry with access date, licence, version, sha256, verifier | `data/sources_registry.csv` | [ ] |
| Verification records | `docs/literature/verification_log.csv` + worksheets | [ ] |
| Data manifest (hash of every raw file; **no raw data in Git**) | `data/manifest.csv` | [ ] |
| Evidence screenshots / licence quotes for open datasets | `docs/data/evidence/<id>/` | [ ] |
| Dataset mappings AUDITED, with audit JSON | `configs/mappings/`, `data/dictionaries/` | [ ] |
| Ingestion commands and QC reports | `docs/data/04_ingestion_and_mapping.md`, `data/processed/<id>/qc_report.json` (QC only) | [ ] |
| Experiment configs and seeds | `experiments/*/config.yaml`, `configs/` | [ ] |
| Production commands + expected outputs | `docs/runbook/05_production_runbook.md`, `experiments/*/expected_outputs.md` | [ ] |
| Run folders with provenance (production only) | `results/runs/<id>/` + `verify_run_dir.py` OK | [ ] |
| Pre-registration frozen + tag | `docs/prereg/conclusions.yaml`, tag `prereg-v1` | [ ] |
| Decision log and limitations | `docs/decisions/`, `templates/limitations_template.md` | [ ] |
| Figures/tables regenerate from stored runs | `python -m iris.tools.make_report` | [ ] |
| Controlled-access data: how to obtain it, never included | `docs/data/03,05,06` | [ ] |
| Citation file and licence | `CITATION.cff`, `LICENSE`, dataset attributions in README | [ ] |
