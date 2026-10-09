"""Leakage checks used by M4: grouped split verification, future-feature rejection, identity canary."""
from __future__ import annotations

import numpy as np
import pandas as pd

from iris.evaluate.cv import grouped_splits
from iris.features.leakage_guard import assert_group_disjoint, subject_identity_canary


def verify_grouped_split(groups) -> dict:
    n = 0
    for tr, te in grouped_splits(np.asarray(groups), 5):
        assert_group_disjoint(np.asarray(groups)[tr], np.asarray(groups)[te]); n += 1
    return {"folds_checked": n, "disjoint": True}


def rowwise_split_leak_demo(groups, rng: np.random.Generator, test_frac=0.3) -> dict:
    """Shows (for the leakage report) that a ROW-level split mixes subjects across train and test."""
    g = np.asarray(groups); idx = rng.permutation(len(g)); te = idx[: int(test_frac * len(g))]; tr = idx[int(test_frac * len(g)):]
    return {"shared_subjects": len(set(g[tr]) & set(g[te])), "total_subjects": len(set(g))}
