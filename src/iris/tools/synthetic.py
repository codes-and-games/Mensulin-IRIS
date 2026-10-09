"""TEST_ONLY synthetic generators. Every output is labelled SYNTHETIC / TEST_ONLY; production gates reject them."""
from __future__ import annotations

import numpy as np
import pandas as pd

TEST_ONLY_LABEL = "TEST_ONLY:synthetic_generator"


def synthetic_person_day(rng: np.random.Generator, n_persons: int = 24, n_days: int = 84, cycle_len: float = 28.0,
                         amplitude: float = 0.05, tdd_mean: float = 40.0, with_cycle_labels: bool = True,
                         isf_tdd_slope: float = -1.0) -> pd.DataFrame:
    rows = []
    for p in range(n_persons):
        base = rng.lognormal(np.log(tdd_mean), 0.3)
        phase = 0.7 + rng.normal(0, 0.3)      # cycle-aligned: the population-level signal shares a common phase
        L = int(round(cycle_len + rng.normal(0, 1.5)))
        for d in range(n_days):
            cday = d % L + 1
            tdd = base * (1 + amplitude * np.sin(2 * np.pi * (cday - 1) / L + phase)) * np.exp(rng.normal(0, 0.06))
            rows.append(dict(dataset="TEST_ONLY:synthetic", person_id=f"P{p:03d}", date_local=str((pd.Timestamp("2026-01-01") + pd.Timedelta(days=d)).date()), tz="UTC",
                             tdd_u=tdd, basal_u=0.45 * tdd, bolus_u=0.55 * tdd, carb_g=rng.normal(120, 20), carb_entries=int(rng.integers(2, 6)),
                             cgm_coverage=float(rng.uniform(0.8, 1.0)), mean_glucose_mgdl=float(rng.normal(150, 15)), tir_pct=60.0, tbr_pct=2.0, tar_pct=38.0,
                             device_type="TEST", exclude_flag=False, exclude_reason=None,
                             cycle_day=cday if with_cycle_labels else np.nan, cycle_len=L if with_cycle_labels else np.nan,
                             cycle_pos=(cday - 1) / L if with_cycle_labels else np.nan, phase=None, pwd_flags=None,
                             isf_clinician=1700.0 / tdd * np.exp(rng.normal(0, 0.15)) if isf_tdd_slope else np.nan))
    return pd.DataFrame(rows)


def synthetic_climate(rng: np.random.Generator, n_days: int = 60, sources=("A", "B"), bias=(0.0, 0.6), noise=(0.2, 0.4)) -> dict:
    """Hourly outdoor temperature (deg C) for several fake 'sources' at the same coordinates/period."""
    t = pd.date_range("2026-01-01", periods=n_days * 24, freq="h", tz="UTC")
    truth = 24 + 6 * np.sin(2 * np.pi * (t.hour.to_numpy() - 9) / 24) + 2 * np.sin(2 * np.pi * np.arange(len(t)) / (24 * 20))
    return {s: pd.Series(truth + b + rng.normal(0, nz, len(t)), index=t) for s, b, nz in zip(sources, bias, noise)}, pd.Series(truth, index=t)


def synthetic_comfort_table(rng: np.random.Generator, n_buildings: int = 12, per_building: int = 120, a: float = 8.0, b: float = 0.7) -> pd.DataFrame:
    rows = []
    for k in range(n_buildings):
        off = rng.normal(0, 0.5)
        x = rng.uniform(10, 38, per_building)
        rows.append(pd.DataFrame({"building_id": f"B{k:02d}", "t_out_c": x, "t_in_c": a + b * x + off + rng.normal(0, 0.8, per_building)}))
    return pd.concat(rows, ignore_index=True)


def synthetic_events_grid(rng: np.random.Generator, n_persons: int = 8, n_days: int = 14, circadian_amp: float = 0.2,
                          peak_h: float = 8.0, dt_min: float = 5.0, tdd: float = 40.0) -> pd.DataFrame:
    """TEST_ONLY 5-min event grid with an injected 24 h sensitivity pattern (columns as in ingest.pipeline.EVENT_COLUMNS)."""
    from iris.estimator.glucose_insulin_model import ModelConstants
    from iris.estimator.simulator import SimDesign, simulate
    k = ModelConstants(55.0, 40.0, 0.9, 1800.0 / tdd, 3.6, dt_min)
    frames = []
    for p in range(n_persons):
        d = SimDesign(days=n_days, amplitude=0.0, cycle_len_d=28.0, phase_rad=0.0, cgm_sd=10.0, carb_error_sd=0.2, gap_fraction=0.08,
                      g_target=120.0, e_offset=0.2 * (1800.0 / tdd) / 50.0, process_sd_g=0.5, circadian_amp=circadian_amp,
                      circadian_peak_h=peak_h + rng.normal(0, 0.5))
        sim = simulate(d, k, rng)
        ts = pd.date_range("2026-01-01", periods=len(sim["cgm"]), freq=f"{int(dt_min)}min")
        frames.append(pd.DataFrame({"dataset": "TEST_ONLY:synthetic", "person_id": f"P{p:03d}", "ts_local": ts,
                                    "date_local": ts.strftime("%Y-%m-%d"), "glucose_mgdl": sim["cgm"], "glucose_flag": "ok",
                                    "basal_u": np.nan, "bolus_u": np.nan, "insulin_u": sim["u"] * dt_min, "carb_g": sim["carb_logged"] * dt_min}))
    return pd.concat(frames, ignore_index=True)
