"""python -m iris.tools.validate_person_day [path] [--out report.json]
Dataset-level quality-control report for a person-day table. Reports; never edits. Exit 1 on hard failures."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from iris.common.io import read_table
from iris.common.schemas import PERSON_DAY

ROOT = Path(__file__).resolve().parents[3]


def qc_report(df: pd.DataFrame) -> dict:
    hard, soft = [], []
    PERSON_DAY.validate(df[[c.name for c in PERSON_DAY.columns]])
    if df.duplicated(["dataset", "person_id", "date_local"]).any():
        hard.append("duplicate (dataset, person_id, date_local) rows")
    inc = df[~df["exclude_flag"]]
    per = inc.groupby("person_id").size()
    rep = {"n_rows": int(len(df)), "n_persons": int(df["person_id"].nunique()), "n_included_days": int(len(inc)),
           "persons_with_included_days": int(len(per)), "days_per_person": {"min": int(per.min()) if len(per) else 0,
           "median": float(per.median()) if len(per) else 0.0, "max": int(per.max()) if len(per) else 0},
           "cgm_coverage_median": float(inc["cgm_coverage"].median()) if len(inc) else None,
           "tdd_available_frac": float(inc["tdd_u"].notna().mean()) if len(inc) else None,
           "carb_available_frac": float(inc["carb_g"].notna().mean()) if len(inc) else None,
           "has_cycle_labels": bool(df["cycle_pos"].notna().any()), "has_isf": bool("isf_clinician" in df and df["isf_clinician"].notna().any()),
           "exclusion_reasons": df.loc[df["exclude_flag"], "exclude_reason"].value_counts().to_dict(),
           "by_dataset": df.groupby("dataset")["person_id"].nunique().to_dict()}
    if len(inc) and (inc["tdd_u"].dropna() > 300).any():
        soft.append("TDD > 300 U on included days: check units (rate vs amount)")
    if len(inc) and inc["tdd_u"].notna().sum() == 0:
        hard.append("no TDD on any included day: insulin roles/units mapped wrongly or insulin incomplete")
    if len(inc) and inc["mean_glucose_mgdl"].dropna().between(40, 400).mean() < 0.99:
        soft.append("mean glucose outside 40-400 mg/dL on >1% of days: check glucose units")
    if rep["n_persons"] < 10:
        soft.append("fewer than 10 persons: only pipeline/method checks are meaningful")
    rep["hard_failures"], rep["warnings"] = hard, soft
    return rep


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default=str(ROOT / "data/processed/person_day.parquet")); ap.add_argument("--out")
    a = ap.parse_args(argv)
    df, _ = read_table(a.path)
    rep = qc_report(df)
    txt = json.dumps(rep, indent=2, default=str)
    print(txt)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True); Path(a.out).write_text(txt)
    return 1 if rep["hard_failures"] else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
