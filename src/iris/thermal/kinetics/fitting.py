"""Kinetic fitting from literature observations (K1) with leave-one-study-out evaluation.

Observation table columns: study, temp_c, time_days, potency, sd (reported or declared assay SD).
Model: y ~ Normal(exp(-k(T) t), sd^2); ln k_ref ~ weakly informative Normal, Ea ~ Normal(80, 40)
kJ/mol truncated at 0 (the document's ASSUMPTION, configurable). Posterior by random-walk
Metropolis with an explicit generator (reproducible). Identifiability is diagnosed, never assumed.
Nothing here carries default data: calling it without observations is an error.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from iris.common.exceptions import NumericalError, ScientificBlocker
from iris.common.units import R_GAS_J_PER_MOL_K, celsius_to_kelvin

REQUIRED = ("study", "temp_c", "time_days", "potency", "sd")


@dataclass(frozen=True)
class Prior:
    ea_mean_kj: float = 80.0   # ASSUMPTION (document 11.4): broad, results reported under alternatives
    ea_sd_kj: float = 40.0
    lnk_mean: float = -4.0     # ln k_ref (per day) centre: weak; widened by lnk_sd
    lnk_sd: float = 5.0


@dataclass
class K1Fit:
    t_ref_c: float
    lnk_draws: np.ndarray
    ea_draws_j: np.ndarray
    n_obs: int
    n_temps: int
    identifiable: bool
    reasons: list
    corr_lnk_ea: float

    def draws(self, n: int, rng: np.random.Generator):
        idx = rng.integers(0, len(self.lnk_draws), size=n)
        return np.exp(self.lnk_draws[idx]), self.ea_draws_j[idx]


def _check(obs: pd.DataFrame) -> pd.DataFrame:
    if obs is None or len(obs) == 0:
        raise ScientificBlocker("degradation_literature", "no extracted observations supplied",
                                "extract multi-temperature, same-product potency data (L2)")
    miss = [c for c in REQUIRED if c not in obs.columns]
    if miss:
        raise NumericalError(f"observations missing columns {miss}")
    if (obs["sd"] <= 0).any():
        raise NumericalError("observation sd must be > 0 (declare an assay SD explicitly)")
    return obs


def _loglik(lnk, ea_j, tref_k, tk, t, y, sd):
    expo = (ea_j / R_GAS_J_PER_MOL_K) * (1.0 / tref_k - 1.0 / tk)
    if np.any(np.abs(expo) > 700):
        return -np.inf
    pred = np.exp(-np.exp(lnk + expo) * t)
    return float(-0.5 * np.sum(((y - pred) / sd) ** 2))


def fit_k1(obs: pd.DataFrame, rng: np.random.Generator, prior: Prior = Prior(), n_iter: int = 6000,
           burn: int = 2000) -> K1Fit:
    obs = _check(obs)
    t_ref_c = float(obs["temp_c"].mean())  # mid-range reference reduces ln k_ref / Ea correlation
    tref_k = float(celsius_to_kelvin(t_ref_c))
    tk = celsius_to_kelvin(obs["temp_c"].to_numpy(float)); t = obs["time_days"].to_numpy(float)
    y = obs["potency"].to_numpy(float); sd = obs["sd"].to_numpy(float)

    def logpost(th):
        lnk, ea_kj = th
        if ea_kj < 0:
            return -np.inf
        ll = _loglik(lnk, ea_kj * 1e3, tref_k, tk, t, y, sd)
        lp = -0.5 * ((ea_kj - prior.ea_mean_kj) / prior.ea_sd_kj) ** 2 - 0.5 * ((lnk - prior.lnk_mean) / prior.lnk_sd) ** 2
        return ll + lp

    # start at a crude LS point: grid over lnk for Ea = prior mean
    grid = np.linspace(prior.lnk_mean - 3 * prior.lnk_sd, prior.lnk_mean + 3 * prior.lnk_sd, 121)
    cur = np.array([grid[np.argmax([logpost((g, prior.ea_mean_kj)) for g in grid])], prior.ea_mean_kj])
    lp = logpost(cur)
    step = np.array([0.3, 5.0])
    chain = np.empty((n_iter, 2)); acc = 0
    for i in range(n_iter):
        prop = cur + step * rng.standard_normal(2)
        lpp = logpost(prop)
        if np.log(rng.uniform()) < lpp - lp:
            cur, lp = prop, lpp; acc += 1
        chain[i] = cur
        if i == burn // 2 and acc / (i + 1) < 0.15:
            step *= 0.5
    post = chain[burn:]
    n_temps = obs["temp_c"].nunique()
    reasons = []
    if n_temps < 3:
        reasons.append(f"only {n_temps} distinct temperatures (>=3 needed)")
    ea_sd = post[:, 1].std()
    if ea_sd > 0.8 * prior.ea_sd_kj:
        reasons.append("posterior SD of Ea approaches the prior SD: data weakly informative")
    corr = float(np.corrcoef(post[:, 0], post[:, 1])[0, 1])
    return K1Fit(t_ref_c, post[:, 0].copy(), post[:, 1] * 1e3, len(obs), n_temps, not reasons, reasons, corr)


def predict_k1(fit: K1Fit, temp_c, time_days, rng, n: int = 400) -> np.ndarray:
    """Posterior predictive potency draws, shape (n,)."""
    tk = float(celsius_to_kelvin(temp_c)); tref_k = float(celsius_to_kelvin(fit.t_ref_c))
    kref, ea = fit.draws(n, rng)
    expo = (ea / R_GAS_J_PER_MOL_K) * (1.0 / tref_k - 1.0 / tk)
    return np.exp(-kref * np.exp(expo) * time_days)


def loso_k1(obs: pd.DataFrame, rng_tree, **fit_kw) -> pd.DataFrame:
    """Leave-one-study-out: fit without a study, predict it, record error and 95% interval coverage."""
    obs = _check(obs)
    studies = list(obs["study"].unique())
    if len(studies) < 2:
        raise ScientificBlocker("LOSO", "fewer than two studies", "extract at least two comparable studies")
    rows = []
    for s in studies:
        train, test = obs[obs["study"] != s], obs[obs["study"] == s]
        if train["temp_c"].nunique() < 1:
            continue
        fit = fit_k1(train, rng_tree.generator("loso", "fit", str(s)), **fit_kw)
        for _, r in test.iterrows():
            pr = predict_k1(fit, r["temp_c"], r["time_days"], rng_tree.generator("loso", "pred", str(s), str(r.name)))
            lo, hi = np.percentile(pr, [2.5, 97.5])
            rows.append(dict(held_out=s, temp_c=r["temp_c"], time_days=r["time_days"], observed=r["potency"],
                             pred_mean=pr.mean(), abs_err=abs(pr.mean() - r["potency"]),
                             covered=bool(lo - 2 * r["sd"] <= r["potency"] <= hi + 2 * r["sd"]),
                             train_identifiable=fit.identifiable))
    return pd.DataFrame(rows)
