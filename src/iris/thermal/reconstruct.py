"""Sub-daily reconstruction from daily Tmax/Tmin: sinusoid, Parton-Logan-style, naive constant.

The Parton-Logan parameters are [TO EXTRACT] from the primary paper; they are REQUIRED INPUTS
(no defaults). Validation against hourly truth (E2) reports bias, RMSE, residual autocorrelation.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from iris.common.exceptions import NumericalError, ScientificBlocker


def naive_constant(tmax, tmin, n_per_day: int = 24):
    tmean = 0.5 * (np.asarray(tmax, float) + np.asarray(tmin, float))
    return np.repeat(tmean, n_per_day)


def sinusoid(tmax, tmin, t_hour_of_max: float, n_per_day: int = 24):
    """T(t) = Tmean + A cos(2 pi (t - tmax_hr)/24), t in hours; hour of max is a declared sensitivity parameter."""
    tmax, tmin = np.asarray(tmax, float), np.asarray(tmin, float)
    if np.any(tmax < tmin):
        raise NumericalError("Tmax < Tmin")
    tmean, amp = 0.5 * (tmax + tmin), 0.5 * (tmax - tmin)
    hours = (np.arange(n_per_day) + 0.5) * 24.0 / n_per_day
    return (tmean[:, None] + amp[:, None] * np.cos(2 * np.pi * (hours[None, :] - t_hour_of_max) / 24.0)).ravel()


@dataclass(frozen=True)
class PartonLoganParams:
    """Parton-Logan (1981) parameters. Values MUST come from the registered paper (source S34).

    a_lag_max_h : lag of the daily maximum after solar noon (h)
    b_night_decay: nocturnal decay coefficient (dimensionless)
    c_lag_min_h : lag of the daily minimum relative to sunrise (h)
    ``form_verified`` must be set True only after the functional form below has been checked
    against the primary paper; otherwise parton_logan() raises ScientificBlocker.
    """
    a_lag_max_h: float
    b_night_decay: float
    c_lag_min_h: float
    form_verified: bool = False


def parton_logan(tmax, tmin, tmin_next, sunrise_h: float, sunset_h: float, params: PartonLoganParams,
                 n_per_day: int = 24):
    """Day: Tmin + (Tmax - Tmin) sin(pi m/(Y + 2a)); night: exponential decay from the sunset value.

    [VERIFY] functional form against S34 before production use. No default parameters exist.
    """
    if not params.form_verified:
        raise ScientificBlocker("parton_logan.form", "functional form and parameters not yet verified against S34 [VERIFY]",
                                "verify equations and extract a, b, c from Parton & Logan (1981)")
    tmax, tmin, tmin_n = (np.asarray(v, float) for v in (tmax, tmin, tmin_next))
    y = sunset_h - sunrise_h
    h = (np.arange(n_per_day) + 0.5) * 24.0 / n_per_day
    out = np.empty((len(tmax), n_per_day))
    for d in range(len(tmax)):
        m = h - (sunrise_h + params.c_lag_min_h)
        day = tmin[d] + (tmax[d] - tmin[d]) * np.sin(np.pi * m / (y + 2 * params.a_lag_max_h))
        t_set = tmin[d] + (tmax[d] - tmin[d]) * np.sin(np.pi * (sunset_h - sunrise_h - params.c_lag_min_h) / (y + 2 * params.a_lag_max_h))
        n_hr = np.where(h >= sunset_h, h - sunset_h, h + 24.0 - sunset_h)
        night = tmin_n[d] + (t_set - tmin_n[d]) * np.exp(-params.b_night_decay * n_hr / (24.0 - y))
        out[d] = np.where((h >= sunrise_h + params.c_lag_min_h) & (h < sunset_h), day, night)
    return out.ravel()


def reconstruction_metrics(truth, recon, max_lag: int = 24) -> dict:
    t, r = np.asarray(truth, float), np.asarray(recon, float)
    if t.shape != r.shape:
        raise NumericalError("truth and reconstruction must align")
    e = r - t
    ac = [1.0] + [float(np.corrcoef(e[:-k], e[k:])[0, 1]) for k in range(1, min(max_lag, len(e) - 2) + 1)]
    return {"bias": float(e.mean()), "rmse": float(np.sqrt(np.mean(e ** 2))), "residual_autocorr": ac,
            "residual_autocorr_lag1": ac[1] if len(ac) > 1 else float("nan")}
