"""python scripts/verify_run_dir.py results/runs/<run_id> [more run dirs]
Checks an imported run directory (for example one downloaded from Kaggle): required files exist, every table's sha256 matches its
provenance sidecar, no TEST_ONLY/synthetic lineage and no provisional/test stamp in a directory you intend to cite as production.
Exit code 0 only if every check passes. Reads only."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def check(run: Path) -> list[str]:
    bad = []
    for f in ("config.yaml", "provenance.json", "log.txt"):
        if not (run / f).exists():
            bad.append(f"missing {f}")
    for t in sorted((run / "tables").glob("*.parquet")) if (run / "tables").exists() else []:
        side = Path(str(t) + ".provenance.json")
        if not side.exists():
            bad.append(f"{t.name}: provenance sidecar missing"); continue
        meta = json.loads(side.read_text())
        if meta.get("run", {}).get("file_sha256") != sha(t):
            bad.append(f"{t.name}: sha256 differs from sidecar (file changed after the run)")
        for r in meta.get("records", []):
            if r.get("synthetic") or str(r.get("source_id", "")).startswith("TEST_ONLY"):
                bad.append(f"{t.name}: synthetic/TEST_ONLY lineage ({r.get('source_id')})")
    log = (run / "log.txt").read_text(errors="ignore") if (run / "log.txt").exists() else ""
    for word in ("mode=test", "mode=provisional", "smoke"):
        if word in log.lower().replace(" ", ""):
            bad.append(f"log mentions {word!r}: not citable as production evidence")
    return bad


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    rc = 0
    for a in sys.argv[1:]:
        problems = check(Path(a))
        print(("OK   " if not problems else "FAIL ") + a)
        for p in problems:
            print("   -", p)
        rc |= bool(problems)
    sys.exit(rc)
