"""Machine-readable publication data book: datasets/sources, hashes, licences, parameters, transformations, experiments, runs, tables,
figures and limitations. Built only from the repository (registry, manifest, literature tables, stored runs); deterministic ordering."""
from __future__ import annotations

import csv
import json
from pathlib import Path

LIMITATIONS = [
    "IRIS is a research simulation/inference framework, not a clinical dosing system or medical device; no output is a dosing or treatment recommendation.",
    "Virtual individuals are SIMULATED; they are not an observed cohort. PROJECTED outputs are model-based extrapolations, not empirical findings.",
    "Computational robustness is conditional on the declared admissible set and adversarial search budget; it is not proof of real-world truth.",
    "Parameters tagged unresolved/pending-verification are not production inputs; provisional and test runs are stamped accordingly.",
    "Glucose-equivalent quantities are model-conditional and secondary.",
]


def build_databook(root: str | Path) -> dict:
    root = Path(root)
    book = {"limitations": LIMITATIONS, "sources": [], "manifest": [], "parameters": [], "experiments": [], "runs": []}
    reg = root / "data/sources_registry.csv"
    if reg.exists():
        with open(reg, newline="") as fh:
            book["sources"] = sorted(csv.DictReader(fh), key=lambda r: r["source_id"])
    man = root / "data/manifest.csv"
    if man.exists():
        with open(man, newline="") as fh:
            book["manifest"] = sorted(csv.DictReader(fh), key=lambda r: r["path"])
    bio = root / "literature/biological_evidence.csv"
    if bio.exists():
        with open(bio, newline="") as fh:
            book["parameters"] = list(csv.DictReader(fh))
    book["experiments"] = sorted(p.name for p in (root / "experiments").iterdir() if (p / "run.py").exists()) if (root / "experiments").exists() else []
    runs_dir = root / "results/runs"
    for d in sorted(runs_dir.iterdir()) if runs_dir.exists() else []:
        pj = d / "provenance.json"
        if not pj.exists():
            continue
        run = json.loads(pj.read_text())["run"]
        tables = sorted(p.name for p in (d / "tables").glob("*.parquet")) if (d / "tables").exists() else []
        figs = sorted(p.name for p in (d / "figures").glob("*.png")) if (d / "figures").exists() else []
        book["runs"].append({k: run.get(k) for k in ("run_id", "experiment", "status", "run_mode", "seed_global", "git_hash", "config_hash", "evidence_class_counts", "partial_blockers", "blocker")}
                            | {"tables": tables, "figures": figs, "stamp": run.get("stamp", "")})
    return book


def write_databook(root: str | Path, out_dir: str | Path | None = None) -> Path:
    root = Path(root)
    out = Path(out_dir) if out_dir else root / "docs/databook"
    out.mkdir(parents=True, exist_ok=True)
    book = build_databook(root)
    (out / "databook.json").write_text(json.dumps(book, indent=2, sort_keys=True))
    lines = ["# IRIS data book (generated; do not edit)", "", "## Limitations", *[f"- {x}" for x in book["limitations"]], "", "## Sources",
             "| source_id | class | title | licence | verified_by |", "| --- | --- | --- | --- | --- |"]
    lines += [f"| {s['source_id']} | {s['class']} | {s['title']} | {s['licence'] or '—'} | {s['verified_by'] or 'UNVERIFIED'} |" for s in book["sources"]]
    lines += ["", "## Runs", "| run_id | experiment | status | mode | tables | figures |", "| --- | --- | --- | --- | --- | --- |"]
    lines += [f"| {r['run_id']} | {r['experiment']} | {r['status']} | {r['run_mode']} | {len(r['tables'])} | {len(r['figures'])} |" for r in book["runs"]]
    (out / "databook.md").write_text("\n".join(lines) + "\n")
    return out / "databook.json"
