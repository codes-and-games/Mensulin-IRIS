"""Next-day TDD supervised table (experiment M7).

Every feature of the row for calendar day t is computed ONLY from days strictly before t (``shift(1)`` on a complete
per-person calendar, so a missing day stays missing and is never bridged), except ``is_weekend`` which is a property of
the target day's date and is therefore known in advance. Nothing here uses cycle labels, and no value is imputed:
days that are excluded, have no recorded TDD, or have TDD <= 0 (HUPA-UCM: pump insulin not captured) become NaN history.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

WINDOW_DEFAULT = 7
MIN_HISTORY_DEFAULT = 3

#: scale-free candidate features (a data-quality audit in the experiment may drop any that are mostly missing in a dataset)
CANDIDATE_FEATURES = (
    "lag1_rel_tdd", "lag2_rel_tdd", "roll7_cv_tdd", "lag1_carb_rel", "lag1_carb_entries",
    "lag1_mean_glucose_mgdl", "lag1_tir_pct", "lag1_tbr_pct", "lag1_tar_pct", "is_weekend",
)
FEATURE_AVAILABILITY = {**{f: "past" for f in CANDIDATE_FEATURES}, "is_weekend": "known_at_prediction"}

_HIST = {"tdd_u": "tdd", "carb_g": "carb", "carb_entries": "carb_entries", "mean_glucose_mgdl": "glucose",
         "tir_pct": "tir", "tbr_pct": "tbr", "tar_pct": "tar"}


def tdd_validity(df: pd.DataFrame) -> tuple[pd.Series, dict]:
    """A day's TDD is usable only if the day is included, TDD is finite and TDD > 0 (0 = 'insulin not recorded', not physiology)."""
    inc = ~df["exclude_flag"].astype(bool)
    tdd = pd.to_numeric(df["tdd_u"], errors="coerce")
    finite = np.isfinite(tdd)
    pos = tdd > 0
    counts = {
        "person_days_total": int(len(df)),
        "excluded_by_ingest_flag": int((~inc).sum()),
        "included_tdd_missing": int((inc & ~finite).sum()),
        "included_tdd_zero_or_negative_treated_as_not_recorded": int((inc & finite & ~pos).sum()),
        "valid_tdd_days": int((inc & finite & pos).sum()),
    }
    return inc & finite & pos, counts


def build_next_day_table(df: pd.DataFrame, window: int = WINDOW_DEFAULT, min_history: int = MIN_HISTORY_DEFAULT) -> tuple[pd.DataFrame, dict]:
    """Return (eligible rows, counts). Eligible = valid target TDD, valid TDD on the previous calendar day, and >= ``min_history``
    valid TDD days among the previous ``window`` calendar days. Columns: dataset, person_id, date_local, y_tdd_u, lag1_tdd_u,
    lag2_tdd_u, roll7_mean_tdd_u (the persistence / trailing-mean baselines) and the CANDIDATE_FEATURES."""
    d = df.copy()
    d["_date"] = pd.to_datetime(d["date_local"])
    if d.duplicated(["person_id", "_date"]).any():
        raise ValueError("duplicate (person_id, date_local) rows in the person-day table")
    valid, counts = tdd_validity(d)
    inc = ~d["exclude_flag"].astype(bool)
    pieces = []
    for pid, g in d.groupby("person_id", sort=True):
        g = g.sort_values("_date")
        cal = pd.date_range(g["_date"].min(), g["_date"].max(), freq="D")
        m = pd.DataFrame(index=g["_date"])
        for col, name in _HIST.items():
            v = pd.to_numeric(g[col], errors="coerce")
            ok = valid.loc[g.index] if col == "tdd_u" else inc.loc[g.index]
            m[name] = v.where(ok).to_numpy()
        m = m.reindex(cal)
        past = m["tdd"].shift(1)
        roll = past.rolling(window, min_periods=min_history).mean()
        rstd = past.rolling(window, min_periods=min_history).std()
        cpast = m["carb"].shift(1)
        croll = cpast.rolling(window, min_periods=min_history).mean()
        o = pd.DataFrame(index=cal)
        o["dataset"] = g["dataset"].iloc[0]
        o["person_id"] = pid
        o["date_local"] = cal.strftime("%Y-%m-%d")
        o["y_tdd_u"] = m["tdd"]
        o["lag1_tdd_u"] = past
        o["lag2_tdd_u"] = m["tdd"].shift(2)
        o["roll7_mean_tdd_u"] = roll
        o["lag1_rel_tdd"] = past / roll
        o["lag2_rel_tdd"] = o["lag2_tdd_u"] / roll
        o["roll7_cv_tdd"] = rstd / roll
        o["lag1_carb_rel"] = (cpast / croll).where(croll > 0)
        o["lag1_carb_entries"] = m["carb_entries"].shift(1)
        o["lag1_mean_glucose_mgdl"] = m["glucose"].shift(1)
        o["lag1_tir_pct"] = m["tir"].shift(1)
        o["lag1_tbr_pct"] = m["tbr"].shift(1)
        o["lag1_tar_pct"] = m["tar"].shift(1)
        o["is_weekend"] = (cal.dayofweek >= 5).astype(float)
        pieces.append(o)
    full = pd.concat(pieces, ignore_index=True)
    elig = full["y_tdd_u"].notna() & full["lag1_tdd_u"].notna() & full["roll7_mean_tdd_u"].notna()
    counts["target_days_valid"] = int(full["y_tdd_u"].notna().sum())
    counts["eligible_next_day_rows"] = int(elig.sum())
    return full.loc[elig].reset_index(drop=True), counts


def filter_min_rows_per_person(tab: pd.DataFrame, min_rows: int) -> tuple[pd.DataFrame, dict[str, int]]:
    """Apply M7's minimum-rows-per-person rule and report every row/person removed."""
    if min_rows < 1:
        raise ValueError("min_rows must be >= 1")
    per = tab.groupby("person_id").size()
    small = per[per < min_rows].index
    n_rows_before = int(len(tab))
    n_people_before = int(tab["person_id"].nunique())
    n_rows_removed = int(per.loc[small].sum()) if len(small) else 0
    kept = tab[~tab["person_id"].isin(small)].reset_index(drop=True)
    counts = {
        "eligible_rows_before_min_rows_filter": n_rows_before,
        "eligible_people_before_min_rows_filter": n_people_before,
        "rows_removed_min_rows_per_person": n_rows_removed,
        "people_removed_min_rows_per_person": int(len(small)),
        "m7_rows_after_min_rows_per_person": int(len(kept)),
        "m7_people_after_min_rows_per_person": int(kept["person_id"].nunique()),
    }
    if n_rows_before - n_rows_removed != len(kept):
        raise AssertionError("M7 cohort filter row accounting failed")
    return kept, counts
