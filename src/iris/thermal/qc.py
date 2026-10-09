"""Quality control and gap handling for climate series. Nothing is deleted: rules write flags."""
from __future__ import annotations

import numpy as np
import pandas as pd

from iris.common.exceptions import NumericalError


def qc_series(t_c: np.ndarray, *, lo_c: float, hi_c: float, fill_values=(-9999.0, -999.0, 9999.0)):
    """Return (flags, mask_missing). Range limits are caller-supplied (location-plausibility from registered source)."""
    t = np.asarray(t_c, float)
    flags = np.full(t.shape, "ok", dtype=object)
    fill = np.isin(t, fill_values) | ~np.isfinite(t)
    flags[(t < lo_c) | (t > hi_c)] = "range_flag"
    flags[fill] = "fill_value"
    return flags, fill


def fill_gaps(t_c: np.ndarray, missing: np.ndarray, step_h: float, gmax_h: float, long_gap: str = "optimistic"):
    """Short gaps (<= gmax_h) linearly interpolated; long gaps filled per ``long_gap`` bracket.

    long_gap: 'missing' (leave NaN), 'optimistic' (carry the lower neighbour), 'pessimistic' (carry the higher).
    Returns (filled, imputed_flag, flags). The imputed fraction must always be reported.
    """
    if long_gap not in ("missing", "optimistic", "pessimistic"):
        raise NumericalError("long_gap must be missing|optimistic|pessimistic")
    t = np.asarray(t_c, float).copy()
    miss = np.asarray(missing, bool).copy()
    flags = np.full(t.shape, "ok", dtype=object)
    imputed = np.zeros(t.shape, bool)
    n = len(t)
    i = 0
    while i < n:
        if not miss[i]:
            i += 1
            continue
        j = i
        while j < n and miss[j]:
            j += 1
        gap_h = (j - i) * step_h
        left = t[i - 1] if i > 0 else np.nan
        right = t[j] if j < n else np.nan
        if gap_h <= gmax_h and np.isfinite(left) and np.isfinite(right):
            t[i:j] = np.linspace(left, right, j - i + 2)[1:-1]
            flags[i:j] = "gap_interpolated"; imputed[i:j] = True
        else:
            flags[i:j] = "gap_missing"
            if long_gap != "missing":
                nb = [v for v in (left, right) if np.isfinite(v)]
                if nb:
                    t[i:j] = min(nb) if long_gap == "optimistic" else max(nb)
                    imputed[i:j] = True
            else:
                t[i:j] = np.nan
        i = j
    return t, imputed, flags
