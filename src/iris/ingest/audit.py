"""Dataset audit: inspect REAL files before any loader is written (document 17).

Produces, per file: columns, dtypes, units hints, timestamp candidates and range, missingness, identifier
candidates, numeric ranges. Never assumes a column exists because a filename suggests it. The resulting
audit JSON is the evidence for the column mapping in configs/mappings/<dataset>.yaml.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

TABULAR = {".csv", ".tsv", ".txt", ".parquet", ".xlsx", ".xls"}


def _read(path: Path, nrows: int | None = None) -> pd.DataFrame:
    s = path.suffix.lower()
    if s == ".parquet":
        return pd.read_parquet(path)
    if s in (".xlsx", ".xls"):
        return pd.read_excel(path, nrows=nrows)
    sep = "\t" if s == ".tsv" else None
    return pd.read_csv(path, sep=sep, engine="python", nrows=nrows)


def audit_dataframe(df: pd.DataFrame, name: str) -> dict:
    cols = {}
    for c in df.columns:
        s = df[c]
        info = {"dtype": str(s.dtype), "n": int(len(s)), "n_missing": int(s.isna().sum()),
                "missing_frac": float(s.isna().mean()), "n_unique": int(s.nunique(dropna=True))}
        if pd.api.types.is_numeric_dtype(s) and s.notna().any():
            info.update(min=float(s.min()), max=float(s.max()), mean=float(s.mean()), median=float(s.median()))
        else:
            is_text = pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")       # format inference warnings are expected while auditing unknown files
                parsed = pd.to_datetime(s, errors="coerce", utc=False) if is_text else None
            if parsed is not None and parsed.notna().mean() > 0.9:
                info.update(timestamp_like=True, ts_min=str(parsed.min()), ts_max=str(parsed.max()),
                            tz_aware=bool(getattr(parsed.dt, "tz", None) is not None))
            elif is_text:
                info["examples"] = [str(v) for v in s.dropna().unique()[:3]]
        info["id_candidate"] = bool(info["n_unique"] <= 0.5 * len(s) and info["n_unique"] > 1
                                    and (pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s)))
        cols[str(c)] = info
    return {"file": name, "n_rows": int(len(df)), "n_cols": int(df.shape[1]), "columns": cols}


def audit_directory(root: str | Path, max_files: int = 500) -> dict:
    root = Path(root)
    files = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in TABULAR)[:max_files]
    report = {"root": str(root), "n_files": len(files), "files": []}
    for p in files:
        try:
            report["files"].append(audit_dataframe(_read(p), str(p.relative_to(root))))
        except Exception as exc:     # an unreadable file is a finding, not a silent skip
            report["files"].append({"file": str(p.relative_to(root)), "error": repr(exc)})
    return report


def write_audit(report: dict, out_json: str | Path) -> None:
    Path(out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(out_json).write_text(json.dumps(report, indent=2, default=str))
