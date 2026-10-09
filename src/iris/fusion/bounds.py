"""Distribution-free bounds that hold for EVERY virtual population consistent with the moments.

Cantelli, Vysochanskij-Petunin, and Makarov bounds for the tail of a product of two variables with
given marginals and unknown dependence (evaluated on empirical marginals on a grid).
"""
from __future__ import annotations

import numpy as np

from iris.common.exceptions import NumericalError


def cantelli_upper(k: float) -> float:
    """Pr(X - mu >= k sigma) <= 1/(1+k^2), k > 0."""
    if k <= 0:
        raise NumericalError("k must be > 0")
    return 1.0 / (1.0 + k * k)


def vysochanskij_petunin_upper(k: float) -> float:
    """Unimodal X: Pr(|X-mu| >= k sigma) <= 4/(9 k^2) for k > sqrt(8/3)."""
    if k <= np.sqrt(8.0 / 3.0):
        raise NumericalError("VP bound requires k > sqrt(8/3)")
    return 4.0 / (9.0 * k * k)


def product_tail_bounds(r_samples, ell_samples, tau: float, n_grid: int = 2000) -> tuple[float, float]:
    """Makarov bounds on Pr(R * ell > tau) over ALL couplings of the two (empirical) marginals.

    With U = ln R, V = ln ell (V = -inf on the zero-loss atom), P(U+V < c) lies in
    [ sup_x max(F_U(x)+F_V(c-x)-1, 0),  inf_x min(F_U(x)+F_V(c-x), 1) ]; hence the tail bounds below.
    Evaluated on a finite grid, and for empirical marginals (Monte Carlo error not included).
    """
    r, l = np.asarray(r_samples, float), np.asarray(ell_samples, float)
    if np.any(r <= 0) or np.any(l < 0):
        raise NumericalError("R must be > 0 and ell >= 0")
    if tau <= 0:
        return 1.0, 1.0
    with np.errstate(divide="ignore"):
        u, v = np.sort(np.log(r)), np.sort(np.log(l))      # v may contain -inf (atom)
    c = np.log(tau)
    grid = np.unique(np.concatenate([np.quantile(u, np.linspace(0, 1, n_grid)), [u.min() - 1.0, u.max() + 1.0]]))
    fu = np.searchsorted(u, grid, side="right") / len(u)
    fv = np.searchsorted(v, c - grid, side="left") / len(v)      # P(V < c - x)
    upper_cdf = min(1.0, float(np.min(fu + fv)))
    lower_cdf = max(0.0, float(np.max(fu + fv - 1.0)))
    return 1.0 - upper_cdf, 1.0 - lower_cdf     # (lower, upper) bounds on Pr(R*ell > tau)
