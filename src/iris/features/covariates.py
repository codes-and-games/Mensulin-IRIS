"""Pre-specified covariates only (cycle position, person baseline, device, contraception flag, lagged context)."""
from __future__ import annotations

import pandas as pd

from .leakage_guard import lag_features

PRESPECIFIED = ("cycle_pos", "device_type", "contraception_flag")


def build_design(df: pd.DataFrame, lagged: list[str], group: str = "person_id", time: str = "date_local") -> pd.DataFrame:
    return lag_features(df, lagged, group, time, lags=1)
