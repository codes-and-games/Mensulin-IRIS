"""Scripted retrieval of registered sources where the licence permits. Downloads are hashed and appended to the
manifest; raw files are made read-only. A source whose address/version/licence is unresolved is REFUSED.

Usage: python -m iris.tools.fetch_sources [--root .] [--ids S27,S29]
"""
from __future__ import annotations

import argparse
import csv
import os
import stat
import sys
import urllib.request
from pathlib import Path

from iris.common.hashing import sha256_file
from iris.common.io import load_yaml
from iris.common.registry import MANIFEST_FIELDS

ALLOWED_SCHEMES = ("https://",)


def fetch_one(source_id: str, url: str, dest: Path, timeout: int = 60) -> str:
    if not url.startswith(ALLOWED_SCHEMES):
        raise ValueError("only https sources are fetched")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=timeout) as r, open(dest, "wb") as fh:   # nosec - allow-listed by config
        fh.write(r.read())
    os.chmod(dest, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)       # raw files are read-only
    return sha256_file(dest)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--ids", default="")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    cfg = load_yaml(root / "configs/thermal/climate_sources.yaml")["sources"]
    want = [s for s in a.ids.split(",") if s] or list(cfg)
    blocked = []
    for sid in want:
        spec = cfg.get(sid)
        if not spec or not spec.get("url") or spec.get("status") == "UNRESOLVED":
            blocked.append(sid); continue
        digest = fetch_one(sid, spec["url"], root / "data/raw/climate" / f"{sid}.dat")
        with open(root / "data/manifest.csv", "a", newline="") as fh:
            csv.writer(fh).writerow([f"data/raw/climate/{sid}.dat", sid, digest, (root / f'data/raw/climate/{sid}.dat').stat().st_size, True])
        print(f"fetched {sid} sha256={digest[:12]}…; verify licence/version in the registry before use")
    if blocked:
        print("BLOCKED (address/version/licence unresolved, nothing fetched):", ", ".join(blocked))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
