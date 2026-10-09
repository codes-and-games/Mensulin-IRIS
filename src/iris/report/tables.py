"""Table export from STORED results: adds the evidence class column; no number is typed by hand."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from iris.common.io import read_sidecar_meta, read_table


def load_run_table(run_dir: str | Path, name: str):
    df, prov = read_table(Path(run_dir) / "tables" / f"{name}.parquet")
    meta = read_sidecar_meta(Path(run_dir) / "tables" / f"{name}.parquet")
    return df, prov, meta


def export_table(run_dir: str | Path, name: str, out_dir: str | Path, fmt: str = "csv") -> Path:
    df, prov, _ = load_run_table(run_dir, name)
    out = df.copy()
    if "evidence_class" not in out.columns:
        out["evidence_class"] = "|".join(sorted({p.evidence_class.value for p in prov}))
    out["run_id"] = Path(run_dir).name
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    path = Path(out_dir) / f"{name}.{fmt}"
    out.to_csv(path, index=False) if fmt == "csv" else path.write_text(out.to_markdown(index=False) if hasattr(out, "to_markdown") else out.to_string(index=False))
    return path
