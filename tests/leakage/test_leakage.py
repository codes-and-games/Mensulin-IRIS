import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestRegressor

from iris.common.exceptions import LeakageError
from iris.evaluate.cv import grouped_cv_predict
from iris.evaluate.leakage import rowwise_split_leak_demo, verify_grouped_split
from iris.features import leakage_guard as lg


def test_identity_canary_quiet_under_grouped_cv_and_loud_under_row_split():
    rng = np.random.default_rng(0)
    g = np.repeat(np.arange(15), 30)
    ids = pd.get_dummies(pd.Series(g)).astype(float)
    mk = lambda: RandomForestRegressor(n_estimators=30, min_samples_leaf=3, random_state=0)
    assert not lg.subject_identity_canary(mk, ids, np.zeros(len(g)), g, rng)["leak_detected"]

    def row_cv(model_factory, X, y, groups, n_splits=5):
        pred = np.full(len(y), np.nan); idx = rng.permutation(len(y))
        Xa = np.asarray(X)
        for f in np.array_split(idx, n_splits):
            tr = np.setdiff1d(idx, f); pred[f] = model_factory().fit(Xa[tr], y[tr]).predict(Xa[f])
        return pred
    assert lg.subject_identity_canary(mk, ids, np.zeros(len(g)), g, rng, cv_predict=row_cv)["leak_detected"]


def test_rowwise_split_shares_subjects_but_grouped_does_not():
    g = np.repeat(np.arange(10), 20)
    assert rowwise_split_leak_demo(g, np.random.default_rng(1))["shared_subjects"] > 0
    assert verify_grouped_split(g)["disjoint"]


def test_future_rows_rejected():
    with pytest.raises(LeakageError):
        lg.assert_no_future_rows([1, 2, 5], [3, 4], same_subject=True)
