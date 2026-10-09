"""Requirement WITHOUT circularity.

    ln rho_ip = ln gamma_ip - eta * ln S_ip + xi_ip          (document 14.4)

rho is NEVER set to 1/S. The degenerate case (eta == 1, gamma constant, xi == 0) reduces to
rho proportional to 1/S and is refused unless explicitly requested as the circularity control (A4).
"""
from __future__ import annotations

import numpy as np

from iris.common.exceptions import CircularityError, NumericalError


def build_requirement(s: np.ndarray, gamma: np.ndarray, eta: float, xi_sd: float, rng: np.random.Generator,
                      *, allow_circular_control: bool = False) -> np.ndarray:
    s, gamma = np.asarray(s, float), np.asarray(gamma, float)
    if (s <= 0).any() or (gamma <= 0).any():
        raise NumericalError("S and gamma must be strictly positive")
    gamma_constant = np.allclose(gamma, gamma[:, :1])
    if (not allow_circular_control) and np.isclose(eta, 1.0) and gamma_constant and xi_sd == 0.0:
        raise CircularityError("eta=1 with constant gamma and xi=0 makes rho proportional to 1/S (circular). "
                               "Declare allow_circular_control=True only for ablation A4.")
    xi = xi_sd * rng.standard_normal(s.shape) if xi_sd > 0 else np.zeros_like(s)
    rho = np.exp(np.log(gamma) - eta * np.log(s) + xi)
    return rho / rho.mean(axis=1, keepdims=True)   # relative to the individual's cycle-average requirement


def swing_stats(rho: np.ndarray, tdd: np.ndarray, s: np.ndarray, high_phase: int = 4, low_phase: int = 0):
    """Individual-level swings (argmax/argmin of R within person) and population-level (midluteal vs early follicular)."""
    r_u = tdd[:, None] * rho
    swing_unit = r_u.max(axis=1) / r_u.min(axis=1)
    swing_sens = s.min(axis=1) / s.max(axis=1)
    swing_unit_pop = r_u[:, high_phase] / r_u[:, low_phase]
    return swing_unit, swing_sens, swing_unit_pop
