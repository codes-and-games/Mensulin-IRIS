"""Simple, interpretable baselines: naive (person mean), person-mean + harmonic regression, ridge."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.linear_model import LinearRegression, Ridge


class NaiveMean(BaseEstimator, RegressorMixin):
    """Predicts the training-set mean (the 'no information' baseline for held-out subjects)."""
    def fit(self, X, y):
        self.mu_ = float(np.mean(y)); return self
    def predict(self, X):
        return np.full(len(X), self.mu_)


class HarmonicRegression(BaseEstimator, RegressorMixin):
    """OLS on [cos k phi, sin k phi] columns (features already harmonic-encoded by features.cycle)."""
    def __init__(self, alpha: float = 0.0):
        self.alpha = alpha
    def fit(self, X, y):
        self.m_ = (Ridge(alpha=self.alpha) if self.alpha > 0 else LinearRegression()).fit(X, y); return self
    def predict(self, X):
        return self.m_.predict(X)
