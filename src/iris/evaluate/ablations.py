"""Ablations A1-A5 (document 16.2). Each takes the population arrays and returns the modified arrays.

A1 no thermal   : P = 1 everywhere          A2 no cycle : S = 1, rho = 1
A3 mean-only    : population-mean biology     A4 circularity control: rho = proportional to 1/S (explicit allow flag)
A5 deterministic: potency fixed at its mean across draws
"""
from __future__ import annotations

import numpy as np

from iris.fusion import controls


def a1_no_thermal(p): return controls.control_c1_no_loss(p)
def a2_no_cycle(s, rho): return controls.control_c2_no_cycle(s, rho)
def a3_mean_biology(r_u): return controls.control_c5_mean_biology(r_u)
def a5_deterministic_potency(ell): return controls.control_c4_deterministic_potency(ell)


def a4_circular(s: np.ndarray) -> np.ndarray:
    """rho proportional to 1/S (normalised to cycle mean 1). CONTROL ONLY: demonstrates how circularity pushes
    the phi ratio toward 1; never used for any reported primary result."""
    inv = 1.0 / np.asarray(s, float)
    return inv / inv.mean(axis=1, keepdims=True)
