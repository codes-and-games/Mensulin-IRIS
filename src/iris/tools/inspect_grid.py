"""python -m iris.tools.inspect_grid <file-or-dir> <timestamp_column> [--glob "*.csv"]
Reports the observed sampling interval per file (median / most common spacing in minutes, share of gaps > 2x the median) so the
mapping's ``grid_minutes`` is read from the data, not guessed. Reads only; never edits a file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from iris.ingest.audit import _read


def spacing(ts: pd.Series) -> dict:
    t = pd.to_datetime(ts, errors="coerce").dropna().sort_values()
    d = t.diff().dropna().dt.total_seconds() / 60.0
    if d.empty:
        return {"n": int(len(t)), "median_min": None, "mode_min": None, "gap_share": None}
    med = float(d.median())
    return {"n": int(len(t)), "median_min": med, "mode_min": float(d.mode().iloc[0]), "gap_share": float((d > 2 * med).mean())}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path"); ap.add_argument("column"); ap.add_argument("--glob", default="*.csv")
    a = ap.parse_args(argv)
    p = Path(a.path)
    files = [p] if p.is_file() else sorted(p.rglob(a.glob))
    if not files:
        print("no files matched"); return 2
    meds = []
    for f in files:
        try:
            r = spacing(_read(f)[a.column])
        except KeyError:
            print(f"{f}: column {a.column!r} not found"); continue
        meds.append(r["median_min"])
        print(f"{f}: n={r['n']} median={r['median_min']} min, most common={r['mode_min']} min, gaps>2x median={r['gap_share']}")
    vals = sorted({m for m in meds if m is not None})
    print("distinct median spacings (minutes):", vals, "-> grid_minutes must equal the native spacing and divide 1440")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
