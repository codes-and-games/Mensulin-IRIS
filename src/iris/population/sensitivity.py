"""Relative insulin sensitivity S_{i,p}:  ln S_ip = m_p + lambda_p * z_i + eps_ip,  then centred so the
cycle-average of S is 1 for each virtual individual (arithmetic mean over the six phases)."""
from __future__ import annotations

import numpy as np

from iris.common.exceptions import NumericalError

N_PHASES = 6
FIRST_LUTEAL = 3  # phases 4..6 (index 3..5) are luteal


def build_sensitivity(z: np.ndarray, m_p: np.ndarray, lambda_p: np.ndarray, eps_sd: float,
                      rng: np.random.Generator, anovulatory: np.ndarray | None = None) -> np.ndarray:
    z = np.asarray(z, float)
    m_p, lam = np.asarray(m_p, float), np.asarray(lambda_p, float)
    if m_p.shape != (N_PHASES,) or lam.shape != (N_PHASES,):
        raise NumericalError("m_p and lambda_p must have six phase entries")
    if eps_sd < 0:
        raise NumericalError("eps_sd must be >= 0")
    ln_s = m_p[None, :] + z[:, None] * lam[None, :] + eps_sd * rng.standard_normal((len(z), N_PHASES))
    if anovulatory is not None and np.any(anovulatory):
        # anovulatory: the luteal sensitivity effect is set to zero (no deviation from the individual baseline)
        ln_s = ln_s.copy()
        ln_s[np.asarray(anovulatory, bool), FIRST_LUTEAL:] = 0.0
    s = np.exp(ln_s)
    return s / s.mean(axis=1, keepdims=True)
