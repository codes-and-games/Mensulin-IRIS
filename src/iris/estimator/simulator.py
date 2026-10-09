"""Glucose-insulin simulator for S1 ground-truth recovery (SIMULATED, TEST-grade virtual people).

Truth is generated with the same T4 dynamics (so structure error is isolated in the 'misspecified time constant' control),
with meals, a simple basal/bolus/proportional controller, sensor noise, carbohydrate-count error and CGM dropouts.
Every random draw takes an explicit numpy Generator.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .glucose_insulin_model import IDX, N_STATE, ModelConstants, transition


@dataclass(frozen=True)
class SimDesign:
    days: int
    amplitude: float            # A in S_t = 1 + A sin(2 pi t / Lc + theta)
    cycle_len_d: float
    phase_rad: float
    cgm_sd: float               # sensor noise SD (mg/dL)
    carb_error_sd: float        # multiplicative SD of logged-carb error
    gap_fraction: float
    g_target: float
    e_offset: float             # slow glucose production offset (mg/dL/min)
    process_sd_g: float         # unmodelled glucose process noise SD per step (mg/dL)
    meal_hours: tuple = (7.5, 12.5, 19.0)
    meal_g_mean: float = 50.0
    meal_g_sd: float = 15.0
    corr_gain_u_per_min_per_mgdl: float = 5e-5
    gap_len_steps: int = 24
    circadian_amp: float = 0.0   # within-day multiplicative modulation of S: S *= 1 + a cos(2 pi (h - peak)/24); 0 => unchanged behaviour
    circadian_peak_h: float = 8.0


def true_daily_s(design: SimDesign) -> np.ndarray:
    d = np.arange(design.days)
    return 1.0 + design.amplitude * np.sin(2 * np.pi * d / design.cycle_len_d + design.phase_rad)


def simulate(design: SimDesign, k: ModelConstants, rng: np.random.Generator) -> dict:
    spd = int(round(1440 / k.dt_min))
    T = design.days * spd
    s_day = true_daily_s(design)
    ln_s = np.repeat(np.log(s_day), spd)
    if design.circadian_amp:
        hh = (np.arange(T) % spd) * k.dt_min / 60.0
        ln_s = ln_s + np.log(1.0 + design.circadian_amp * np.cos(2 * np.pi * (hh - design.circadian_peak_h) / 24.0))
    carb_true = np.zeros(T); carb_logged = np.zeros(T)
    for d in range(design.days):
        for h in design.meal_hours:
            i = d * spd + int(h * 60 / k.dt_min)
            g = max(5.0, rng.normal(design.meal_g_mean, design.meal_g_sd))
            carb_true[i] = g / k.dt_min
            carb_logged[i] = g * max(0.0, 1.0 + rng.normal(0.0, design.carb_error_sd)) / k.dt_min
    x = np.zeros(N_STATE)
    u_b = design.e_offset / (k.isf0_mgdl_per_u * 1.0)               # basal balancing E at S = 1 (U/min)
    x[IDX["I1"]] = x[IDX["I2"]] = u_b * k.tau_i_min
    x[IDX["G"]], x[IDX["lnS"]], x[IDX["E"]] = design.g_target, ln_s[0], design.e_offset
    icr_u_per_g = k.csf0_mgdl_per_g / k.isf0_mgdl_per_u
    G = np.empty(T); u = np.zeros(T)
    for t in range(T):
        x[IDX["lnS"]] = ln_s[t]
        bolus = carb_logged[t] * k.dt_min * icr_u_per_g / k.dt_min   # dose logged/measured by the person, spread over one step
        corr = design.corr_gain_u_per_min_per_mgdl * (x[IDX["G"]] - design.g_target)
        u[t] = max(0.0, u_b + corr) + bolus
        G[t] = x[IDX["G"]]
        x = transition(x, u[t], carb_true[t], k)
        x[:4] = np.maximum(x[:4], 0.0)
        x[IDX["G"]] += design.process_sd_g * rng.standard_normal()
    cgm = G + design.cgm_sd * rng.standard_normal(T)
    mask = np.ones(T, bool)
    n_gap_target = int(design.gap_fraction * T)
    while (~mask).sum() < n_gap_target:
        s = int(rng.integers(0, max(T - design.gap_len_steps, 1)))
        mask[s:s + design.gap_len_steps] = False
    cgm_obs = np.where(mask, cgm, np.nan)
    return {"cgm": cgm_obs, "cgm_true_glucose": G, "u": u, "carb_logged": carb_logged, "carb_true": carb_true,
            "s_daily_true": s_day, "steps_per_day": spd, "u_basal_u_per_min": u_b}
