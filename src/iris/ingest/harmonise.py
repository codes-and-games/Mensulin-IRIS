"""Harmonisation of audited public data to canonical units/time. Flags, never silently deletes."""
from __future__ import annotations

import numpy as np
import pandas as pd

from iris.common.exceptions import NumericalError
from iris.common.units import mmoll_to_mgdl

GLUCOSE_PLAUSIBLE_MGDL = (20.0, 600.0)   # sensor reporting range guard (flag only; source device ranges to be registered)


def to_utc_with_local(ts: pd.Series, tz: str) -> pd.DataFrame:
    """Parse timestamps as tz-aware (original timezone kept) and add UTC; DST transition rows are flagged."""
    local = pd.to_datetime(ts, errors="raise")
    if local.dt.tz is None:
        local = local.dt.tz_localize(tz, ambiguous="NaT", nonexistent="NaT")
    dst_issue = local.isna()
    utc = local.dt.tz_convert("UTC")
    return pd.DataFrame({"ts_local": local, "ts_utc": utc, "dst_ambiguous_flag": dst_issue})


def glucose_to_mgdl(values: pd.Series, unit: str) -> pd.Series:
    u = unit.lower().replace(" ", "")
    if u in ("mg/dl", "mgdl"):
        return values.astype(float)
    if u in ("mmol/l", "mmoll"):
        return pd.Series(mmoll_to_mgdl(values.astype(float)), index=values.index)
    raise NumericalError(f"unknown glucose unit {unit!r}")


def flag_glucose(g_mgdl: pd.Series, lo_hi=GLUCOSE_PLAUSIBLE_MGDL) -> pd.Series:
    """'range_flag' outside plausible sensor range, else 'ok'. Values retained."""
    return pd.Series(np.where((g_mgdl < lo_hi[0]) | (g_mgdl > lo_hi[1]), "range_flag", "ok"), index=g_mgdl.index)


def daily_aggregate(events: pd.DataFrame, person: str, ts_local: str, cols: dict, expected_per_day: int | None,
                    tz: str = "UTC") -> pd.DataFrame:
    """Aggregate to person-days. ``cols`` maps roles -> column names: glucose_mgdl, basal_u, bolus_u, carb_g.

    - TDD = basal + bolus where BOTH are recorded; otherwise NaN (never guess the missing part).
    - cgm_coverage = observed glucose samples / expected_per_day (None => NaN).
    - TIR/TBR/TAR use 70-180 mg/dL (consensus ranges; thresholds are parameters of THIS summary, not evidence).
    """
    e = events.copy()
    e["date_local"] = pd.to_datetime(e[ts_local]).dt.strftime("%Y-%m-%d")
    g = e.groupby([person, "date_local"])
    out = pd.DataFrame(index=g.size().index)
    if "glucose_mgdl" in cols:
        gl = e[cols["glucose_mgdl"]]
        out["mean_glucose_mgdl"] = g[cols["glucose_mgdl"]].mean()
        out["cgm_coverage"] = g[cols["glucose_mgdl"]].count() / expected_per_day if expected_per_day else np.nan
        e["_tir"], e["_tbr"], e["_tar"] = gl.between(70, 180), gl < 70, gl > 180
        for k in ("tir", "tbr", "tar"):
            out[f"{k}_pct"] = e.groupby([person, "date_local"])[f"_{k}"].mean() * 100.0
    for role in ("basal_u", "bolus_u", "carb_g"):
        if role in cols:
            out[role] = g[cols[role]].sum(min_count=1)
    if {"basal_u", "bolus_u"} <= set(out.columns):
        out["tdd_u"] = out["basal_u"] + out["bolus_u"]
    return out.reset_index().rename(columns={person: "person_id"})
