"""K0: label-stable null. P == 1 exactly (a point mass; never smoothed)."""
from __future__ import annotations

import numpy as np

from .base import KineticModel


class K0(KineticModel):
    model_id = "K0"

    def potency(self, t_vial_c, dt_days):
        t = np.atleast_2d(np.asarray(t_vial_c, dtype=float))
        return np.ones(t.shape[0])
