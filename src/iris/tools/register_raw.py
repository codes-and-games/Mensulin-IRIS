"""python -m iris.tools.register_raw <dataset> <source_id> [--root .]
Hash every file under data/raw/<dataset>/ and append it to data/manifest.csv (POSIX paths). Existing entries must match
(a changed file is an ERROR, never silently re-hashed). Files are made read-only. Also prints the dataset-level SHA-256 digest
(sha256 of the sorted per-file digests) to record in the registry `sha256` column."""
from __future__ import annotations

import argparse
import csv
import hashlib
import os
import stat
import sys
from pathlib import Path

from iris.common.hashing import sha256_file
from iris.common.registry import MANIFEST_FIELDS

ROOT = Path(__file__).resolve().parents[3]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset"); ap.add_argument("source_id"); ap.add_argument("--root", default=str(ROOT))
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    base = root / "data/raw" / a.dataset
    files = sorted(p for p in base.rglob("*") if p.is_file() and p.name != ".gitkeep")
    if not files:
        print(f"no files under {base}"); return 2
    man = root / "data/manifest.csv"
    existing = {}
    if man.exists():
        with open(man, newline="") as fh:
            existing = {r["path"]: r for r in csv.DictReader(fh) if r.get("path")}
    new_rows, digests, bad = [], [], []
    for f in files:
        rel = f.relative_to(root).as_posix(); h = sha256_file(f); digests.append(h)
        e = existing.get(rel)
        if e is None:
            new_rows.append([rel, a.source_id, h, f.stat().st_size, True])
        elif e["sha256"] != h:
            bad.append(rel)
        elif e["source_id"] != a.source_id:
            bad.append(f"{rel} (registered under {e['source_id']})")
    if bad:
        print("ERROR: manifest mismatch (file changed or wrong source id):"); [print("  ", b) for b in bad]; return 1
    new = not man.exists() or man.stat().st_size == 0
    with open(man, "a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(MANIFEST_FIELDS)
        w.writerows(new_rows)
    for f in files:
        os.chmod(f, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    ds = hashlib.sha256("".join(sorted(digests)).encode()).hexdigest()
    print(f"registered {len(new_rows)} new file(s); {len(files) - len(new_rows)} already registered.")
    print(f"dataset digest (record in data/sources_registry.csv column sha256 for {a.source_id}): {ds}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
