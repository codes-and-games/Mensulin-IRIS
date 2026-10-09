"""Mapping-driven loader. A mapping (configs/mappings/<dataset>.yaml) must exist and cite the audit that justified it;
every mapped column is verified to exist in the file. Datasets without an audited mapping cannot be loaded."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from iris.common.exceptions import ScientificBlocker
from iris.common.io import load_yaml
from iris.ingest.audit import _read


def load_with_mapping(path: str | Path, mapping_path: str | Path) -> tuple[pd.DataFrame, dict]:
    mp = Path(mapping_path)
    if not mp.exists():
        raise ScientificBlocker("column_mapping", f"no audited mapping at {mp}",
                                "run `make audit` on the real files and write the mapping from its output")
    m = load_yaml(mp)
    if m.get("audit_status") != "AUDITED" or not m.get("audit_file"):
        raise ScientificBlocker("column_mapping", "mapping not marked AUDITED with an audit_file reference",
                                "complete the audit and set audit_status: AUDITED")
    df = _read(Path(path))
    missing = [c for c in m["columns"].values() if c not in df.columns]
    if missing:
        raise ScientificBlocker("column_mapping", f"mapped columns not present in file: {missing}",
                                "mapping must be derived from the actual audit; never assume columns from filenames")
    return df, m
