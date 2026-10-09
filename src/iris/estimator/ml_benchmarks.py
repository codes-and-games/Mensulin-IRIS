"""Tree-based benchmarks (only where specified). Interpretability and calibration take priority over scores."""
from __future__ import annotations

from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor


def random_forest(seed: int, **kw):
    return RandomForestRegressor(n_estimators=kw.get("n_estimators", 200), min_samples_leaf=kw.get("min_samples_leaf", 5),
                                 random_state=seed, n_jobs=1)


def gradient_boosting(seed: int, **kw):
    return GradientBoostingRegressor(random_state=seed, n_estimators=kw.get("n_estimators", 200), max_depth=kw.get("max_depth", 2),
                                     learning_rate=kw.get("learning_rate", 0.05))
