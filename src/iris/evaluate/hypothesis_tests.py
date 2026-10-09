"""Preregistered-style tests: permutation tests and placebo-cycle controls (document 9.4)."""
from __future__ import annotations

import numpy as np


def permutation_pvalue(stat_fn, data: np.ndarray, rng: np.random.Generator, n_perm: int = 999, seed_stat=None) -> float:
    obs = stat_fn(data) if seed_stat is None else seed_stat
    ge = sum(stat_fn(rng.permutation(data)) >= obs for _ in range(n_perm))
    return (ge + 1) / (n_perm + 1)


def placebo_cycle_amplitudes(daily_values: np.ndarray, cycle_starts: list[int], amp_fn, rng: np.random.Generator,
                             n_rep: int = 200) -> np.ndarray:
    """Shift cycle starts randomly (cyclic rotation of the series) and recompute the amplitude statistic."""
    v = np.asarray(daily_values, float)
    return np.array([amp_fn(np.roll(v, int(rng.integers(1, len(v))))) for _ in range(n_rep)])
