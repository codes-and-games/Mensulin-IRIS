"""Instrument validation of the concentration statistics (document F4 / Part 16A.4): the excess-concentration statistic
must read ZERO when concentration is absent (N1, N2) and respond MONOTONICALLY when injected (P1). If it fails it is not
used as evidence."""
from __future__ import annotations

import numpy as np
import pandas as pd

from iris.common.rng import RngTree

from . import controls
from . import metrics as mt


def excess_tci(r_high: np.ndarray, ell: np.ndarray, swing: np.ndarray, rank: np.ndarray, tau: float, rng, n_perm: int = 15) -> float:
    e = r_high * ell > tau
    v = mt.tci(e, rank)
    base = mt.algebraic_baseline(lambda l: r_high * l, ell, swing, rank, tau, rng, n_perm=n_perm)
    return v - base["tci_alg"] if np.isfinite(v) and np.isfinite(base["tci_alg"]) else float("nan")


def validate_instrument(arr: dict, ell_pool: np.ndarray, tau: float, rng_tree: RngTree, n_seeds: int = 40,
                        strengths=(0.25, 0.5, 1.0), phase_col: int = 4) -> pd.DataFrame:
    """Rows: control, strength, mean excess, SE, detection rate; plus pass flags (N: |mean| < 3 SE + 0.02; P: positive + monotone)."""
    r_high, swing, rank = arr["R"][:, phase_col], arr["swing"], arr["rank"]
    n = len(r_high)
    rows = []
    base_ell = float(np.median(ell_pool[ell_pool > 0])) if (ell_pool > 0).any() else 0.0
    for control in ("N1_independent_assignment", "N2_shuffled_loss", "P1_injected_dependence"):
        for c in ((0.0,) if control.startswith("N") else strengths):
            ex = []
            for s in range(n_seeds):
                rng = rng_tree.generator("instrument", control, f"{c}", f"#{s}")
                ell = rng.choice(ell_pool, size=n)                    # independent assignment (N1)
                if control.startswith("N2"):
                    ell = controls.control_n2_shuffle_loss(ell, rng)
                if control.startswith("P1"):
                    ell = controls.control_p1_inject_dependence(ell, rank, c)
                ex.append(excess_tci(r_high, ell, swing, rank, tau, rng))
            ex = np.array(ex, float); ex = ex[np.isfinite(ex)]
            rows.append(dict(control=control, strength=c, n_valid=int(ex.size), mean_excess=float(ex.mean()) if ex.size else np.nan,
                             se=float(ex.std(ddof=1) / np.sqrt(ex.size)) if ex.size > 1 else np.nan,
                             detection_rate=float(np.mean(ex > 0.1)) if ex.size else np.nan))
    df = pd.DataFrame(rows)
    neg = df[df.control.str.startswith("N")]
    pos = df[df.control.str.startswith("P1")].sort_values("strength")
    df["passed"] = False
    df.loc[neg.index, "passed"] = (neg["mean_excess"].abs() < 3 * neg["se"] + 0.02).to_numpy()
    mono = bool(np.all(np.diff(pos["mean_excess"].to_numpy()) > 0)) and bool((pos["mean_excess"] > 0).all())
    df.loc[pos.index, "passed"] = mono
    return df
