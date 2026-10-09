"""K5: empirical lookup of a PUBLISHED potency-vs-temperature-vs-time table.

No extrapolation. A composition rule for time-varying temperature would be an additional
scientific assumption, so K5 supports ISOTHERMAL histories only; otherwise it raises a
ScientificBlocker instead of inventing one.
"""
from __future__ import annotations

import numpy as np
from scipy.interpolate import LinearNDInterpolator

from iris.common.exceptions import NumericalError, ScientificBlocker

from .base import KineticModel


class K5(KineticModel):
    model_id = "K5"

    def __init__(self, temps_c, times_days, potency, isothermal_tol_c: float = 0.25):
        t = np.asarray(temps_c, float); d = np.asarray(times_days, float); p = np.asarray(potency, float)
        if not (t.shape == d.shape == p.shape) or t.ndim != 1 or len(t) < 4:
            raise NumericalError("K5 table needs >= 4 aligned (T, t, potency) rows")
        if np.any((p < 0) | (p > 1)):
            raise NumericalError("table potency must lie in [0, 1]")
        self._pts = np.column_stack([t, d])
        self._interp = LinearNDInterpolator(self._pts, p)
        self.tmin, self.tmax, self.dmin, self.dmax = t.min(), t.max(), d.min(), d.max()
        self.tol = isothermal_tol_c

    def potency(self, t_vial_c, dt_days):
        t = np.atleast_2d(np.asarray(t_vial_c, float))
        out = np.empty(t.shape[0])
        for i, row in enumerate(t):
            if np.ptp(row) > self.tol:
                raise ScientificBlocker("K5.composition_rule",
                                        "lookup table has no rule for time-varying temperature",
                                        "declare a composition assumption or use K1/K3/K4")
            T, dur = float(row.mean()), row.size * dt_days
            if not (self.tmin <= T <= self.tmax and self.dmin <= dur <= self.dmax):
                raise NumericalError(f"K5 query (T={T:.1f} C, t={dur:.2f} d) outside tabulated range: no extrapolation")
            v = float(self._interp(T, dur))
            if not np.isfinite(v):
                raise NumericalError("K5 query lies outside the convex hull of the table")
            out[i] = v
        return out
