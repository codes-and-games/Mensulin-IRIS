# 06 Troubleshooting

| Symptom | Meaning | Fix |
|---|---|---|
| `BLOCKED: SCIENTIFIC BLOCKER: parameter 'X' is unresolved ... Needed: ...` | The repository refuses to invent X | Do exactly what "Needed" says; do not edit configs to bypass |
| `UnregisteredSourceError: source 'Sn' is registered but unverified: missing [...]` | Registry row lacks access date / licence / verified_by | Complete the worksheet row, `apply-sources` |
| `UnregisteredSourceError: file '...' is not listed in data/manifest.csv` | A raw file was not registered | `python -m iris.tools.register_raw <dataset> <source_id>` |
| `ProvenanceError: hash mismatch` | A raw file changed after registration | Restore the original download; never re-hash silently |
| `TestOnlyDataError` in production for S1/S2 | Synthetic-truth experiments are test-mode by design | Run them with `--mode test`; report as code verification |
| `RunExistsError` | A *completed* run with the same date/commit/config exists | Use that run folder (immutable by design); change nothing |
| `ScientificBlocker column_mapping ... not marked AUDITED` | Mapping still DRAFT | `docs/data/04_ingestion_and_mapping.md` |
| `mapped columns missing [...]` | Mapping does not match this dataset version | Re-audit this exact download, correct the mapping |
| `ingested in 'provisional' mode; cannot feed a 'production' run` | Ingest mode too weak | Re-run `ingest_dataset ... --mode production` |
| `apply-params`: `verifier equals extractor` | Second reader required | Different person verifies, or `--allow-single-reader` and document the limitation in the verification log |
| `apply-params`: `value does not match the paper -> NOT applied` | The tool logs `MISMATCH_REPORTED` and changes nothing | Follow `docs/literature/01_source_verification_runbook.md` section "When the paper disagrees with IRIS"; after second-reader verification and a numbered decision note, use the documented `sync_population_status --approve-mismatch ... --decision-note ...` path only for the explicitly approved parameter group |
| `claims_lint` failure | A document makes an unsupported claim | Reword; see `python -m iris.tools.claims_lint --help` |
| DiaTrend Excel files unreadable | `.xlsx` needs `openpyxl` | `python -m pip install openpyxl` |
| Windows: `make` not found | Not installed | Use the `python -m` equivalents in the docs |
| Timestamps shift by one hour in spring/autumn | DST rows are dropped as ambiguous (logged) | Check `ingest_report.json` log; set the correct `tz` from the dataset paper |
