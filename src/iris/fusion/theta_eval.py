"""Evaluate a parameter point theta -> endpoint metrics, from STORED population/potency inputs (supplied as callables,
so fusion never imports population or thermal internals). Used by F5/F6/R*, the adversary and the LHS sweeps.

Potency assignment here is always 'coupled' (r_PB = 0 is independent assignment): thermal variation across the stored draws
is treated as between-individual variation, which is what a dependence sweep requires (documented in docs/decisions/0002).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd

from iris.common.exceptions import NumericalError, ScientificBlocker
from iris.common.rng import RngTree

from . import dosing_cases as dc
from . import metrics as mt
from .admissible_set import Theta
from .mc_engine import assign_loss, population_arrays
from .instrument import excess_tci

HIGH = 4


def select_pool(pot: pd.DataFrame, scenario_key: str, model_choice: str) -> np.ndarray:
    """Loss pool (ell = 1 - P) for a scenario key and kinetic-model choice, from the STORED potency table."""
    sub = pot[pot["scenario_id"] == scenario_key]
    if sub.empty:
        raise ScientificBlocker(scenario_key, "no stored potency draws for this scenario/transfer level", "run E4 with this scenario and transfer level")
    if model_choice == "ensemble":
        pass
    elif model_choice == "K0":
        sub = sub[sub["kinetic_model"] == "K0"]
    elif model_choice == "K1_only":
        sub = sub[sub["kinetic_model"] == "K1"]
    elif model_choice in ("pessimistic_envelope", "optimistic_envelope"):
        med = sub[sub["kinetic_model"] != "K0"].groupby("kinetic_study")["potency"].median()
        if med.empty:
            raise ScientificBlocker(scenario_key, "no non-null kinetic study for envelope", "extract kinetics")
        pick = med.idxmin() if model_choice.startswith("pess") else med.idxmax()
        sub = sub[sub["kinetic_study"] == pick]
    else:
        raise NumericalError(f"unknown model choice {model_choice!r}")
    if sub.empty:
        raise ScientificBlocker(scenario_key, f"model choice '{model_choice}' has no stored draws", "extract the corresponding kinetics")
    return 1.0 - sub["potency"].to_numpy(float)


@dataclass
class ThetaEvaluator:
    population_fn: Callable[[dict], pd.DataFrame]        # theta dict -> virtual population (cached by caller)
    potency: pd.DataFrame                                 # stored potency_draws
    duration_d: float
    thresholds_units: tuple
    rng_tree: RngTree
    n_eval: int = 2000
    cache: dict = field(default_factory=dict)

    def _pop(self, th: dict) -> dict:
        key = (th["f"], round(float(th["h"]), 4), round(float(th["eta"]), 4), th["R_B"])
        if key not in self.cache:
            df = self.population_fn(th)
            self.cache[key] = population_arrays(df.iloc[: self.n_eval] if len(df) > self.n_eval else df)
        return self.cache[key]

    def metrics(self, theta: Theta) -> dict:
        th = theta.as_dict()
        arr = self._pop(th)
        from iris.thermal.potency_draws import full_key
        pool = select_pool(self.potency, full_key(th["s"], self.duration_d, float(th["st"])), th["m"])
        n = len(arr["tdd"])
        rng = self.rng_tree.generator("theta_eval", repr(sorted((k, str(v)) for k, v in th.items())))
        r_pb = float(np.clip(th["r_PB"], -0.999, 0.999))
        ell = assign_loss(pool, 0, n, "coupled", r_pb, arr["rank"], rng)
        p = 1.0 - ell
        r_u = arr["R"][:, HIGH]
        du = dc.shortfall_units(th["d"], r_u, arr["tdd"], p)
        r_mean = np.full_like(r_u, r_u.mean())
        du_mean = dc.shortfall_units(th["d"], r_mean, np.full_like(arr["tdd"], arr["tdd"].mean()), p)
        out = {"pi0": float((ell == 0).mean())}
        for t in self.thresholds_units:
            hp = mt.heterogeneity_penalty(du, du_mean, t)
            out[f"hp@{t:g}"] = hp["hp"]; out[f"p_het@{t:g}"] = hp["p_het"]; out[f"p_mean@{t:g}"] = hp["p_mean"]
            out[f"excess_tci@{t:g}"] = excess_tci(r_u, ell, arr["swing"], arr["rank"], t, rng, n_perm=8)
        return out

    def margin_fn(self, metric: str, tau: float, comparator: str, value: float) -> Callable[[Theta], float]:
        key = f"{metric}@{tau:g}"

        def f(theta: Theta) -> float:
            m = self.metrics(theta)[key]
            if not np.isfinite(m):
                return float("inf") if (m == np.inf) else float("nan")
            return (m - value) if comparator == ">" else (value - m)
        return f


def evaluate_points(ev: "ThetaEvaluator", thetas: list[Theta], metric: str, tau: float, comparator: str, value: float) -> pd.DataFrame:
    """Margin of one conclusion at each theta; ScientificBlocker => blocked row (never silently dropped)."""
    from .admissible_set import COMPONENTS
    f = ev.margin_fn(metric, tau, comparator, value)
    rows = []
    for t in thetas:
        r = dict(zip(COMPONENTS, t.values)); r["blocked"] = False; r["blocked_reason"] = ""
        try:
            r["margin"] = f(t)
        except ScientificBlocker as e:
            r["margin"], r["blocked"], r["blocked_reason"] = np.nan, True, str(e)[:160]
        rows.append(r)
    return pd.DataFrame(rows)
