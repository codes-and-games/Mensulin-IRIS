"""T4 state-space glucose-insulin model (document 8.x / T4). Explicit equations; nothing hidden in helpers.

STATE  x = [I1, I2, C1, C2, G, lnS, E]
  I1' = u - I1/tauI                      (subcutaneous insulin compartment 1, U)
  I2' = (I1 - I2)/tauI                   (compartment 2)
  C1' = Ag*Carb - C1/tauC                (carbohydrate absorption compartment 1)
  C2' = (C1 - C2)/tauC                   (compartment 2)
  G'  = -S*ISF0*(I2/tauI) + CSF0*(C2/tauC) + E          (glucose, mg/dL)
  lnS_{t+1} = lnS_t + w,  w ~ N(0, q)    (slowly varying sensitivity, S = exp(lnS) relative to the person mean)
  E_{t+1}   = E_t + e,    e ~ N(0, qE)   (slow unmodelled glucose-production offset)
OBSERVATION  CGM = G + v, v ~ N(0, r)   (missing => no update)
INPUTS  u(t): insulin delivery (U/min), Carb(t): carbohydrate (g/min).
CONSTRAINTS  I, C >= 0 are enforced by projection after prediction; S is positive by construction (log state).
Constants are ARGUMENTS with no defaults: tauI, tauC (ASSUMPTION levels in the document), Ag, ISF0, CSF0.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

IDX = dict(I1=0, I2=1, C1=2, C2=3, G=4, lnS=5, E=6)
N_STATE = 7


@dataclass(frozen=True)
class ModelConstants:
    tau_i_min: float
    tau_c_min: float
    ag: float
    isf0_mgdl_per_u: float
    csf0_mgdl_per_g: float
    dt_min: float = 5.0

    def __post_init__(self):
        if min(self.tau_i_min, self.tau_c_min, self.dt_min, self.isf0_mgdl_per_u, self.csf0_mgdl_per_g) <= 0 or not 0 < self.ag <= 1.5:
            raise ValueError("model constants must be positive (and 0 < Ag <= 1.5)")
        if self.dt_min > self.tau_i_min / 4 or self.dt_min > self.tau_c_min / 4:
            raise ValueError("Euler step too coarse relative to the time constants (dt <= tau/4 required)")


def transition(x: np.ndarray, u_u_per_min: float, carb_g_per_min: float, k: ModelConstants) -> np.ndarray:
    """Euler transition f(x, inputs) over one step (deterministic part)."""
    I1, I2, C1, C2, G, lnS, E = x
    d = k.dt_min
    S = np.exp(lnS)
    nx = np.empty_like(x)
    nx[0] = I1 + d * (u_u_per_min - I1 / k.tau_i_min)
    nx[1] = I2 + d * (I1 - I2) / k.tau_i_min
    nx[2] = C1 + d * (k.ag * carb_g_per_min - C1 / k.tau_c_min)
    nx[3] = C2 + d * (C1 - C2) / k.tau_c_min
    nx[4] = G + d * (-S * k.isf0_mgdl_per_u * (I2 / k.tau_i_min) + k.csf0_mgdl_per_g * (C2 / k.tau_c_min) + E)
    nx[5], nx[6] = lnS, E
    return nx


def jacobian(x: np.ndarray, k: ModelConstants) -> np.ndarray:
    """df/dx (analytic)."""
    I1, I2, C1, C2, G, lnS, E = x
    d, S = k.dt_min, np.exp(lnS)
    F = np.eye(N_STATE)
    F[0, 0] = 1 - d / k.tau_i_min
    F[1, 0], F[1, 1] = d / k.tau_i_min, 1 - d / k.tau_i_min
    F[2, 2] = 1 - d / k.tau_c_min
    F[3, 2], F[3, 3] = d / k.tau_c_min, 1 - d / k.tau_c_min
    F[4, 1] = -d * S * k.isf0_mgdl_per_u / k.tau_i_min
    F[4, 3] = d * k.csf0_mgdl_per_g / k.tau_c_min
    F[4, 5] = -d * S * k.isf0_mgdl_per_u * I2 / k.tau_i_min
    F[4, 6] = d
    return F


def observation_matrix() -> np.ndarray:
    H = np.zeros((1, N_STATE)); H[0, IDX["G"]] = 1.0
    return H
