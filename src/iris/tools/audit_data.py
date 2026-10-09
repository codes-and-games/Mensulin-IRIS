"""CLI:  python -m iris.tools.audit_data [raw_dir] [out_json]   (make audit)"""
from __future__ import annotations

import sys
from pathlib import Path

from iris.ingest.audit import audit_directory, write_audit
from iris.tools.verify_registry import verify

ROOT = Path(__file__).resolve().parents[3]


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    raw = Path(argv[0]) if argv else ROOT / "data/raw"
    out = Path(argv[1]) if len(argv) > 1 else ROOT / "data/dictionaries/audit.json"
    rep = verify(ROOT)
    for line in rep.hard_errors():
        print("REGISTRY ERROR:", line)
    audit = audit_directory(raw)
    write_audit(audit, out)
    print(f"audited {audit['n_files']} tabular files under {raw}; wrote {out}")
    if audit["n_files"] == 0:
        print("no raw datasets present: scientific pipelines depending on them will report BLOCKED (nothing is fabricated)")
    return 1 if rep.hard_errors() else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
