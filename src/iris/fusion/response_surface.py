"""Response surface over (loss ell, sensitivity reduction s)  (document 16.3). Analytic boundary + density.

Layer 1 (algebra): E_rel = (1 - ell)(1 - s).
Layer 2 (biology density): fraction of virtual individuals per sensitivity-reduction bin.
Layer 3/4 (thermal exposure, uncertainty envelope) are supplied by the caller as stored tables.
Z = Pr(shortfall > tau) among virtual individuals whose phase sensitivity reduction lies in the bin.
"""
from __future__ import annotations

import numpy as np


def analytic_effective_action(ell_grid, s_grid):
    L, S = np.meshgrid(ell_grid, s_grid, indexing="ij")
    return (1 - L) * (1 - S)


def exceedance_surface(r_u: np.ndarray, sens: np.ndarray, ell_grid, s_edges, tau: float, rho_scale: np.ndarray | None = None):
    """Return (Z[ell, bin], bin_counts). ``sens`` = relative sensitivity S in the phase (reduction s = 1 - S)."""
    s_red = 1.0 - np.asarray(sens, float)
    idx = np.digitize(s_red, s_edges) - 1
    Z = np.full((len(ell_grid), len(s_edges) - 1), np.nan)
    counts = np.zeros(len(s_edges) - 1, int)
    for b in range(len(s_edges) - 1):
        m = idx == b
        counts[b] = int(m.sum())
        if m.any():
            for a, l in enumerate(ell_grid):
                Z[a, b] = float(np.mean(r_u[m] * l > tau))
    return Z, counts
