"""Sliding/aligned windows with strict past-only construction."""
from __future__ import annotations

import numpy as np
import pandas as pd


def rolling_past_mean(df: pd.DataFrame, col: str, group: str, window: int) -> pd.Series:
    """Mean of the previous ``window`` days (the current day excluded)."""
    return df.groupby(group)[col].transform(lambda s: s.shift(1).rolling(window, min_periods=max(1, window // 2)).mean())
