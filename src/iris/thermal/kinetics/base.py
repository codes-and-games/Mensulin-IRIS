"""Common interface for kinetic models.

A kinetic model maps a vial-temperature history (deg C, shape (T,) or (D, T)) sampled at a
uniform step ``dt_days`` to a potency fraction P in [0, 1]. Implementations must be
monotone: P never increases with time. Parameters are NEVER defaulted here.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class KineticModel(ABC):
    model_id: str = ""

    @abstractmethod
    def potency(self, t_vial_c: np.ndarray, dt_days: float) -> np.ndarray:
        """Final potency per history row."""

    def potency_trajectory(self, t_vial_c: np.ndarray, dt_days: float) -> np.ndarray:
        """Potency after each step (same shape as input, first column = after step 1)."""
        t = np.atleast_2d(np.asarray(t_vial_c, dtype=float))
        return np.stack([self.potency(t[:, : i + 1], dt_days) for i in range(t.shape[1])], axis=-1)
