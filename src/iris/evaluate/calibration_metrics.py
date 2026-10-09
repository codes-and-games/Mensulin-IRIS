"""Interval coverage, CRPS (Gaussian/ensemble), PIT and amplitude/phase recovery metrics."""
from __future__ import annotations

import numpy as np
from scipy import stats


def interval_coverage(y, lo, hi) -> float:
    y, lo, hi = (np.asarray(v, float) for v in (y, lo, hi))
    return float(np.mean((y >= lo) & (y <= hi)))


def gaussian_coverage(y, mu, sd, level: float = 0.95) -> float:
    z = stats.norm.ppf(0.5 + level / 2)
    return interval_coverage(y, np.asarray(mu) - z * np.asarray(sd), np.asarray(mu) + z * np.asarray(sd))


def crps_ensemble(y: float, ens: np.ndarray) -> float:
    e = np.asarray(ens, float)
    return float(np.mean(np.abs(e - y)) - 0.5 * np.mean(np.abs(e[:, None] - e[None, :])))


def amplitude_phase(values: np.ndarray, period_days: float) -> tuple[float, float, float]:
    """Fit v_d = c + a cos(2 pi d/P) + b sin(2 pi d/P); return (amplitude, phase_rad, F-test p-value for harmonic terms)."""
    v = np.asarray(values, float); d = np.arange(len(v))
    X = np.column_stack([np.ones_like(d, float), np.cos(2 * np.pi * d / period_days), np.sin(2 * np.pi * d / period_days)])
    beta, rss, *_ = np.linalg.lstsq(X, v, rcond=None)
    rss1 = float(np.sum((v - X @ beta) ** 2)); rss0 = float(np.sum((v - v.mean()) ** 2))
    df2 = len(v) - 3
    f = ((rss0 - rss1) / 2) / (rss1 / df2) if rss1 > 0 else np.inf
    p = float(stats.f.sf(f, 2, df2))
    return float(np.hypot(beta[1], beta[2])), float(np.arctan2(beta[2], beta[1])), p


def phase_error(est: float, true: float) -> float:
    return float((est - true + np.pi) % (2 * np.pi) - np.pi)
