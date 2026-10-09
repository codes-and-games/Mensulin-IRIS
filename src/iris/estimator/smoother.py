"""Rauch-Tung-Striebel smoother for the EKF, plus aggregation of smoothed ln S to a daily value with SD."""
from __future__ import annotations

import numpy as np

from .ekf import FilterResult
from .glucose_insulin_model import IDX, N_STATE


def rts_smooth(res: FilterResult):
    T = res.x_filt.shape[0]
    xs, Ps = res.x_filt.copy(), res.P_filt.copy()
    for t in range(T - 2, -1, -1):
        F = res.F[t + 1]
        C = res.P_filt[t] @ F.T @ np.linalg.pinv(res.P_pred[t + 1])
        xs[t] = res.x_filt[t] + C @ (xs[t + 1] - res.x_pred[t + 1])
        Ps[t] = res.P_filt[t] + C @ (Ps[t + 1] - res.P_pred[t + 1]) @ C.T
    return xs, Ps


def daily_sensitivity(xs: np.ndarray, Ps: np.ndarray, steps_per_day: int, relative_to_mean: bool = True):
    """Daily S = exp(mean smoothed lnS) (optionally divided by the person mean), with posterior SD (delta method)."""
    T = xs.shape[0]
    n_days = T // steps_per_day
    ln = xs[: n_days * steps_per_day, IDX["lnS"]].reshape(n_days, steps_per_day)
    var = Ps[: n_days * steps_per_day, IDX["lnS"], IDX["lnS"]].reshape(n_days, steps_per_day)
    m, v = ln.mean(axis=1), var.mean(axis=1)
    if relative_to_mean:
        m = m - m.mean()
    return np.exp(m), np.exp(m) * np.sqrt(v), m
