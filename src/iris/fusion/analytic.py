"""Exact analytic results that precede any simulation (document 16A.2). COMPUTED.

No epsilon is ever added to make a logarithm work: zero loss (P == 1) is an atom handled by an
atom-aware mixture, and ln(delta_u) is evaluated only on the continuous-loss support (ell > 0).
"""
from __future__ import annotations

import numpy as np

from iris.common.exceptions import NumericalError


def loss(p):
    """ell = 1 - P, with P validated to [0, 1]. P == 1 gives ell == 0 exactly."""
    p = np.asarray(p, dtype=float)
    if np.any((p < 0) | (p > 1)) or np.any(~np.isfinite(p)):
        raise NumericalError("potency must lie in [0, 1]")
    return 1.0 - p


def shortfall_case_a(r_u, p):
    """Case A (dose tracks need): delta_u = R * (1 - P). Exactly 0 when P == 1."""
    return np.asarray(r_u, dtype=float) * loss(p)


def shortfall_case_b(r_u, dbar_u, p):
    """Case B (habitual dose = cycle-average requirement): delta_u = R - Dbar * P (signed; surplus retained)."""
    p = np.asarray(p, dtype=float)
    loss(p)  # validate
    return np.asarray(r_u, dtype=float) - np.asarray(dbar_u, dtype=float) * p


def positive_part(x):
    return np.maximum(np.asarray(x, dtype=float), 0.0)


def effective_action_relative(d_u, p, s, dbar_u):
    """E_rel = D * P * S / Dbar  (Case A: D = R; Case B: D = Dbar)."""
    return np.asarray(d_u, float) * np.asarray(p, float) * np.asarray(s, float) / np.asarray(dbar_u, float)


def compounding_retained(s_reduction, ell):
    """Retained effective action (1 - s)(1 - ell) = 1 - s - ell + s*ell; returns (retained, interaction s*ell)."""
    s, l = np.asarray(s_reduction, float), np.asarray(ell, float)
    return (1 - s) * (1 - l), s * l


# ---- Result A1: support-aware variance decomposition -------------------------------------------
def log_variance_decomposition(ln_tdd, ln_rho, ln_ell, assume_independent: bool = False) -> dict:
    """Var(ln du | ell>0) with full covariance terms, ln du = ln TDD + ln rho + ln ell.

    Inputs must be finite (continuous-loss support only). ``assume_independent=True`` is an explicitly
    declared scenario in which covariance terms are dropped. Returns variances, covariances, total and
    shares (shares may be negative/>1 when covariances are non-zero, by design).
    """
    a, b, c = (np.asarray(v, float) for v in (ln_tdd, ln_rho, ln_ell))
    if not (a.shape == b.shape == c.shape) or a.ndim != 1:
        raise NumericalError("log components must be aligned 1-D arrays")
    if not (np.isfinite(a).all() and np.isfinite(b).all() and np.isfinite(c).all()):
        raise NumericalError("log decomposition requires finite logs: restrict to ell > 0 (zero-loss atom handled separately)")
    cov = np.cov(np.vstack([a, b, c]))
    var_terms = {"tdd": cov[0, 0], "rho": cov[1, 1], "ell": cov[2, 2]}
    cov_terms = {"tdd_rho": 2 * cov[0, 1], "tdd_ell": 2 * cov[0, 2], "rho_ell": 2 * cov[1, 2]}
    if assume_independent:
        cov_terms = {k: 0.0 for k in cov_terms}
        total = sum(var_terms.values())
    else:
        total = float(np.var(a + b + c, ddof=1))
    shares = {k: v / total for k, v in {**var_terms, **cov_terms}.items()} if total > 0 else {}
    return {"var": var_terms, "cov2": cov_terms, "total": float(total), "shares": shares,
            "independence_imposed": bool(assume_independent)}


def zero_loss_mixture_moments(pi0: float, mu_plus: float, v_plus: float) -> tuple[float, float]:
    """E[du] = (1-pi0) mu+ ;  Var(du) = (1-pi0) v+ + pi0 (1-pi0) mu+^2   (atom-aware)."""
    if not (0.0 <= pi0 <= 1.0):
        raise NumericalError("pi0 must lie in [0, 1]")
    if v_plus < 0:
        raise NumericalError("v_plus must be >= 0")
    mean = (1 - pi0) * mu_plus
    var = (1 - pi0) * v_plus + pi0 * (1 - pi0) * mu_plus ** 2
    return float(mean), float(var)


def mixture_summary(delta_u: np.ndarray, ell: np.ndarray) -> dict:
    """Empirical pi0, mu+, v+ and the atom-aware mean/variance; also the direct sample mean/variance for cross-checks."""
    d, l = np.asarray(delta_u, float), np.asarray(ell, float)
    atom = l == 0.0
    pi0 = float(atom.mean())
    if (~atom).any():
        mu_plus, v_plus = float(d[~atom].mean()), float(d[~atom].var(ddof=0))
    else:
        mu_plus, v_plus = 0.0, 0.0
    # population (ddof=0) identity: Var = (1-pi0) v+ + pi0(1-pi0) mu+^2
    mean, var = zero_loss_mixture_moments(pi0, mu_plus, v_plus)
    return {"pi0": pi0, "mu_plus": mu_plus, "v_plus": v_plus, "mean": mean, "var": var,
            "direct_mean": float(d.mean()), "direct_var": float(d.var(ddof=0))}


# ---- Result A2: phase contrast of mean unit shortfall (Case A, P independent of biology) ---------
def phase_mean_shortfall_ratio(tdd, rho_high, rho_low) -> dict:
    """E[TDD rho_high]/E[TDD rho_low] versus the simpler E[rho_high]/E[rho_low]; they differ unless TDD is
    uncorrelated with rho. E[ell] cancels."""
    tdd, rh, rl = (np.asarray(v, float) for v in (tdd, rho_high, rho_low))
    den = float(np.mean(tdd * rl))
    if den <= 0:
        raise NumericalError("denominator E[TDD*rho_low] must be positive")
    return {"weighted_ratio": float(np.mean(tdd * rh) / den), "simple_ratio": float(rh.mean() / rl.mean())}


# ---- Result A3: glucose-equivalent shortfall -----------------------------------------------------
def glucose_equivalent_case_a(k_const, ell, rho, s):
    """ISF = (K/TDD) S  =>  dg = K * ell * rho * S."""
    return np.asarray(k_const, float) * np.asarray(ell, float) * np.asarray(rho, float) * np.asarray(s, float)


def glucose_equivalent_cancelling(k_const, ell):
    """ISF = K / R_phase  =>  dg = K * ell exactly (carries no information about cycle biology)."""
    return np.asarray(k_const, float) * np.asarray(ell, float)


def isf_k_over_tdd_times_s(k_const, tdd, s):
    return float(k_const) / np.asarray(tdd, float) * np.asarray(s, float)


def isf_k_over_requirement(k_const, r_u):
    return float(k_const) / np.asarray(r_u, float)
