"""Two-level Monte Carlo fusion engine (document 15.3).

OUTER loop j (epistemic): one stored potency draw per j (kinetic study/model/parameters, tau, climate-bias, transfer
discrepancy are all frozen inside that stored row). The engine NEVER recomputes kinetics.
INNER loop i (aleatory): virtual individuals of the stored population.

Two potency-assignment modes are explicit (and recorded in every output):
  'shared'  : every individual has the epistemic draw's P_j  (thermal uncertainty stays epistemic)
  'coupled' : individuals draw loss from the scenario's pooled potency distribution through a Gaussian copula with
              correlation r_PB to a latent biological score (thermal variation is then treated as BETWEEN-individual
              variation). r_PB == 0 gives independent assignment.
All outputs are PROJECTED (model-based extrapolation), never empirical findings.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

from iris.common.exceptions import NumericalError
from iris.common.rng import RngTree
from iris.common.schemas import FUSION_OUT, N_PHASES, PHASES

from . import dosing_cases as dc
from . import metrics as mt

HIGH_POP, LOW_POP = 4, 0
PHASE_LABELS = list(PHASES) + ["high_pop", "low_pop", "high_ind", "low_ind"]


@dataclass(frozen=True)
class FusionConfig:
    run_id: str
    scenario_id: str
    J: int
    dosing_cases: tuple[str, ...]
    isf_model: str
    isf_const: tuple[float, ...]
    thr_units: tuple[float, ...]
    thr_pct_tdd: tuple[float, ...]
    thr_glucose: tuple[float, ...]
    mode: str = "shared"
    r_pb: float = 0.0
    tci_top_fraction: float = 0.2
    n_batches: int = 10
    include_glucose: bool = True
    include_concentration: bool = True
    n_perm_baseline: int = 10


def population_arrays(pop: pd.DataFrame) -> dict:
    cols = lambda pre, suf="": np.column_stack([pop[f"{pre}{k}{suf}"].to_numpy() for k in range(1, N_PHASES + 1)])
    return {"tdd": pop["tdd_u"].to_numpy(), "S": cols("S_p"), "R": cols("R_p", "_u"), "rho": cols("rho_p"),
            "swing": pop["swing_unit"].to_numpy(), "rank": pop["swing_rank"].to_numpy()}


def assign_loss(ell_pool: np.ndarray, j_row: int, n: int, mode: str, r_pb: float, rank: np.ndarray,
                rng: np.random.Generator) -> np.ndarray:
    """Per-individual loss vector for epistemic draw j."""
    if mode == "shared":
        return np.full(n, ell_pool[j_row])
    if mode == "coupled":
        if not -1.0 < r_pb < 1.0:
            raise NumericalError("|r_PB| must be < 1")
        zb = stats.norm.ppf(np.clip(rank, 1e-6, 1 - 1e-6))      # latent biological score (rank-based: exact margins)
        h = r_pb * zb + np.sqrt(1 - r_pb ** 2) * rng.standard_normal(n)
        q = stats.norm.cdf(h)
        return np.quantile(ell_pool, q, method="linear")
    raise NumericalError(f"unknown potency mode {mode!r}")


def _phase_views(arr: dict) -> dict:
    """phase label -> (R_u, S, rho) vectors."""
    out = {}
    for k, name in enumerate(PHASES):
        out[name] = (arr["R"][:, k], arr["S"][:, k], arr["rho"][:, k])
    ind_hi, ind_lo = arr["R"].argmax(axis=1), arr["R"].argmin(axis=1)
    idx = np.arange(arr["R"].shape[0])
    out["high_pop"], out["low_pop"] = out[PHASES[HIGH_POP]], out[PHASES[LOW_POP]]
    out["high_ind"] = (arr["R"][idx, ind_hi], arr["S"][idx, ind_hi], arr["rho"][idx, ind_hi])
    out["low_ind"] = (arr["R"][idx, ind_lo], arr["S"][idx, ind_lo], arr["rho"][idx, ind_lo])
    return out


def run_fusion(pop: pd.DataFrame, potency: pd.DataFrame, cfg: FusionConfig, rng_tree: RngTree,
               phases: tuple[str, ...] | None = None) -> pd.DataFrame:
    """Run the two-level MC and return a validated ``fusion_out`` table."""
    sub = potency[potency["scenario_id"] == cfg.scenario_id].sort_values("epistemic_draw_j")
    if sub.empty:
        raise NumericalError(f"no stored potency draws for scenario {cfg.scenario_id!r}")
    ell_pool = 1.0 - sub["potency"].to_numpy()
    J = min(cfg.J, len(ell_pool))
    arr = population_arrays(pop)
    n = len(pop)
    views = _phase_views(arr)
    use_phases = phases or tuple(PHASE_LABELS)
    rows = []
    r_assign = rng_tree.child("fusion", cfg.scenario_id)
    for j in range(J):
        ell = assign_loss(ell_pool, j, n, cfg.mode, cfg.r_pb, arr["rank"], r_assign.indexed("assign", j))
        p_vec = 1.0 - ell
        for case in cfg.dosing_cases:
            for ph in use_phases:
                r_u, s, rho = views[ph]
                du = dc.shortfall_units(case, r_u, arr["tdd"], p_vec)
                _emit_unit_metrics(rows, cfg, j, ph, case, du, arr, ell, rng_tree)
                if cfg.include_glucose:
                    for k in cfg.isf_const:
                        dg = dc.glucose_shortfall(du, dc.isf(cfg.isf_model, k, arr["tdd"], s, r_u))
                        for g in cfg.thr_glucose:
                            p, se = mt.exceedance(dg, g)
                            rows.append((cfg.run_id, j, cfg.scenario_id, ph, case, float(k), "exceed_glucose_mgdl", float(g), p, se))
    df = pd.DataFrame(rows, columns=list(c.name for c in FUSION_OUT.columns))
    FUSION_OUT.validate(df)
    return df


def _emit_unit_metrics(rows, cfg, j, ph, case, du, arr, ell, rng_tree):
    rid, sid = cfg.run_id, cfg.scenario_id
    for t in cfg.thr_units:
        p, se = mt.exceedance(du, t); rows.append((rid, j, sid, ph, case, np.nan, "exceed_units", float(t), p, se))
    for t in cfg.thr_pct_tdd:
        p, se = mt.exceedance(du / arr["tdd"], t / 100.0); rows.append((rid, j, sid, ph, case, np.nan, "exceed_pct_tdd", float(t), p, se))
    m, se = mt.mean_positive_part(du); rows.append((rid, j, sid, ph, case, np.nan, "mean_positive_part_u", np.nan, m, se))
    if cfg.include_concentration and ph in ("high_pop", "high_ind") and case == "A":
        for t in cfg.thr_units:
            e = du > t
            v = mt.tci(e, arr["rank"], cfg.tci_top_fraction)
            rows.append((rid, j, sid, ph, case, np.nan, "tci", float(t), v, np.nan))
            rows.append((rid, j, sid, ph, case, np.nan, "ci", float(t), mt.concentration_index(e, arr["swing"]), np.nan))
            if np.ptp(ell) == 0.0:
                # loss is identical across individuals => permuting it changes nothing: baseline == observed EXACTLY,
                # so excess concentration is identically zero (instrument control N1 holds by construction here).
                tci_alg, excess = v, (0.0 if np.isfinite(v) else np.nan)
            else:
                base = mt.algebraic_baseline(lambda l: du_for(arr, ph, l), ell, arr["swing"], arr["rank"], t,
                                             rng_tree.generator("alg_baseline", f"#{j}", sid, ph, f"{t}"), n_perm=cfg.n_perm_baseline,
                                             top_fraction=cfg.tci_top_fraction)
                tci_alg = base["tci_alg"]
                excess = v - tci_alg if np.isfinite(v) and np.isfinite(tci_alg) else np.nan
            rows.append((rid, j, sid, ph, case, np.nan, "tci_algebraic", float(t), tci_alg, np.nan))
            rows.append((rid, j, sid, ph, case, np.nan, "tci_excess", float(t), excess, np.nan))


def du_for(arr, phase_label, ell_vec):
    r = _phase_views(arr)[phase_label][0]
    return r * ell_vec


def summarise_epistemic(df: pd.DataFrame, level: float = 0.95) -> pd.DataFrame:
    """Aleatory statistic per j -> epistemic interval across j (+ mean MC SE)."""
    key = ["scenario_id", "phase", "dosing_case", "isf_const", "metric", "threshold"]
    g = df.groupby(key, dropna=False)
    q = (1 - level) / 2
    out = g["value"].agg(median="median", lo=lambda v: v.quantile(q), hi=lambda v: v.quantile(1 - q), n_draws="count").reset_index()
    out["mc_se_mean"] = g["mc_se"].mean().to_numpy()
    out["evidence_class"] = "PROJECTED"
    return out
