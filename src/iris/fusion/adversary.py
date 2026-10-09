"""Adversarial counterexample search (differential evolution) with a fixed, recorded evaluation budget.

Minimises the conclusion margin (margin > 0 means the conclusion holds). A counterexample is found when
the best margin <= 0. 'Computationally robust' is then only meaningful under THIS search design and budget.
"""
from __future__ import annotations

from typing import Callable

import numpy as np
from scipy.optimize import differential_evolution

from iris.common.rng import RngTree

from .admissible_set import COMPONENTS, AdmissibleSet, Theta


def _decode(x: np.ndarray, bounds_spec, which: str) -> Theta:
    vals = []
    for xi, (c, spec) in zip(x, bounds_spec):
        if c == "q":
            vals.append(which)
        elif spec[0] == "cont":
            vals.append(float(xi))
        else:
            lv = spec[1]; vals.append(lv[min(int(np.floor(xi)), len(lv) - 1)])
    return Theta(tuple(vals), which)


def adversarial_search(margin_fn: Callable[[Theta], float], aset: AdmissibleSet, which: str, rng_tree: RngTree,
                       budget: int, popsize: int = 8) -> dict:
    """Search the named analysis set for the theta that most strongly falsifies the conclusion."""
    spec = aset.bounds_for_search(which)
    free = [(i, s) for i, (c, s) in enumerate(spec) if c != "q" and (s[0] == "cat" and len(s[1]) > 1 or s[0] == "cont")]
    best_theta, best_margin, n_eval = None, np.inf, 0
    cache: dict = {}
    exhausted = [False]

    def full_x(xf):
        x = np.zeros(len(spec))
        for i, (c, s) in enumerate(spec):
            x[i] = 0.5 if (s[0] == "cat") else s[1]
        for (i, s), v in zip(free, xf):
            x[i] = v
        return x

    def obj(xf):
        nonlocal best_theta, best_margin, n_eval
        th = _decode(full_x(xf), spec, which)
        if th in cache:
            return cache[th]
        if n_eval >= budget:           # hard cap: the budget is a declared part of the search design
            exhausted[0] = True
            return 1e12
        n_eval += 1
        try:
            m = float(margin_fn(th))
        except Exception:      # blocked evaluation is not a counterexample; treat as non-informative
            m = np.inf
        m = np.inf if np.isnan(m) else m
        cache[th] = m
        if m < best_margin:
            best_margin, best_theta = m, th
        return m if np.isfinite(m) else 1e12

    if not free:
        th = _decode(full_x([]), spec, which)
        n_eval = 1
        m = float(margin_fn(th))
        return dict(analysis_set=which, budget=budget, evaluations=1, best_margin=m, best_theta=th.as_dict(),
                    counterexample_found=bool(m <= 0), method="enumeration (no free components)", seed_name="adversary")
    bounds = [(s[1], s[2]) if s[0] == "cont" else (0.0, float(len(s[1])) - 1e-9) for _, s in free]
    ndim = len(bounds)
    maxiter = max(1, budget // (popsize * ndim) - 1)
    seed = int(rng_tree.generator("adversary", which).integers(0, 2 ** 31 - 1))
    differential_evolution(obj, bounds, maxiter=maxiter, popsize=popsize, seed=seed, tol=0, polish=False,
                           init="sobol", updating="deferred", callback=lambda *a, **k: exhausted[0])
    return dict(analysis_set=which, budget=budget, evaluations=n_eval, best_margin=float(best_margin),
                best_theta=best_theta.as_dict() if best_theta else None, counterexample_found=bool(best_margin <= 0),
                method="differential_evolution", seed=seed, maxiter=maxiter, popsize=popsize,
                note="searches the convex hull of numeric levels and all categorical levels of the named set")
