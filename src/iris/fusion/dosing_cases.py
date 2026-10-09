"""Dosing cases and ISF models applied to arrays. Consumes stored population/potency tables only."""
from __future__ import annotations

import numpy as np

from iris.common.exceptions import NumericalError

from . import analytic as an

ISF_MODELS = ("K_over_tdd_times_S", "K_over_R_phase")


def shortfall_units(case: str, r_u: np.ndarray, tdd_u: np.ndarray, p) -> np.ndarray:
    """delta_u for dosing case 'A' (D = R) or 'B' (D = cycle-average requirement = TDD)."""
    if case == "A":
        return an.shortfall_case_a(r_u, p)
    if case == "B":
        return an.shortfall_case_b(r_u, tdd_u[:, None] if np.ndim(r_u) == 2 else tdd_u, p)
    raise NumericalError(f"unknown dosing case {case!r}")


def isf(model: str, k_const: float, tdd_u: np.ndarray, s: np.ndarray, r_u: np.ndarray) -> np.ndarray:
    if model == "K_over_tdd_times_S":
        t = tdd_u[:, None] if s.ndim == 2 else tdd_u
        return an.isf_k_over_tdd_times_s(k_const, t, s)
    if model == "K_over_R_phase":
        return an.isf_k_over_requirement(k_const, r_u)
    raise NumericalError(f"unknown ISF model {model!r}")


def glucose_shortfall(delta_u: np.ndarray, isf_arr: np.ndarray) -> np.ndarray:
    """delta_g = delta_u * ISF (model-conditional, secondary)."""
    return delta_u * isf_arr
