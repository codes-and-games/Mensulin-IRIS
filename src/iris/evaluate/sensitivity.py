"""Global sensitivity: Sobol indices (SALib) for the thermal variance share, plus one-at-a-time tornado tables.

The model function receives a matrix of unit-hypercube-mapped parameters and returns the scalar response.
The thermal-share decomposition uses declared uncertainty components (climate input, kinetic parameters,
model choice, transfer discrepancy, lag); the response function is supplied by the caller (stored layer-2 emulator).
"""
from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd
from SALib.analyze import sobol as sobol_analyze
from SALib.sample import sobol as sobol_sample

from iris.common.exceptions import NumericalError


def sobol_indices(fn: Callable[[np.ndarray], np.ndarray], names: list[str], bounds: list[tuple[float, float]], n: int,
                  seed: int, calc_second_order: bool = False) -> pd.DataFrame:
    if len(names) != len(bounds):
        raise NumericalError("names and bounds must align")
    problem = {"num_vars": len(names), "names": names, "bounds": [list(b) for b in bounds]}
    X = sobol_sample.sample(problem, n, calc_second_order=calc_second_order, scramble=True, seed=seed)
    Y = np.asarray(fn(X), float)
    if Y.shape != (X.shape[0],) or not np.isfinite(Y).all():
        raise NumericalError("model function must return one finite value per sample")
    r = sobol_analyze.analyze(problem, Y, calc_second_order=calc_second_order, print_to_console=False, seed=seed)
    return pd.DataFrame({"parameter": names, "S1": r["S1"], "S1_conf": r["S1_conf"], "ST": r["ST"], "ST_conf": r["ST_conf"]})


def tornado(fn: Callable[[dict], float], base: dict, ranges: dict[str, tuple[float, float]]) -> pd.DataFrame:
    """One-at-a-time: swing each parameter to its low/high value with the rest at base."""
    f0 = fn(base)
    rows = []
    for k, (lo, hi) in ranges.items():
        flo, fhi = fn({**base, k: lo}), fn({**base, k: hi})
        rows.append(dict(parameter=k, low=lo, high=hi, f_low=flo, f_high=fhi, base=f0, swing=abs(fhi - flo)))
    return pd.DataFrame(rows).sort_values("swing", ascending=False).reset_index(drop=True)
