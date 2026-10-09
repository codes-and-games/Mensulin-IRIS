"""Caption generation. REFUSES when provenance is missing; stamps non-production runs; lints wording."""
from __future__ import annotations

from dataclasses import dataclass

from iris.common.exceptions import ProvenanceError
from iris.common.provenance import Provenance
from iris.tools.claims_lint import assert_clean

STAMPS = {"production": "", "provisional": "PROVISIONAL (inputs not fully verified) - not a production result", "test": "TEST-ONLY synthetic fixtures - not a scientific result"}


@dataclass(frozen=True)
class FigureProvenance:
    run_id: str
    run_mode: str
    evidence_classes: tuple
    source_ids: tuple
    uncertainty: str
    experiment: str

    def validate(self) -> None:
        missing = [k for k, v in (("run_id", self.run_id), ("evidence_classes", self.evidence_classes), ("source_ids", self.source_ids),
                                  ("uncertainty", self.uncertainty), ("run_mode", self.run_mode)) if not v]
        if missing:
            raise ProvenanceError(f"cannot caption: provenance missing {missing}")


def from_records(records: list[Provenance], run_id: str, run_mode: str, uncertainty: str, experiment: str) -> FigureProvenance:
    if not records:
        raise ProvenanceError("cannot caption: no provenance records")
    src = sorted({s for r in records for s in (*r.parent_source_ids, r.source_id)})
    ec = sorted({r.evidence_class.value for r in records})
    fp = FigureProvenance(run_id, run_mode, tuple(ec), tuple(src), uncertainty, experiment)
    fp.validate()
    return fp


def make_caption(title: str, description: str, fp: FigureProvenance, publication: bool = False) -> str:
    fp.validate()
    if publication and fp.run_mode != "production":
        raise ProvenanceError(f"publication figure refused: run mode is '{fp.run_mode}', not 'production'")
    parts = [f"{title}. {description}",
             f"Evidence class: {', '.join(fp.evidence_classes)}. Run: {fp.run_id} ({fp.experiment}). Sources: {', '.join(fp.source_ids)}. Uncertainty: {fp.uncertainty}."]
    if STAMPS[fp.run_mode]:
        parts.append(STAMPS[fp.run_mode] + ".")
    text = " ".join(parts)
    assert_clean(text, f"caption of {title}")
    return text
