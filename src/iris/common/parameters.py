"""Scientific parameter objects with explicit resolution status.

A parameter tagged [VERIFY], [TO EXTRACT], [ASSUMPTION] in the IRIS document is NEVER given a
guessed value. ``Parameter.get`` raises ``ScientificBlocker`` unless the parameter is usable
under the current run mode; only the computation that depends on it fails.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .exceptions import ScientificBlocker
from .provenance import EvidenceClass


class Status(str, Enum):
    RESOLVED = "RESOLVED"            # extracted and verified against a primary source
    PENDING_VERIFY = "PENDING_VERIFY"  # value present from the document, primary source not yet verified
    UNRESOLVED = "UNRESOLVED"        # [TO EXTRACT]: no value may be used
    ASSUMPTION = "ASSUMPTION"        # analyst-declared assumption (needs a sensitivity analysis)
    STRESS_TEST = "STRESS_TEST"      # analyst-defined probe, never evidence (Theta_S only)


class RunMode(str, Enum):
    PRODUCTION = "production"    # RESOLVED + registered/verified sources only
    PROVISIONAL = "provisional"  # PENDING_VERIFY allowed; every output stamped PROVISIONAL
    TEST = "test"                # synthetic fixtures allowed; never publishable


@dataclass(frozen=True)
class Parameter:
    name: str
    value: float | tuple | None
    unit: str
    status: Status
    source_id: str = ""
    evidence_class: EvidenceClass | None = None
    note: str = ""
    analysis_set: str = "E"  # 'E' (evidence-constrained) or 'S' (stress-test)

    def usable(self, mode: RunMode) -> bool:
        if self.value is None or self.status is Status.UNRESOLVED:
            return False
        if mode is RunMode.TEST:
            return True
        if self.status is Status.RESOLVED:
            return True
        if self.status in (Status.ASSUMPTION, Status.STRESS_TEST):
            return True  # declared and labelled; reported as such, never as evidence
        return mode is RunMode.PROVISIONAL  # PENDING_VERIFY

    def get(self, mode: RunMode):
        if not self.usable(mode):
            raise ScientificBlocker(
                self.name,
                f"status={self.status.value}, mode={mode.value}",
                needed=self.note or "extract/verify against the primary source and register it",
            )
        return self.value


def unresolved(name: str, unit: str, note: str) -> Parameter:
    return Parameter(name, None, unit, Status.UNRESOLVED, note=note)
