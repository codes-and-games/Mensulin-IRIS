"""Candidate targets T1-T5 from person-day tables (document 8.2). T7 (1800/TDD) is REJECTED as a data target."""
from __future__ import annotations

import numpy as np
import pandas as pd

from iris.common.exceptions import IrisError


def t1_relative_tdd(df: pd.DataFrame) -> pd.Series:
    """TDD relative to the person's mean TDD over included days. Reflects controller behaviour under AID."""
    ok = df[~df["exclude_flag"]]
    mean = ok.groupby("person_id")["tdd_u"].transform("mean")
    return (df["tdd_u"] / mean.reindex(df.index)).rename("t1_rel_tdd")


def t2_carb_adjusted(df: pd.DataFrame, min_carb_g: float) -> pd.Series:
    """Insulin per gram of logged carbohydrate; undefined (NaN) when carbohydrate logging is missing/low."""
    c = df["carb_g"].where(df["carb_g"] >= min_carb_g)
    return (df["bolus_u"] / c).rename("t2_bolus_per_g")


def t3_basal_fraction(df: pd.DataFrame) -> pd.Series:
    return (df["basal_u"] / df["tdd_u"]).rename("t3_basal_fraction")


def t7_rule_of_thumb(*args, **kwargs):
    raise IrisError("T7 (rule-of-thumb sensitivity K/TDD) is circular and REJECTED as a data target; "
                    "it is used only in the glucose-equivalent conversion")
