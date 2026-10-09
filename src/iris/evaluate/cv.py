"""Subject-level grouped cross-validation. Row-level splitting is never offered."""
from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut

from iris.common.exceptions import LeakageError
from iris.features.leakage_guard import assert_group_disjoint


def grouped_splits(groups: np.ndarray, n_splits: int | None = 5):
    """Yield (train_idx, test_idx) with disjoint subjects. ``n_splits=None`` => leave-one-group-out."""
    g = np.asarray(groups)
    if len(np.unique(g)) < 2:
        raise LeakageError("need >= 2 subjects for grouped validation")
    splitter = LeaveOneGroupOut() if n_splits is None else GroupKFold(n_splits=min(n_splits, len(np.unique(g))))
    for tr, te in splitter.split(np.zeros(len(g)), groups=g):
        assert_group_disjoint(g[tr], g[te])
        yield tr, te


def grouped_cv_predict(model_factory: Callable, X, y, groups, n_splits: int | None = 5) -> np.ndarray:
    X = X.to_numpy() if isinstance(X, pd.DataFrame) else np.asarray(X)
    y = np.asarray(y, float)
    pred = np.full(len(y), np.nan)
    for tr, te in grouped_splits(groups, n_splits):
        m = model_factory()
        m.fit(X[tr], y[tr])
        pred[te] = m.predict(X[te])
    return pred


def grouped_cv_scores(model_factory, X, y, groups, n_splits=5) -> dict:
    pred = grouped_cv_predict(model_factory, X, y, groups, n_splits)
    y = np.asarray(y, float)
    ok = np.isfinite(pred) & np.isfinite(y)
    res = y[ok] - pred[ok]
    return {"rmse": float(np.sqrt(np.mean(res ** 2))), "mae": float(np.mean(np.abs(res))),
            "r2": float(1 - np.sum(res ** 2) / np.sum((y[ok] - y[ok].mean()) ** 2)), "n": int(ok.sum())}
