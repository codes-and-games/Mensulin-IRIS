"""Parquet/CSV/YAML I/O with schema validation and provenance sidecars."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

from .hashing import sha256_file
from .provenance import Provenance, read_provenance, write_provenance
from .schemas import TableSchema


def load_yaml(path: str | Path) -> dict:
    with open(path) as fh:
        data = yaml.safe_load(fh)
    return {} if data is None else data


def dump_yaml(obj: dict, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as fh:
        yaml.safe_dump(obj, fh, sort_keys=True)


def sidecar_path(path: str | Path) -> Path:
    p = Path(path)
    return p.with_name(p.name + ".provenance.json")


def write_table(df: pd.DataFrame, path: str | Path, prov: list[Provenance],
                schema: TableSchema | None = None, extra: dict | None = None) -> str:
    """Write parquet (or csv) + provenance sidecar; refuses empty provenance."""
    if not prov:
        raise ValueError("write_table requires at least one Provenance record (NO SOURCE, NO NUMBER)")
    if schema is not None:
        schema.validate(df)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.suffix == ".parquet":
        df.to_parquet(p, index=False)
    else:
        df.to_csv(p, index=False)
    digest = sha256_file(p)
    write_provenance(sidecar_path(p), prov, extra={"file_sha256": digest, "rows": int(len(df)), **(extra or {})})
    return digest


def read_sidecar_meta(path: str | Path) -> dict:
    sc = sidecar_path(path)
    return json.loads(sc.read_text()).get("run", {}) if sc.exists() else {}


def read_table(path: str | Path, schema: TableSchema | None = None, require_provenance: bool = True):
    p = Path(path)
    sc = sidecar_path(p)
    prov = []
    if require_provenance:
        if not sc.exists():
            from .exceptions import ProvenanceError
            raise ProvenanceError(f"missing provenance sidecar for {p}")
        meta = json.loads(sc.read_text())
        prov = read_provenance(sc)
        if meta.get("run", {}).get("file_sha256") != sha256_file(p):
            from .exceptions import ProvenanceError
            raise ProvenanceError(f"hash mismatch: {p} changed since its provenance was written")
    df = pd.read_parquet(p) if p.suffix == ".parquet" else pd.read_csv(p)
    if schema is not None:
        schema.validate(df)
    return df, prov
