"""Exception hierarchy for IRIS.

The hierarchy encodes the three failure categories used across the project:
engineering errors, missing scientific evidence (ScientificBlocker) and
violations of the evidence/provenance rules.
"""
from __future__ import annotations


class IrisError(Exception):
    """Base class for all IRIS errors."""


class SchemaError(IrisError):
    """A table or record violates its declared schema."""


class ProvenanceError(IrisError):
    """Provenance is missing, malformed, or breaks the lineage chain."""


class UnregisteredSourceError(ProvenanceError):
    """A scientific input is not present in the source registry (NO SOURCE, NO NUMBER)."""


class TestOnlyDataError(ProvenanceError):
    """Synthetic / TEST_ONLY data reached a production scientific pipeline."""

    __test__ = False  # not a pytest class


class EvidenceClassError(ProvenanceError):
    """An evidence class is missing, unknown, or inconsistent with how a value was produced."""


class ScientificBlocker(IrisError):
    """A required scientific input is unresolved ([VERIFY], [TO EXTRACT], [ASSUMPTION] ...).

    Raised ONLY by computations that genuinely depend on the missing value.
    Never caught and replaced by a default: IRIS must not invent evidence.
    """

    def __init__(self, parameter: str, reason: str, needed: str = ""):
        self.parameter = parameter
        self.reason = reason
        self.needed = needed
        msg = f"SCIENTIFIC BLOCKER: parameter '{parameter}' is unresolved ({reason})."
        if needed:
            msg += f" Needed: {needed}"
        super().__init__(msg)


class ClaimsViolation(IrisError):
    """Generated text contains prohibited or misleading scientific wording."""


class NumericalError(IrisError):
    """Invalid numerical input (units, overflow, impossible parameter range)."""


class LeakageError(IrisError):
    """A model or split would leak future or same-subject information."""


class CircularityError(IrisError):
    """Requirement was constructed as rho = 1/S (or an equivalent degenerate balance). Prohibited
    outside the explicit circularity control (ablation A4)."""
