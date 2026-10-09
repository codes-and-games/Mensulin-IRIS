"""Calibration of xi_sd (and eta where a target exists) to PUBLISHED phase-variance targets.

Targets are inputs; with no target the functions raise ScientificBlocker rather than choose a value.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import brentq

from iris.common.exceptions import ScientificBlocker
from iris.common.rng import RngTree

from .generator import PopulationSpec, generate, phase_matrix


def calibrate_xi_sd(spec: PopulationSpec, target_sd_ln_rho: float | None, rng_tree: RngTree, hi: float = 1.0,
                    n: int = 4000) -> float:
    """Find xi_sd so that the pooled SD of ln rho matches a published target (e.g. TDD phase variability)."""
    if target_sd_ln_rho is None:
        raise ScientificBlocker("target_sd_ln_rho", "no published TDD phase-variance target supplied",
                                "extract the phase-profile variance of TDD from the anchor study")
    import copy

    def f(xi):
        sp = copy.copy(spec); sp.xi_sd = float(xi); sp.n = n
        df = generate(sp, rng_tree.child("calibrate"))
        return float(np.log(phase_matrix(df, "rho_p")).std(axis=1).mean()) - target_sd_ln_rho

    lo_val = f(1e-6)
    if lo_val > 0:
        raise ScientificBlocker("xi_sd", "target below the variability already induced by gamma and eta",
                                "target unattainable with xi_sd >= 0 under the chosen structure")
    return brentq(f, 1e-6, hi, xtol=1e-4)
