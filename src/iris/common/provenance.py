"""Evidence classes and the typed provenance object.

NO SOURCE, NO NUMBER: every scientific quantity carries a Provenance record whose
``evidence_class`` is one of the six IRIS classes. Lineage is preserved through
``parent_source_ids`` / ``transformation`` so a potency draw can be traced back to the
climate file it came from.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path

from .exceptions import EvidenceClassError, ProvenanceError, TestOnlyDataError


class EvidenceClass(str, Enum):
    PUBLISHED = "PUBLISHED"
    PUBLIC_DATASET = "PUBLIC_DATASET"
    OPEN_RESOURCE = "OPEN_RESOURCE"
    COMPUTED = "COMPUTED"
    SIMULATED = "SIMULATED"
    PROJECTED = "PROJECTED"


#: Classes that describe external, registry-backed inputs.
SOURCE_CLASSES = frozenset(
    {EvidenceClass.PUBLISHED, EvidenceClass.PUBLIC_DATASET, EvidenceClass.OPEN_RESOURCE}
)
#: Classes IRIS may assign to its own outputs. "MEASURED" is not an IRIS class.
OUTPUT_CLASSES = frozenset(
    {EvidenceClass.COMPUTED, EvidenceClass.SIMULATED, EvidenceClass.PROJECTED}
)
#: Marker for synthetic fixtures. Never a legal production source.
TEST_ONLY_SOURCE_PREFIX = "TEST_ONLY:"


def parse_evidence_class(value) -> EvidenceClass:
    if isinstance(value, EvidenceClass):
        return value
    try:
        return EvidenceClass(str(value).strip().upper())
    except ValueError as exc:
        raise EvidenceClassError(
            f"unknown evidence class {value!r}; allowed: {[c.value for c in EvidenceClass]} "
            "('MEASURED' is not an IRIS evidence class)"
        ) from exc


@dataclass(frozen=True)
class Provenance:
    evidence_class: EvidenceClass
    source_id: str
    citation_or_url: str = ""
    version: str = ""
    access_date: str = ""
    licence: str = ""
    sha256: str = ""
    transformation: str = ""
    parent_source_ids: tuple[str, ...] = ()
    generated_by: str = ""
    run_id: str = ""
    synthetic: bool = False  # True => TEST_ONLY fixture

    def __post_init__(self):
        object.__setattr__(self, "evidence_class", parse_evidence_class(self.evidence_class))
        object.__setattr__(self, "parent_source_ids", tuple(self.parent_source_ids))
        if not self.source_id:
            raise ProvenanceError("Provenance.source_id is required")
        if self.synthetic and not (self.source_id.startswith(TEST_ONLY_SOURCE_PREFIX) or any(
                s.startswith(TEST_ONLY_SOURCE_PREFIX) for s in self.parent_source_ids)):
            raise ProvenanceError("synthetic provenance must use a 'TEST_ONLY:' source_id or descend from one")

    # -- derivation ------------------------------------------------------------------
    def derive(self, *, evidence_class: EvidenceClass, source_id: str, transformation: str,
               generated_by: str, run_id: str = "", extra_parents: tuple[str, ...] = (),
               sha256: str = "") -> "Provenance":
        """Create child provenance preserving lineage (this record becomes a parent)."""
        return Provenance(
            evidence_class=evidence_class,
            source_id=source_id,
            transformation=transformation,
            parent_source_ids=tuple(dict.fromkeys((*self.parent_source_ids, self.source_id, *extra_parents))),
            generated_by=generated_by,
            run_id=run_id or self.run_id,
            sha256=sha256,
            synthetic=self.synthetic,
        )

    def to_dict(self) -> dict:
        d = asdict(self)
        d["evidence_class"] = self.evidence_class.value
        d["parent_source_ids"] = list(self.parent_source_ids)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Provenance":
        d = dict(d)
        d["parent_source_ids"] = tuple(d.get("parent_source_ids", ()))
        return cls(**d)


def write_provenance(path: str | Path, items: list[Provenance], extra: dict | None = None) -> None:
    payload = {"records": [p.to_dict() for p in items]}
    if extra:
        payload["run"] = extra
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True))


def read_provenance(path: str | Path) -> list[Provenance]:
    data = json.loads(Path(path).read_text())
    return [Provenance.from_dict(r) for r in data.get("records", [])]


def assert_production_safe(items: list[Provenance]) -> None:
    """Refuse any lineage that touches TEST_ONLY / synthetic data (production gate)."""
    for p in items:
        tainted = p.synthetic or p.source_id.startswith(TEST_ONLY_SOURCE_PREFIX) or any(
            s.startswith(TEST_ONLY_SOURCE_PREFIX) for s in p.parent_source_ids
        )
        if tainted:
            raise TestOnlyDataError(
                f"production pipeline received synthetic/TEST_ONLY lineage via source '{p.source_id}'"
            )
