"""K1: first-order Arrhenius degradation.

    k(T)  = k_ref * exp[(Ea/R) * (1/T_ref - 1/T)]          (T in KELVIN, always)
    H     = sum_n k(T_n) * dt ,   P = exp(-H)
Also the mean kinetic temperature (MKT), an exposure *descriptor* (never potency).
"""
from __future__ import annotations

import numpy as np

from iris.common.exceptions import NumericalError
from iris.common.units import R_GAS_J_PER_MOL_K, celsius_to_kelvin

from .base import KineticModel

_MAX_EXPONENT = 700.0  # exp() overflows ~709; refuse rather than silently clip


def arrhenius_rate(t_k, k_ref, ea_j_mol, t_ref_k):
    """k(T) with explicit Kelvin inputs; broadcasts over arrays. Raises on invalid/overflowing input."""
    t_k = np.asarray(t_k, dtype=float)
    k_ref = np.asarray(k_ref, dtype=float)
    ea = np.asarray(ea_j_mol, dtype=float)
    tref = np.asarray(t_ref_k, dtype=float)
    if np.any(t_k < 150.0) or np.any(tref < 150.0):
        raise NumericalError("temperature < 150 K: Celsius passed where Kelvin expected?")
    if np.any(~np.isfinite(t_k)) or np.any(~np.isfinite(ea)) or np.any(~np.isfinite(k_ref)):
        raise NumericalError("non-finite Arrhenius input")
    if np.any(ea < 0):
        raise NumericalError("Ea must be >= 0 (negative apparent activation energy rejected)")
    if np.any(k_ref < 0):
        raise NumericalError("k_ref must be >= 0")
    expo = (ea / R_GAS_J_PER_MOL_K) * (1.0 / tref - 1.0 / t_k)
    if np.any(np.abs(expo) > _MAX_EXPONENT):
        raise NumericalError("Arrhenius exponent out of safe range (parameters pathological)")
    return k_ref * np.exp(expo)


def arrhenius_ratio(t_c, ea_j_mol, t_ref_c):
    """k(T)/k(T_ref); equals exactly 1.0 at T == T_ref."""
    tk, tref = celsius_to_kelvin(t_c), celsius_to_kelvin(t_ref_c)
    return arrhenius_rate(tk, 1.0, ea_j_mol, tref)


class K1(KineticModel):
    model_id = "K1"

    def __init__(self, k_ref_per_day, ea_j_mol, t_ref_c: float):
        self.k_ref = np.atleast_1d(np.asarray(k_ref_per_day, dtype=float))
        self.ea = np.atleast_1d(np.asarray(ea_j_mol, dtype=float))
        self.t_ref_k = float(celsius_to_kelvin(t_ref_c))

    def cumulative_hazard(self, t_vial_c, dt_days):
        t = np.atleast_2d(np.asarray(t_vial_c, dtype=float))
        if dt_days <= 0:
            raise NumericalError("dt_days must be > 0")
        tk = celsius_to_kelvin(t)
        d = t.shape[0]
        kref = np.broadcast_to(self.k_ref, (d,))[:, None]
        ea = np.broadcast_to(self.ea, (d,))[:, None]
        k = arrhenius_rate(tk, kref, ea, self.t_ref_k)
        return k.sum(axis=1) * dt_days

    def potency(self, t_vial_c, dt_days):
        return np.exp(-self.cumulative_hazard(t_vial_c, dt_days))


def mean_kinetic_temperature_c(t_c, ea_j_mol: float):
    """MKT = (Ea/R) / [-ln( mean_n exp(-Ea/(R T_n)) )], returned in deg C. Descriptor only."""
    if ea_j_mol <= 0:
        raise NumericalError("MKT requires Ea > 0 (supply a registered/declared value explicitly)")
    tk = celsius_to_kelvin(np.asarray(t_c, dtype=float))
    x = ea_j_mol / R_GAS_J_PER_MOL_K
    # log-mean-exp for stability: ln mean exp(-x/T)
    a = -x / tk
    amax = a.max()
    lme = amax + np.log(np.mean(np.exp(a - amax)))
    return float(x / (-lme) - 273.15)
