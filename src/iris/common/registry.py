"""Source registry and manifest: enforcement of NO SOURCE, NO NUMBER.

``data/sources_registry.csv`` lists every external source. ``data/manifest.csv`` lists
file-level hashes of every file that scientific code reads. A scientific pipeline calls
``SourceRegistry.require(...)`` before using any input; unregistered or unverified inputs
raise ``UnregisteredSourceError``.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .exceptions import ProvenanceError, TestOnlyDataError, UnregisteredSourceError
from .hashing import sha256_file
from .provenance import SOURCE_CLASSES, TEST_ONLY_SOURCE_PREFIX, EvidenceClass, Provenance, parse_evidence_class

REGISTRY_FIELDS = ["source_id", "class", "title", "citation_or_url", "version", "access_date",
                   "licence", "sha256", "used_for", "verified_by"]
MANIFEST_FIELDS = ["path", "source_id", "sha256", "bytes", "read_only"]
#: Fields that must be non-empty for a source to count as *verified* (production-usable).
_REQUIRED_VERIFIED = ["source_id", "class", "title", "citation_or_url", "access_date", "licence", "verified_by"]


@dataclass(frozen=True)
class SourceRow:
    source_id: str
    cls: EvidenceClass
    title: str
    citation_or_url: str
    version: str
    access_date: str
    licence: str
    sha256: str
    used_for: str
    verified_by: str

    def missing_metadata(self) -> list[str]:
        d = {"source_id": self.source_id, "class": self.cls.value, "title": self.title,
             "citation_or_url": self.citation_or_url, "access_date": self.access_date,
             "licence": self.licence, "verified_by": self.verified_by}
        return [k for k in _REQUIRED_VERIFIED if not str(d[k]).strip()]

    def to_provenance(self, *, transformation: str = "", generated_by: str = "", run_id: str = "") -> Provenance:
        return Provenance(self.cls, self.source_id, self.citation_or_url, self.version, self.access_date,
                          self.licence, self.sha256, transformation, (), generated_by, run_id)


class SourceRegistry:
    def __init__(self, rows: dict[str, SourceRow], manifest: dict[str, dict] | None = None):
        self.rows = rows
        self.manifest = manifest or {}

    # -- loading -----------------------------------------------------------------
    @classmethod
    def load(cls, registry_csv: str | Path, manifest_csv: str | Path | None = None) -> "SourceRegistry":
        rows: dict[str, SourceRow] = {}
        with open(registry_csv, newline="") as fh:
            reader = csv.DictReader(fh)
            miss = [f for f in REGISTRY_FIELDS if f not in (reader.fieldnames or [])]
            if miss:
                raise ProvenanceError(f"registry missing columns {miss}")
            for r in reader:
                sid = r["source_id"].strip()
                if not sid:
                    continue
                if sid in rows:
                    raise ProvenanceError(f"duplicate source_id in registry: {sid}")
                c = parse_evidence_class(r["class"])
                if c not in SOURCE_CLASSES:
                    raise ProvenanceError(
                        f"registry row {sid}: class {c.value} is not a source class (PUBLISHED/PUBLIC_DATASET/OPEN_RESOURCE)")
                rows[sid] = SourceRow(sid, c, r["title"], r["citation_or_url"], r["version"], r["access_date"],
                                      r["licence"], r["sha256"], r["used_for"], r["verified_by"])
        manifest: dict[str, dict] = {}
        if manifest_csv and Path(manifest_csv).exists():
            with open(manifest_csv, newline="") as fh:
                for r in csv.DictReader(fh):
                    if r.get("path"):
                        manifest[r["path"]] = r
        return cls(rows, manifest)

    # -- enforcement -------------------------------------------------------------
    def require(self, source_id: str, *, allow_unverified: bool = False) -> SourceRow:
        """Return the registry row or raise. Test-only ids are always refused here."""
        if source_id.startswith(TEST_ONLY_SOURCE_PREFIX):
            raise TestOnlyDataError(f"'{source_id}' is TEST_ONLY and cannot be used by a production pipeline")
        row = self.rows.get(source_id)
        if row is None:
            raise UnregisteredSourceError(f"source '{source_id}' is not in the source registry")
        if not allow_unverified:
            missing = row.missing_metadata()
            if missing:
                raise UnregisteredSourceError(
                    f"source '{source_id}' is registered but unverified: missing {missing}")
        return row

    def require_file(self, path: str | Path, root: str | Path = ".") -> SourceRow:
        """Production file gate: file must be in the manifest, hash-consistent and its source verified."""
        rel = Path(path).resolve().relative_to(Path(root).resolve()).as_posix()   # manifest paths are POSIX on every OS
        entry = self.manifest.get(rel)
        if entry is None:
            raise UnregisteredSourceError(f"file '{rel}' is not listed in data/manifest.csv")
        row = self.require(entry["source_id"])
        actual = sha256_file(path)
        if actual != entry["sha256"]:
            raise ProvenanceError(f"hash mismatch for {rel}: manifest {entry['sha256'][:12]}…, actual {actual[:12]}…")
        return row


def append_registry_row(registry_csv: str | Path, row: dict) -> None:
    p = Path(registry_csv)
    exists = p.exists() and p.stat().st_size > 0
    with open(p, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=REGISTRY_FIELDS)
        if not exists:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in REGISTRY_FIELDS})
