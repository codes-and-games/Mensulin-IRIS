"""Context mapping: outdoor temperature -> air temperature next to the vial (contexts C0..C5).

Coefficients are never defaulted. C1 can be FIT on a held-out-by-building split of a registered
thermal-comfort table (E2/V18); published-regression coefficients enter via ``ContextMapping``.
Residuals are sampled as AR(1) noise (autocorrelation matters for heat spikes).
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd

from iris.common.exceptions import NumericalError


@dataclass(frozen=True)
class ContextMapping:
    context_id: str
    model: str            # 'linear_running_mean' | 'identity_offset' | 'damped_swing'
    coefficients: dict
    residual_sd: float
    residual_autocorr: float
    source_ids: tuple
    validation: dict

    def to_json_dict(self) -> dict:
        d = asdict(self); d["source_ids"] = list(self.source_ids); return d


def ar1_noise(rng: np.random.Generator, n: int, sd: float, rho: float) -> np.ndarray:
    """Stationary AR(1) with marginal SD ``sd`` and lag-1 autocorrelation ``rho``."""
    if not (-1 < rho < 1) or sd < 0:
        raise NumericalError("need |rho|<1 and sd>=0")
    e = np.empty(n)
    e[0] = rng.standard_normal() * sd
    innov = sd * np.sqrt(1 - rho ** 2)
    z = rng.standard_normal(n)
    for i in range(1, n):
        e[i] = rho * e[i - 1] + innov * z[i]
    return e


def map_damped_swing(t_out, samples_per_day: int, t_in_mean_c, gamma: float, residual=None):
    """C1 form: T_air = T_in_mean + gamma (T_out - daily mean of T_out), 0 <= gamma <= 1 (doc 12.7)."""
    if not 0.0 <= gamma <= 1.0:
        raise NumericalError("gamma must lie in [0, 1]")
    t = np.asarray(t_out, float)
    if t.size % samples_per_day:
        raise NumericalError("series must contain whole days")
    daily_mean = t.reshape(-1, samples_per_day).mean(axis=1)
    dm = np.repeat(daily_mean, samples_per_day)
    tin = np.asarray(t_in_mean_c, float)
    tin = np.repeat(tin, samples_per_day) if tin.ndim == 1 and tin.size == daily_mean.size else tin
    out = tin + gamma * (t - dm)
    return out + (0.0 if residual is None else residual)


def map_offset(t_out, offset_c: float, residual=None):
    """C4 form: T_air = T_out + shade offset; C5 uses the same with a bounded radiative excess (STRESS)."""
    return np.asarray(t_out, float) + offset_c + (0.0 if residual is None else residual)


def fit_linear_mapping(df: pd.DataFrame, group_col: str, x_col: str, y_col: str, rng: np.random.Generator,
                       test_frac: float = 0.3) -> tuple[ContextMapping, dict]:
    """Fit T_air = a + b T_out + eps with building-level (group) hold-out: no group in both train and test."""
    groups = np.array(sorted(df[group_col].unique()))
    if len(groups) < 3:
        raise NumericalError("need >= 3 groups (buildings) for a train/test split")
    rng.shuffle(groups)
    n_test = max(1, int(round(test_frac * len(groups))))
    test_g, train_g = set(groups[:n_test]), set(groups[n_test:])
    assert not (test_g & train_g)
    tr, te = df[df[group_col].isin(train_g)], df[df[group_col].isin(test_g)]
    b, a = np.polyfit(tr[x_col].to_numpy(float), tr[y_col].to_numpy(float), 1)
    res_tr = tr[y_col].to_numpy(float) - (a + b * tr[x_col].to_numpy(float))
    res_te = te[y_col].to_numpy(float) - (a + b * te[x_col].to_numpy(float))
    ac1 = float(np.corrcoef(res_tr[:-1], res_tr[1:])[0, 1]) if len(res_tr) > 2 else float("nan")
    val = {"train_groups": sorted(map(str, train_g)), "test_groups": sorted(map(str, test_g)),
           "test_rmse": float(np.sqrt(np.mean(res_te ** 2))), "test_bias": float(res_te.mean()),
           "train_rmse": float(np.sqrt(np.mean(res_tr ** 2)))}
    cm = ContextMapping("C1", "linear_running_mean", {"a": float(a), "b": float(b)}, float(res_tr.std(ddof=2)), ac1, (), val)
    return cm, val
