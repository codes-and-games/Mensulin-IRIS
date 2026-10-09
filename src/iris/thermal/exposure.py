"""Model-independent exposure summaries and parametric scenario generation.

Summaries (COMPUTED): hours above 25/30/35/40 C, degree-hours above 25 C, max temperature,
MKT under a *stated* Ea (a descriptor, not potency), imputed fraction.
Parametric scenarios (SIMULATED) are generated from YAML definitions; nothing is hard-coded.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from iris.common.exceptions import NumericalError, ScientificBlocker
from iris.thermal.kinetics.k1 import mean_kinetic_temperature_c

THRESHOLDS_C = (25.0, 30.0, 35.0, 40.0)


def exposure_summary(t_c, dt_h: float, *, imputed=None, mkt_ea_j_mol: float | None = None,
                     thresholds_c=THRESHOLDS_C, base_c: float = 25.0) -> dict:
    t = np.asarray(t_c, dtype=float)
    if t.ndim != 1 or t.size == 0 or not np.isfinite(t).all():
        raise NumericalError("exposure_summary needs a finite 1-D series")
    out = {f"hours_gt_{int(th)}C": float((t > th).sum() * dt_h) for th in thresholds_c}
    out["degree_hours_gt_25C"] = float(np.clip(t - base_c, 0, None).sum() * dt_h)
    out["max_c"] = float(t.max())
    out["mean_c"] = float(t.mean())
    out["mkt_c"] = mean_kinetic_temperature_c(t, mkt_ea_j_mol) if mkt_ea_j_mol else float("nan")
    out["imputed_fraction"] = 0.0 if imputed is None else float(np.mean(np.asarray(imputed, bool)))
    return out


def _grid(duration_d: float, dt_min: float):
    n = int(round(duration_d * 1440.0 / dt_min))
    return np.arange(n) * dt_min / 60.0  # hours


def generate_parametric(cfg: dict, duration_d: float, dt_min: float, rng: np.random.Generator) -> tuple[np.ndarray, list]:
    """Air temperature (deg C) next to the vial for a parametric scenario definition.

    Returns (series, declared_assumptions). Scenarios needing registered data (S5, S8) raise
    ScientificBlocker; they are not parametric.
    """
    kind = cfg["kind"]
    th = _grid(duration_d, dt_min)
    assumptions = [k for k, v in cfg.get("params", {}).items() if isinstance(v, dict) and v.get("status") in ("ASSUMPTION", "STRESS_TEST")]
    p = {k: (v["value"] if isinstance(v, dict) else v) for k, v in cfg.get("params", {}).items()}
    if kind == "constant":
        return np.full_like(th, p["temp_c"]), assumptions
    if kind == "sinusoid":
        mid, amp = 0.5 * (p["tmax_c"] + p["tmin_c"]), 0.5 * (p["tmax_c"] - p["tmin_c"])
        return mid + amp * np.cos(2 * np.pi * (th - p["hour_of_max"]) / p["period_h"]), assumptions
    if kind == "refrigerator_band":
        mid, amp = 0.5 * (p["band_max_c"] + p["band_min_c"]), 0.5 * (p["band_max_c"] - p["band_min_c"])
        return mid + amp * np.sin(2 * np.pi * th / p["cycle_period_h"]), assumptions
    if kind == "heat_spikes":
        base = np.full_like(th, p["base_c"])
        days = int(np.ceil(duration_d))
        n_total = int(round(p["episodes_per_week"] * duration_d / 7.0))
        if n_total > 0:
            for i in range(n_total):
                start_h = rng.uniform(0, max(duration_d * 24 - p["episode_max_h"], 1e-9))
                dur_h = rng.uniform(p["episode_min_h"], p["episode_max_h"])
                peak = rng.uniform(p["peak_min_c"], p["peak_max_c"])
                base[(th >= start_h) & (th < start_h + dur_h)] = peak
        return base, assumptions
    if kind == "transport_window":
        t = _grid(duration_d, dt_min)
        base = np.full_like(t, p["base_c"])
        start_h = p["window_start_h"]
        dur = rng.uniform(p["window_min_h"], p["window_max_h"])
        base[(t >= start_h) & (t < start_h + dur)] = p["window_temp_c"]
        return base, assumptions
    if kind in ("reanalysis_driven", "published_benchmark"):
        raise ScientificBlocker(cfg.get("id", kind), f"scenario kind '{kind}' requires registered, verified inputs",
                                cfg.get("blocked_on", "registered climate/benchmark source"))
    raise NumericalError(f"unknown scenario kind '{kind}'")


def exposure_table(scenario_id: str, context_id: str, location_id: str, start_utc: str, dt_min: float,
                   t_out, t_air, t_vial, tau_min: float, source_ids: str, qc_flag, imputed, evidence_class: str) -> pd.DataFrame:
    n = len(t_air)
    ts = pd.date_range(start_utc, periods=n, freq=pd.Timedelta(minutes=dt_min), tz="UTC").tz_convert("UTC").tz_localize(None)
    return pd.DataFrame({
        "scenario_id": scenario_id, "context_id": context_id, "location_id": location_id,
        "timestamp_utc": ts, "t_out_c": np.asarray(t_out, float) if t_out is not None else np.full(n, np.nan),
        "t_air_c": np.asarray(t_air, float), "t_vial_c": np.asarray(t_vial, float), "tau_min": float(tau_min),
        "source_ids": source_ids, "qc_flag": np.asarray(qc_flag) if not isinstance(qc_flag, str) else qc_flag,
        "imputed_flag": np.asarray(imputed, bool) if not isinstance(imputed, bool) else imputed,
        "evidence_class": evidence_class,
    })
