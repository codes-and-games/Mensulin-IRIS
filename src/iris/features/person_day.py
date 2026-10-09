"""Construct validated person-day tables from harmonised event/daily data (no cycle fields invented)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from iris.common.schemas import PERSON_DAY, PHASES


def finalize_person_day(df: pd.DataFrame) -> pd.DataFrame:
    """Add schema-required nullable cycle columns when absent (NULL, never guessed) and validate."""
    out = df.copy()
    defaults = {"cycle_day": np.nan, "cycle_len": np.nan, "cycle_pos": np.nan, "phase": None, "pwd_flags": None,
                "exclude_flag": False, "exclude_reason": None, "device_type": None}
    for c, v in defaults.items():
        if c not in out:
            out[c] = v
    for c in ("tdd_u", "basal_u", "bolus_u", "carb_g", "carb_entries", "cgm_coverage", "mean_glucose_mgdl", "tir_pct", "tbr_pct", "tar_pct"):
        if c not in out:
            out[c] = np.nan
    out["exclude_flag"] = out["exclude_flag"].astype(bool)
    return PERSON_DAY.validate(out[[c.name for c in PERSON_DAY.columns]])


def apply_inclusion(df: pd.DataFrame, min_cgm_coverage: float, min_days: int, log=None) -> pd.DataFrame:
    """Flag (never silently delete) days below coverage and persons below min days; every exclusion is logged."""
    out = df.copy()
    low = out["cgm_coverage"].notna() & (out["cgm_coverage"] < min_cgm_coverage)
    out.loc[low, "exclude_flag"] = True
    out.loc[low & out["exclude_reason"].isna(), "exclude_reason"] = f"cgm_coverage<{min_cgm_coverage}"
    counts = out[~out["exclude_flag"]].groupby("person_id").size()
    short = set(counts[counts < min_days].index) | set(out["person_id"]) - set(counts.index)
    m = out["person_id"].isin(short) & ~out["exclude_flag"]
    out.loc[m, "exclude_flag"] = True
    out.loc[m, "exclude_reason"] = f"person_days<{min_days}"
    if log is not None:
        log.exclude(f"{int(low.sum())} person-days below coverage; {len(short)} persons below min days")
    return out
