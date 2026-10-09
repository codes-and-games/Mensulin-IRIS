"""M3: leave-one-subject-out generalisation of the baselines and optional tree benchmark; row-level splitting is not available."""
import numpy as np
import pandas as pd

from iris.common.provenance import EvidenceClass
from iris.estimator.baselines import HarmonicRegression, NaiveMean
from iris.estimator.ml_benchmarks import random_forest
from iris.estimator.targets import t1_relative_tdd
from iris.evaluate.cv import grouped_cv_scores
from iris.features.cycle import harmonic_features
from iris.features.person_day import finalize_person_day
from iris.tools import experiment_lib as xl


def run(ctx):
    raw, prov = xl.load_person_day(ctx, with_cycle_labels=True)
    pdf = finalize_person_day(raw.drop(columns=[c for c in ["isf_clinician"] if c in raw]))
    y = t1_relative_tdd(pdf); ok = y.notna() & pdf["cycle_pos"].notna()
    if not ok.any():
        from iris.common.exceptions import ScientificBlocker
        raise ScientificBlocker("cycle_labels", "no cycle labels", "needs a labelled dataset")
    X = harmonic_features(pdf.loc[ok, "cycle_pos"].to_numpy(), 2); yv, g = y[ok].to_numpy(), pdf.loc[ok, "person_id"].to_numpy()
    rows = []
    for name, f in (("naive", lambda: NaiveMean()), ("harmonic_K2", lambda: HarmonicRegression()), ("random_forest_benchmark", lambda: random_forest(int(ctx.cfg["seed"]), n_estimators=60))):
        rows.append(dict(model=name, scheme="LeaveOneGroupOut", **grouped_cv_scores(f, X, yv, g, None)))
    ctx.save_table(pd.DataFrame(rows), "loso_scores", [xl.derived_prov(ctx, prov[:1], EvidenceClass.COMPUTED, "loso_scores", "LOGO CV", "iris.evaluate.cv")])
