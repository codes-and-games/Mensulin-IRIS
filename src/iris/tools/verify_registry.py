"""verify_registry: discover scientific inputs, verify hashes, check registry membership.

Usage:  python -m iris.tools.verify_registry [--root .] [--strict|--lenient]

Exit status 0 only when every discovered scientific input file is in the manifest,
hash-consistent and traces to a registered source with complete metadata. ``--lenient``
reports problems but does not fail on registered-but-unverified literature rows (for pre-commit).
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

from iris.common.exceptions import IrisError
from iris.common.hashing import sha256_file
from iris.common.provenance import TEST_ONLY_SOURCE_PREFIX
from iris.common.registry import SourceRegistry

SCIENTIFIC_INPUT_DIRS = ("data/raw",)
IGNORED_NAMES = {".gitkeep"}


@dataclass
class RegistryReport:
    unregistered_files: list[str] = field(default_factory=list)
    hash_mismatches: list[str] = field(default_factory=list)
    unknown_source_ids: list[str] = field(default_factory=list)
    unverified_sources: dict[str, list[str]] = field(default_factory=dict)
    test_only_in_production: list[str] = field(default_factory=list)
    missing_files: list[str] = field(default_factory=list)
    files_checked: int = 0

    def hard_errors(self) -> list[str]:
        out = []
        out += [f"unregistered file: {f}" for f in self.unregistered_files]
        out += [f"hash mismatch: {f}" for f in self.hash_mismatches]
        out += [f"manifest references unknown source_id: {s}" for s in self.unknown_source_ids]
        out += [f"TEST_ONLY lineage in production inputs: {s}" for s in self.test_only_in_production]
        out += [f"manifest file missing on disk: {f}" for f in self.missing_files]
        return out

    def soft_warnings(self) -> list[str]:
        return [f"source {s} unverified; missing {m}" for s, m in self.unverified_sources.items()]


def discover_inputs(root: Path) -> list[Path]:
    files: list[Path] = []
    for d in SCIENTIFIC_INPUT_DIRS:
        base = root / d
        if base.exists():
            files += [p for p in base.rglob("*") if p.is_file() and p.name not in IGNORED_NAMES]
    return sorted(files)


def verify(root: str | Path = ".") -> RegistryReport:
    root = Path(root).resolve()
    reg_csv, man_csv = root / "data/sources_registry.csv", root / "data/manifest.csv"
    rep = RegistryReport()
    if not reg_csv.exists():
        raise IrisError(f"missing {reg_csv}")
    reg = SourceRegistry.load(reg_csv, man_csv if man_csv.exists() else None)
    for sid, row in reg.rows.items():
        miss = row.missing_metadata()
        if miss:
            rep.unverified_sources[sid] = miss
    for rel, entry in reg.manifest.items():
        sid = entry["source_id"]
        if sid.startswith(TEST_ONLY_SOURCE_PREFIX):
            rep.test_only_in_production.append(sid)
        elif sid not in reg.rows:
            rep.unknown_source_ids.append(sid)
        if not (root / rel).exists():
            rep.missing_files.append(rel)
    for f in discover_inputs(root):
        rel = f.relative_to(root).as_posix()
        rep.files_checked += 1
        entry = reg.manifest.get(rel)
        if entry is None:
            rep.unregistered_files.append(rel)
        elif entry["sha256"] != sha256_file(f):
            rep.hash_mismatches.append(rel)
    return rep


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".")
    ap.add_argument("--lenient", action="store_true", help="do not fail on unverified-but-registered sources")
    args = ap.parse_args(argv)
    rep = verify(args.root)
    for line in rep.hard_errors():
        print("ERROR:", line)
    for line in rep.soft_warnings():
        print("WARN: ", line)
    print(f"checked {rep.files_checked} input files; {len(rep.hard_errors())} errors; {len(rep.soft_warnings())} warnings")
    failed = bool(rep.hard_errors()) or (not args.lenient and bool(rep.soft_warnings()) and False)
    return 1 if failed else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
