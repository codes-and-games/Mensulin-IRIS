"""Units and physical constants. Temperatures in kelvin inside all rate laws."""
from __future__ import annotations

import numpy as np

from .exceptions import NumericalError

R_GAS_J_PER_MOL_K: float = 8.314  # J/(mol K), as specified in the IRIS document
ZERO_CELSIUS_K: float = 273.15
MGDL_PER_MMOLL_GLUCOSE: float = 18.0156  # mg/dL per mmol/L (molar mass of glucose / 10)
MIN_PER_DAY: float = 1440.0
HOURS_PER_DAY: float = 24.0

# Physically admissible bounds used as guards (NOT scientific parameters).
_MIN_PLAUSIBLE_C = -90.0
_MAX_PLAUSIBLE_C = 120.0


def celsius_to_kelvin(t_c):
    """Convert degrees Celsius to kelvin, rejecting values outside physical guard bounds."""
    t = np.asarray(t_c, dtype=float)
    if np.any(~np.isfinite(t)):
        raise NumericalError("non-finite temperature (NaN/inf) passed to celsius_to_kelvin")
    if np.any(t < _MIN_PLAUSIBLE_C) or np.any(t > _MAX_PLAUSIBLE_C):
        raise NumericalError(
            "temperature outside guard bounds [%g, %g] C: is this kelvin passed as Celsius?"
            % (_MIN_PLAUSIBLE_C, _MAX_PLAUSIBLE_C)
        )
    out = t + ZERO_CELSIUS_K
    return out if out.ndim else float(out)


def kelvin_to_celsius(t_k):
    """Convert kelvin to degrees Celsius."""
    t = np.asarray(t_k, dtype=float)
    if np.any(t <= 0):
        raise NumericalError("kelvin temperature must be > 0")
    out = t - ZERO_CELSIUS_K
    return out if out.ndim else float(out)


def mgdl_to_mmoll(g):
    return np.asarray(g, dtype=float) / MGDL_PER_MMOLL_GLUCOSE


def mmoll_to_mgdl(g):
    return np.asarray(g, dtype=float) * MGDL_PER_MMOLL_GLUCOSE


def minutes_to_days(m):
    return np.asarray(m, dtype=float) / MIN_PER_DAY


def hours_to_days(h):
    return np.asarray(h, dtype=float) / HOURS_PER_DAY
