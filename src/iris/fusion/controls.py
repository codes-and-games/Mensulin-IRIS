"""Controls C1-C5 (document 16.2) and instrument controls N1-N3, P1-P2 (document 16A.4)."""
from __future__ import annotations

import numpy as np


def control_c1_no_loss(p):
    """C1: P == 1 (zero thermal loss). All shortfall metrics must vanish in Case A."""
    return np.ones_like(np.asarray(p, float))


def control_c2_no_cycle(s, rho):
    """C2: S == 1, rho == 1 (no cycle effect)."""
    return np.ones_like(s), np.ones_like(rho)


def control_c3_permute_phases(mat: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """C3: permute phase labels WITHIN person (marginal distributions kept, cycle structure broken)."""
    out = np.array(mat, copy=True)
    for i in range(out.shape[0]):
        out[i] = out[i, rng.permutation(out.shape[1])]
    return out


def control_c4_deterministic_potency(ell, how: str = "mean") -> np.ndarray:
    """C4: potency identical across individuals and deterministic (isolates biology)."""
    ell = np.asarray(ell, float)
    v = ell.mean() if how == "mean" else float(np.median(ell))
    return np.full_like(ell, v)


def control_c5_mean_biology(mat: np.ndarray) -> np.ndarray:
    """C5: biology fixed at the population mean profile (isolates thermal)."""
    return np.broadcast_to(mat.mean(axis=0, keepdims=True), mat.shape).copy()


def control_n2_shuffle_loss(ell: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """N2: marginal-preserving shuffle of loss across individuals."""
    return rng.permutation(np.asarray(ell, float))


def control_p1_inject_dependence(ell: np.ndarray, swing_rank: np.ndarray, c: float, top_frac: float = 0.2) -> np.ndarray:
    """P1: multiply loss by (1 + c) for individuals in the top swing quintile; clipped to <= 1."""
    ell = np.array(ell, float, copy=True)
    top = np.asarray(swing_rank) > (1.0 - top_frac)
    ell[top] = np.minimum(ell[top] * (1.0 + c), 1.0)
    return ell
