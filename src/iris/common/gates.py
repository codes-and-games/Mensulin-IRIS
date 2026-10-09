"""Production gates: refuse scientific computation whose inputs are unregistered, unverified or synthetic."""
from __future__ import annotations

from .exceptions import ScientificBlocker, UnregisteredSourceError
from .parameters import RunMode
from .provenance import TEST_ONLY_SOURCE_PREFIX
from .registry import SourceRegistry


def require_sources(registry: SourceRegistry, source_ids: list[str], mode: RunMode) -> list:
    """Return registry rows for ``source_ids`` or raise.

    production  : registered AND verified (complete metadata, verified_by), never TEST_ONLY
    provisional : registered (metadata may be incomplete) but never TEST_ONLY; callers stamp outputs PROVISIONAL
    test        : synthetic ids allowed
    """
    rows = []
    for sid in source_ids:
        if sid.startswith(TEST_ONLY_SOURCE_PREFIX):
            if mode is not RunMode.TEST:
                from .exceptions import TestOnlyDataError
                raise TestOnlyDataError(f"'{sid}' is TEST_ONLY and cannot enter a {mode.value} pipeline")
            continue
        rows.append(registry.require(sid, allow_unverified=(mode is not RunMode.PRODUCTION)))
    return rows


def blocked(parameter: str, why: str, needed: str = ""):
    """Raise a ScientificBlocker (helper for readability at call sites)."""
    raise ScientificBlocker(parameter, why, needed)
