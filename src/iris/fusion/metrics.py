"""Fusion metrics: exceedance, positive-part means, TCI/CI with algebraic baselines, heterogeneity penalty.

All outputs are PROJECTED. Thresholds come from configuration (never hard-coded here).
"""
from __future__ import annotations

import numpy as np

from iris.common.exceptions import NumericalError


def exceedance(x: np.ndarray, tau: float) -> tuple[float, float]:
    """(Pr(X > tau), Monte Carlo SE sqrt(p(1-p)/N))."""
    x = np.asarray(x, float)
    p = float((x > tau).mean())
    return p, float(np.sqrt(p * (1 - p) / x.size))


def mean_positive_part(x: np.ndarray) -> tuple[float, float]:
    """(M+ = E[max(X,0)], standard error)."""
    y = np.maximum(np.asarray(x, float), 0.0)
    return float(y.mean()), float(y.std(ddof=1) / np.sqrt(y.size))


def tci(exceed: np.ndarray, swing_rank: np.ndarray, top_fraction: float = 0.2) -> float:
    """Tail concentration index: share of exceedances from the top ``top_fraction`` by swing / top_fraction.
    NaN when there are no exceedances (undefined, omitted)."""
    e = np.asarray(exceed, bool)
    if not e.any():
        return float("nan")
    top = np.asarray(swing_rank) > (1.0 - top_fraction)
    return float((e & top).sum() / e.sum() / top_fraction)


def concentration_index(exceed: np.ndarray, swing: np.ndarray) -> float:
    """CI = 2 * (area between the diagonal and the Lorenz-type curve) for exceedances ordered by increasing swing."""
    e = np.asarray(exceed, float)
    if e.sum() == 0:
        return float("nan")
    order = np.argsort(np.asarray(swing), kind="stable")
    c = np.concatenate([[0.0], np.cumsum(e[order]) / e.sum()])
    x = np.linspace(0.0, 1.0, c.size)
    area_under = float(np.sum((c[1:] + c[:-1]) * np.diff(x)) / 2.0)
    return 1.0 - 2.0 * area_under


def algebraic_baseline(delta_u_fn, ell: np.ndarray, swing: np.ndarray, swing_rank: np.ndarray, tau: float,
                       rng: np.random.Generator, n_perm: int = 20, top_fraction: float = 0.2) -> dict:
    """TCI_alg / CI_alg: concentration when loss is independent of ALL biology (permuted across individuals).

    ``delta_u_fn(ell_vector)`` returns the high-phase shortfall vector for a given per-individual loss vector.
    """
    t_vals, c_vals = [], []
    for _ in range(n_perm):
        d = delta_u_fn(rng.permutation(ell))
        e = d > tau
        t_vals.append(tci(e, swing_rank, top_fraction)); c_vals.append(concentration_index(e, swing))
    return {"tci_alg": float(np.nanmean(t_vals)) if not np.all(np.isnan(t_vals)) else float("nan"),
            "ci_alg": float(np.nanmean(c_vals)) if not np.all(np.isnan(c_vals)) else float("nan"),
            "tci_alg_sd": float(np.nanstd(t_vals)) if not np.all(np.isnan(t_vals)) else float("nan")}


def heterogeneity_penalty(delta_het: np.ndarray, delta_mean: np.ndarray, tau: float) -> dict:
    """HP(tau) = Pr_het(du > tau)/Pr_mean(du > tau); computed from DIRECT tail probabilities, never means."""
    p_het, se_het = exceedance(delta_het, tau)
    p_mean, se_mean = exceedance(delta_mean, tau)
    if p_mean == 0.0:
        hp = float("inf") if p_het > 0 else float("nan")   # undefined ratio is flagged, not hidden
    else:
        hp = p_het / p_mean
    return {"hp": hp, "p_het": p_het, "p_mean": p_mean, "se_het": se_het, "se_mean": se_mean,
            "denominator_zero": bool(p_mean == 0.0)}


def batch_se(values_by_batch: np.ndarray) -> float:
    v = np.asarray(values_by_batch, float)
    v = v[np.isfinite(v)]
    return float(v.std(ddof=1) / np.sqrt(v.size)) if v.size > 1 else float("nan")


def swing_band(rank: np.ndarray, edges=(0.25, 0.75, 0.90)) -> np.ndarray:
    """Band index 0..3: <25th, 25-75, 75-90, >90 percentile of swing."""
    return np.digitize(np.asarray(rank), edges)


def joint_vs_product(exceed_a: np.ndarray, exceed_b: np.ndarray) -> dict:
    """Secondary compounding diagnostic: joint exceedance vs product of marginals."""
    a, b = np.asarray(exceed_a, bool), np.asarray(exceed_b, bool)
    pj, pa, pb = float((a & b).mean()), float(a.mean()), float(b.mean())
    return {"joint": pj, "product": pa * pb, "excess": pj - pa * pb}
