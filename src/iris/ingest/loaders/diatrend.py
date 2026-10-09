"""Loader for diatrend. Requires configs/mappings/diatrend.yaml derived from an actual dataset audit (iris.ingest.audit)
and a verified registry entry for the dataset. No columns are assumed; without them this raises ScientificBlocker."""
from __future__ import annotations

from pathlib import Path

from iris.ingest.loaders.generic import load_with_mapping

MAPPING = Path(__file__).resolve().parents[4] / "configs" / "mappings" / "diatrend.yaml"


def load(path):
    return load_with_mapping(path, MAPPING)
