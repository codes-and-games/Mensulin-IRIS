"""Primary endpoints computed from STORED population arrays and potency pools (PROJECTED).

P1 support-aware variance decomposition (+ pi0, atom-aware moments)   P2 heterogeneity penalty HP(tau)
P3 excess concentration (from the engine)                              P5 thermal variance share (see evaluate.sensitivity)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import analytic as an
from . import bounds as bd
from . import metrics as mt
from .mc_engine import population_arrays


def pooled_pairs(arr: dict, ell_pool: np.ndarray, phase_col: int, n_pairs: int, rng: np.random.Generator):
    """Independent pairing of virtual individuals with epistemic potency draws (independence reference)."""
    i = rng.integers(0, len(arr["tdd"]), n_pairs)
    j = rng.integers(0, len(ell_pool), n_pairs)
    return arr["tdd"][i], arr["rho"][i, phase_col], ell_pool[j], arr["R"][i, phase_col]


def p1_variance_decomposition(arr: dict, ell_pool: np.ndarray, phase_col: int, rng: np.random.Generator, n_pairs: int = 200000) -> dict:
    tdd, rho, ell, r_u = pooled_pairs(arr, ell_pool, phase_col, n_pairs, rng)
    du = r_u * ell
    mix = an.mixture_summary(du, ell)
    pos = ell > 0
    out = {"pi0": mix["pi0"], "mu_plus": mix["mu_plus"], "v_plus": mix["v_plus"], "mean_du": mix["mean"], "var_du": mix["var"]}
    if pos.sum() > 10 and np.var(np.log(ell[pos])) > 0:
        dec = an.log_variance_decomposition(np.log(tdd[pos]), np.log(rho[pos]), np.log(ell[pos]))
        out.update({f"share_{k}": v for k, v in dec["shares"].items()}); out["total_log_var_positive_support"] = dec["total"]
    else:
        out["note"] = "log decomposition undefined: loss has no variance on the positive support"
    return out


def p2_heterogeneity_penalty(arr: dict, ell_pool: np.ndarray, phase_col: int, thresholds, J: int | None = None) -> pd.DataFrame:
    """HP(tau) per epistemic draw: Pr_het(du>tau)/Pr_mean(du>tau) with mean-only biology R_mean = E[R_phase]."""
    r = arr["R"][:, phase_col]
    r_mean = np.full_like(r, r.mean())
    rows = []
    for j, ell in enumerate(ell_pool[: J or len(ell_pool)]):
        for t in thresholds:
            hp = mt.heterogeneity_penalty(r * ell, r_mean * ell, t)
            rows.append(dict(epistemic_draw_j=j, threshold=float(t), **hp))
    return pd.DataFrame(rows)


def product_tail_envelope(arr: dict, ell_pool: np.ndarray, phase_col: int, thresholds, n: int = 20000, rng=None) -> pd.DataFrame:
    rng = rng or np.random.default_rng(0)
    r = arr["R"][rng.integers(0, len(arr["R"]), n), phase_col]
    ell = ell_pool[rng.integers(0, len(ell_pool), n)]
    rows = []
    for t in thresholds:
        lo, hi = bd.product_tail_bounds(r, ell, t)
        rows.append(dict(threshold=float(t), bound_lower=lo, bound_upper=hi, independent_estimate=float(np.mean(r * rng.permutation(ell) > t))))
    return pd.DataFrame(rows)
