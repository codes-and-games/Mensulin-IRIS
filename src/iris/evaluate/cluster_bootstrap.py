"""Clustered (by person) bootstrap: resample PEOPLE, never days (document 10.3)."""
from __future__ import annotations

import numpy as np


def cluster_bootstrap_skill(groups, abs_err_model, abs_err_base, rng: np.random.Generator, B: int = 2000, alpha: float = 0.05) -> dict:
    """Pooled-MAE skill = 1 - MAE_model / MAE_baseline with a percentile CI from resampling persons with replacement.
    Positive skill = the model has lower pooled absolute error than the baseline on the same rows."""
    g = np.asarray(groups)
    em, eb = np.asarray(abs_err_model, float), np.asarray(abs_err_base, float)
    ok = np.isfinite(em) & np.isfinite(eb)
    g, em, eb = g[ok], em[ok], eb[ok]
    ids, inv = np.unique(g, return_inverse=True)
    sm, sb = np.bincount(inv, weights=em), np.bincount(inv, weights=eb)
    k = len(ids)
    point = float(1.0 - sm.sum() / sb.sum())
    idx = rng.integers(0, k, size=(B, k))
    boot = 1.0 - sm[idx].sum(axis=1) / sb[idx].sum(axis=1)
    lo, hi = np.quantile(boot, [alpha / 2, 1 - alpha / 2])
    return {"skill": point, "ci_lo": float(lo), "ci_hi": float(hi), "n_people": int(k), "B": int(B)}
