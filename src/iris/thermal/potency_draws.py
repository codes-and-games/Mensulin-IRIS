"""Layer 2 output: M potency draws per scenario (+ exposure summaries). Fusion samples these;
it never recomputes kinetics.

Uncertainty carried per epistemic draw j: climate-data bias (only for climate-driven scenarios),
context-mapping residual (when a context mapping is used), vial lag tau (log-uniform), kinetic
study/model/parameters, and transfer discrepancy ln k_target = ln k + delta, delta~N(0, st^2).
Random streams are keyed by NAME so adding draws elsewhere never perturbs another component;
kinetics streams are keyed only by j so scenarios share common random numbers.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from iris.common.rng import RngTree
from iris.common.schemas import validate_potency_draws

from .ensemble import ModelSet
from .exposure import generate_parametric
from .lag import exponential_integrator, sample_tau_log_uniform


def scenario_key(scenario_id: str, duration_d: float) -> str:
    return f"{scenario_id}@{int(duration_d) if float(duration_d).is_integer() else duration_d}d"


def full_key(scenario_id: str, duration_d: float, transfer_sd: float) -> str:
    """Scenario key including the transfer-discrepancy level, e.g. 'S3@28d#st0.35'."""
    return f"{scenario_key(scenario_id, duration_d)}#st{transfer_sd:g}"


def generate_potency_draws(scenario_cfg: dict, duration_d: float, model_set: ModelSet, tau_min_range: tuple[float, float],
                           J: int, rng_tree: RngTree, *, dt_min: float = 1.0, transfer_sd: float = 0.0,
                           sigma_data_c: float = 0.0, return_histories: bool = False):
    """Return a validated potency_draws DataFrame (and optionally the vial histories of draw 0)."""
    sid = scenario_cfg["id"]
    key = full_key(sid, duration_d, transfer_sd)
    uses_climate = bool(scenario_cfg.get("uses_climate", False))
    dt_days = dt_min / 1440.0
    rows, first_hist = [], None
    for j in range(J):
        r_hist = rng_tree.generator("history", sid, f"#{j}")
        r_kin = rng_tree.generator("kinetics", f"#{j}")     # shared across scenarios (CRN)
        r_tau = rng_tree.generator("tau", f"#{j}")
        r_bias = rng_tree.generator("climate_bias", f"#{j}")
        r_tr = rng_tree.generator("transfer", f"#{j}")
        air, _ = generate_parametric(scenario_cfg, duration_d, dt_min, r_hist)
        delta = float(r_bias.normal(0.0, sigma_data_c)) if (uses_climate and sigma_data_c > 0) else 0.0
        air = air + delta
        tau = float(sample_tau_log_uniform(r_tau, tau_min_range, 1)[0])
        vial = exponential_integrator(air, dt_min * 60.0, tau * 60.0)
        k = model_set.sample_member(r_kin)
        spec = model_set.specs[k]
        draw_i = int(r_kin.integers(0, spec.n_draws))
        scale = float(np.exp(r_tr.normal(0.0, transfer_sd))) if transfer_sd > 0 else 1.0
        p = float(spec.build(draw_i, scale).potency(vial, dt_days)[0])
        if spec.is_null:
            p = 1.0
        rows.append((key, spec.study, spec.model_id, j, delta, tau, min(max(p, 0.0), 1.0), spec.is_null))
        if j == 0:
            first_hist = (air, vial)
    df = pd.DataFrame(rows, columns=["scenario_id", "kinetic_study", "kinetic_model", "epistemic_draw_j",
                                     "delta_data_c", "tau_min", "potency", "is_null_model"])
    validate_potency_draws(df)
    return (df, first_hist) if return_histories else df
