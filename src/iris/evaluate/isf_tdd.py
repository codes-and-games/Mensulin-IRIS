"""Empirical ISF-TDD relationship: ln(ISF) = a + b ln(TDD) (+ person random intercept optional).

IMPORTANT: ISF here is a CLINICIAN/PUMP-SET parameter, not a measurement of physiological sensitivity. The slope describes
how settings relate to dose, and cannot validate the 1500-1800/TDD rule as physiology. Slope b = -1 corresponds to ISF ∝ 1/TDD."""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from iris.common.exceptions import NumericalError, ScientificBlocker


def isf_tdd_fit(df: pd.DataFrame, isf_col: str = "isf_clinician", person: str = "person_id", min_persons: int = 10) -> dict:
    if isf_col not in df.columns or df[isf_col].notna().sum() == 0:
        raise ScientificBlocker("isf_setting", "no ISF settings column in the data", "dataset must report pump/clinician ISF; keep glucose-equivalent analysis model-conditional otherwise")
    d = df[[person, "tdd_u", isf_col]].dropna()
    pm = d.groupby(person).agg(tdd=("tdd_u", "mean"), isf=(isf_col, "median")).reset_index()
    if len(pm) < min_persons:
        raise ScientificBlocker("isf_tdd", f"only {len(pm)} persons (< {min_persons})", "more persons with ISF settings")
    x, y = np.log(pm["tdd"].to_numpy()), np.log(pm["isf"].to_numpy())
    res = sm.OLS(y, sm.add_constant(x)).fit(cov_type="HC3")
    lo, hi = res.conf_int()[1]
    resid_sd = float(np.std(res.resid, ddof=2))
    return {"n_persons": int(len(pm)), "slope": float(res.params[1]), "slope_ci_low": float(lo), "slope_ci_high": float(hi), "intercept": float(res.params[0]),
            "residual_sd_ln": resid_sd, "consistent_with_minus_one": bool(lo <= -1.0 <= hi),
            "caveat": "ISF is a clinician-set parameter, not measured physiology"}
