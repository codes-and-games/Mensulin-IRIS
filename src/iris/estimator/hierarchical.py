"""Mixed-effects model for daily outcomes: y = b0 + sum_k (a_k cos + b_k sin) + person random intercept (+ random slopes).

statsmodels MixedLM; hierarchical Bayesian variants (PyMC/NumPyro) are optional extras and not required here.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from iris.common.exceptions import NumericalError


def fit_harmonic_mixed(df: pd.DataFrame, y: str, person: str, x_col: str, K: int = 1, random_slopes: bool = False):
    d = df[[y, person, x_col]].dropna().copy()
    if d[person].nunique() < 3:
        raise NumericalError("need >= 3 persons for a mixed model")
    terms = []
    for k in range(1, K + 1):
        d[f"c{k}"], d[f"s{k}"] = np.cos(2 * np.pi * k * d[x_col]), np.sin(2 * np.pi * k * d[x_col])
        terms += [f"c{k}", f"s{k}"]
    fixed = f"{y} ~ " + " + ".join(terms)
    re = "~" + " + ".join(terms) if random_slopes else None
    model = smf.mixedlm(fixed, d, groups=d[person], re_formula=re)
    res = model.fit(reml=True, method="lbfgs")
    amp = {f"A{k}": float(np.hypot(res.fe_params[f"c{k}"], res.fe_params[f"s{k}"])) for k in range(1, K + 1)}
    return res, amp
