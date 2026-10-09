"""K4: two competing first-order pathways, k(T) = ka(T) + kb(T), each Arrhenius."""
from __future__ import annotations

import numpy as np

from iris.common.exceptions import NumericalError
from iris.common.units import celsius_to_kelvin

from .base import KineticModel
from .k1 import arrhenius_rate


class K4(KineticModel):
    model_id = "K4"

    def __init__(self, ka_ref, ea_a_j_mol, kb_ref, ea_b_j_mol, t_ref_c: float):
        self.p = [np.atleast_1d(np.asarray(v, float)) for v in (ka_ref, ea_a_j_mol, kb_ref, ea_b_j_mol)]
        self.t_ref_k = float(celsius_to_kelvin(t_ref_c))

    def potency(self, t_vial_c, dt_days):
        t = np.atleast_2d(np.asarray(t_vial_c, float))
        if dt_days <= 0:
            raise NumericalError("dt_days must be > 0")
        tk = celsius_to_kelvin(t)
        d = t.shape[0]
        b = lambda v: np.broadcast_to(v, (d,))[:, None]
        ka = arrhenius_rate(tk, b(self.p[0]), b(self.p[1]), self.t_ref_k)
        kb = arrhenius_rate(tk, b(self.p[2]), b(self.p[3]), self.t_ref_k)
        return np.exp(-(ka + kb).sum(axis=1) * dt_days)
