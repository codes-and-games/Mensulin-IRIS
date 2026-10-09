"""K3: nucleation-growth (Finke-Watzky-type) kinetics with Arrhenius rate constants.

    da/dt = -a (k1 + k2' (1 - a)),   a(0) = 1,   k1, k2' Arrhenius in T.
Exact within each step for piecewise-constant T (Bernoulli equation, u = 1/a):
    u(t+dt) = (u(t) - k2'/c) * exp(c*dt) + k2'/c ,   c = k1 + k2'
so the integrator is exact for the step-wise-constant vial temperature and a is monotone
non-increasing. a(t) is the fraction of intact insulin and is used as potency.
"""
from __future__ import annotations

import numpy as np

from iris.common.exceptions import NumericalError
from iris.common.units import celsius_to_kelvin

from .base import KineticModel
from .k1 import arrhenius_rate


class K3(KineticModel):
    model_id = "K3"

    def __init__(self, k1_ref, k2p_ref, ea1_j_mol, ea2_j_mol, t_ref_c: float):
        self.k1_ref = np.atleast_1d(np.asarray(k1_ref, float))
        self.k2_ref = np.atleast_1d(np.asarray(k2p_ref, float))
        self.ea1 = np.atleast_1d(np.asarray(ea1_j_mol, float))
        self.ea2 = np.atleast_1d(np.asarray(ea2_j_mol, float))
        self.t_ref_k = float(celsius_to_kelvin(t_ref_c))

    def potency(self, t_vial_c, dt_days):
        t = np.atleast_2d(np.asarray(t_vial_c, float))
        if dt_days <= 0:
            raise NumericalError("dt_days must be > 0")
        tk = celsius_to_kelvin(t)
        d, n = t.shape
        b = lambda v: np.broadcast_to(v, (d,))[:, None]
        k1 = arrhenius_rate(tk, b(self.k1_ref), b(self.ea1), self.t_ref_k)
        k2 = arrhenius_rate(tk, b(self.k2_ref), b(self.ea2), self.t_ref_k)
        u = np.ones(d)  # u = 1/a
        for j in range(n):
            c = k1[:, j] + k2[:, j]
            ratio = np.divide(k2[:, j], c, out=np.zeros(d), where=c > 0)
            e = np.exp(np.minimum(c * dt_days, 700.0))
            u = (u - ratio) * e + ratio
            u = np.maximum(u, 1.0)  # a <= 1 (guards round-off)
        return 1.0 / u
