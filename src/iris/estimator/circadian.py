"""Within-day (24 h) sensitivity profile from the EKF + RTS smoother (document V2 / M2: circadian recovery).

Output is a *relative* profile: ln S(hour) minus the person's mean ln S (the absolute scale depends on the nuisance
constants ISF0/CSF0, which cancel in the relative profile to first order). Amplitude is the 24 h harmonic amplitude of
the relative profile in ln units; peak is the clock hour of maximal S (insulin sensitivity). No biological reading is
attached here: interpretation requires the literature direction (document [VERIFY]) and split-half reproducibility.
"""
from __future__ import annotations

import numpy as np

from .ekf import NoiseSpec, run_ekf
from .glucose_insulin_model import IDX, N_STATE, ModelConstants
from .smoother import rts_smooth


def hourly_ln_s(xs: np.ndarray, steps_per_day: int, dt_min: float, day_mask: np.ndarray | None = None) -> np.ndarray:
    """Mean smoothed lnS by hour of day (24,), centred to zero mean; ``day_mask`` selects days (for split-half)."""
    T = xs.shape[0]; n_days = T // steps_per_day
    ln = xs[: n_days * steps_per_day, IDX["lnS"]].reshape(n_days, steps_per_day)
    if day_mask is not None:
        ln = ln[np.asarray(day_mask, bool)[:n_days]]
    hour = (np.arange(steps_per_day) * dt_min // 60).astype(int)
    prof = np.array([ln[:, hour == h].mean() for h in range(24)])
    return prof - prof.mean()


def harmonic24(profile: np.ndarray) -> tuple[float, float]:
    """(amplitude in ln units, peak hour in [0,24)) of the 24 h harmonic of an hourly profile."""
    h = np.arange(24) + 0.5
    X = np.column_stack([np.cos(2 * np.pi * h / 24), np.sin(2 * np.pi * h / 24)])
    a, b = np.linalg.lstsq(X, profile - profile.mean(), rcond=None)[0]
    amp = float(np.hypot(a, b)); peak = float((np.arctan2(b, a) * 24 / (2 * np.pi)) % 24)
    return amp, peak


def circ_diff_h(a: float, b: float) -> float:
    """Signed circular difference of two clock hours in (-12, 12]."""
    d = (a - b + 12) % 24 - 12
    return float(12.0 if d == -12 else d)


def person_profile(cgm, insulin_u_per_step, carb_g_per_step, k: ModelConstants, noise: NoiseSpec, g_target: float) -> dict:
    """EKF+RTS on one person's grid series. Inputs are per-step amounts (U, g); converted to rates per minute."""
    dt = k.dt_min; spd = int(round(1440 / dt))
    u = np.nan_to_num(np.asarray(insulin_u_per_step, float), nan=0.0) / dt
    carb = np.nan_to_num(np.asarray(carb_g_per_step, float), nan=0.0) / dt
    cgm = np.asarray(cgm, float)
    first = np.nanmedian(cgm[: spd]) if np.isfinite(cgm[:spd]).any() else g_target
    x0 = np.zeros(N_STATE); x0[IDX["G"]] = first
    u_b = np.nanmedian(u[u > 0]) if (u > 0).any() else 0.0
    x0[IDX["I1"]] = x0[IDX["I2"]] = u_b * k.tau_i_min
    res = run_ekf(cgm, u, carb, k, noise, x0, np.diag([1, 1, 1, 1, 100, 0.05, 0.01]))
    xs, Ps = rts_smooth(res)
    n_days = len(cgm) // spd
    odd = np.arange(n_days) % 2 == 1
    out = {"profile": hourly_ln_s(xs, spd, dt), "profile_even": hourly_ln_s(xs, spd, dt, ~odd), "profile_odd": hourly_ln_s(xs, spd, dt, odd),
           "n_days": n_days, "loglik": res.loglik}
    out["amp"], out["peak_h"] = harmonic24(out["profile"])
    return out
