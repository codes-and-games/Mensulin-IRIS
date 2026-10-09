# 07 Final result assembly

1. All production runs finished; `results/status_production.md` saved. `python -m iris.tools.verify_registry` exits 0.
2. `python -m iris.tools.make_report` builds figures and `docs/databook/` from stored tables.
3. Fill `templates/results_report_template.md` strictly from `results/runs/*/tables`: every number cites a run ID. Fill `templates/limitations_template.md`.
4. Run `python -m iris.tools.claims_lint README.md docs/decisions/*.md docs/paper/*.md` and fix every flagged claim.
5. Confirm every conclusion's status (confirmatory / exploratory / not supported) matches `docs/prereg/conclusions.yaml` and its freeze tag.
6. Complete `docs/validation/scientific_validation_checklist.md` and `docs/reproducibility/checklist.md`.
7. Create the release: `docs/release/release_checklist.md`.

What the finished project contains: verified source registry and logs; ingested data manifests (hashes only, no raw controlled data); production run folders with provenance; figures/tables/data book; frozen pre-registration; decision log; limitations; reproducibility package.
