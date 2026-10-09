"""Leakage guard: causal-availability checks for features and subject-grouped splits."""
from __future__ import annotations

import numpy as np
import pandas as pd

from iris.common.exceptions import LeakageError

#: Same-day glucose summaries are excluded from explanatory TDD models (glucose-insulin leakage under AID).
SAME_DAY_GLUCOSE_FEATURES = ("mean_glucose_mgdl", "tir_pct", "tbr_pct", "tar_pct", "cgm_coverage")


def check_feature_availability(feature_names: list[str], availability: dict[str, str], prediction_time: str = "day_start",
                               target_is_tdd: bool = False) -> None:
    """``availability[name]`` in {'past','known_at_prediction','same_day','future'}; reject same-day/future features."""
    bad = [f for f in feature_names if availability.get(f, "unknown") in ("future", "unknown")]
    if bad:
        raise LeakageError(f"features with future/unknown availability rejected: {bad}")
    same = [f for f in feature_names if availability.get(f) == "same_day"]
    if same:
        raise LeakageError(f"same-day features rejected for prediction at {prediction_time}: {same}")
    if target_is_tdd:
        g = [f for f in feature_names if f in SAME_DAY_GLUCOSE_FEATURES]
        if g:
            raise LeakageError(f"same-day glucose summaries leak into TDD targets (AID loop): {g}")


def lag_features(df: pd.DataFrame, cols: list[str], group: str, time: str, lags: int = 1) -> pd.DataFrame:
    """Create strictly lagged (past-only) copies of columns within each group."""
    out = df.sort_values([group, time]).copy()
    for c in cols:
        for k in range(1, lags + 1):
            out[f"{c}_lag{k}"] = out.groupby(group)[c].shift(k)
    return out


def assert_group_disjoint(train_groups, test_groups) -> None:
    inter = set(train_groups) & set(test_groups)
    if inter:
        raise LeakageError(f"{len(inter)} subject(s) appear in both train and test: {sorted(map(str, inter))[:5]}")


def assert_no_future_rows(train_times, test_times, same_subject: bool = False) -> None:
    if same_subject and np.max(np.asarray(train_times)) >= np.min(np.asarray(test_times)):
        raise LeakageError("training data extend into the test period for the same subject")


def subject_identity_canary(model_factory, X: pd.DataFrame, y: np.ndarray, groups: np.ndarray, rng: np.random.Generator,
                            tol: float = 0.1, cv_predict=None) -> dict:
    """Leakage canary: a target made of PURE subject-identity noise should NOT be predictable on held-out subjects.
    Predictability above ``tol`` R^2 under grouped CV means identity leaks across the split."""
    from iris.evaluate.cv import grouped_cv_predict
    cv_predict = cv_predict or grouped_cv_predict
    per_subject = {g: rng.standard_normal() for g in np.unique(groups)}
    y_noise = np.array([per_subject[g] for g in groups])
    pred = cv_predict(model_factory, X, y_noise, groups, n_splits=min(5, len(np.unique(groups))))
    r2 = 1.0 - np.sum((y_noise - pred) ** 2) / np.sum((y_noise - y_noise.mean()) ** 2)
    return {"canary_r2": float(r2), "leak_detected": bool(r2 > tol)}
