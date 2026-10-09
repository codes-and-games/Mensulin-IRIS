"""python -m iris.tools.make_mapping_template <dataset> <source_id> [--audit data/dictionaries/audit_<dataset>.json] [--raw-dir data/raw/<dataset>]
Writes configs/mappings/<dataset>.yaml as a DRAFT with ranked candidates. A human must complete and mark it AUDITED."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from iris.common.io import dump_yaml
from iris.ingest.mapping import make_template

ROOT = Path(__file__).resolve().parents[3]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset"); ap.add_argument("source_id")
    ap.add_argument("--audit"); ap.add_argument("--raw-dir"); ap.add_argument("--root", default=str(ROOT))
    a = ap.parse_args(argv)
    root = Path(a.root)
    audit_path = Path(a.audit) if a.audit else root / f"data/dictionaries/audit_{a.dataset}.json"
    if not audit_path.exists():
        print(f"missing audit file {audit_path}. Run: python -m iris.tools.audit_data data/raw/{a.dataset} {audit_path}")
        return 2
    audit = json.loads(audit_path.read_text())
    if not audit.get("n_files"):
        print("audit contains 0 tabular files: nothing to map"); return 2
    t = make_template(audit, a.dataset, a.source_id, a.raw_dir or f"data/raw/{a.dataset}")
    t["audit_file"] = ""                       # stays empty until a human completes the review
    out = root / "configs/mappings" / f"{a.dataset}.yaml"
    if out.exists():
        print(f"{out} already exists; refusing to overwrite (move it first)"); return 2
    dump_yaml(t, out)
    print(f"wrote DRAFT {out} ({t['n_files_audited']} files audited). Review `candidates`, fill columns/units/tz, set audit_status: AUDITED.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
