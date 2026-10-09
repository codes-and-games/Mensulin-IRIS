"""M1: baseline suite (naive person-free mean; harmonic regression on cycle position) with subject-grouped CV for target T1 (relative TDD).
Cycle-based baselines need real cycle labels: without them they are BLOCKED and ONLY the naive baseline is reported (no cycle biology claimed)."""
import numpy as np
import pandas as pd

from iris.common.provenance import EvidenceClass
from iris.estimator.baselines import HarmonicRegression, NaiveMean
from iris.estimator.targets import t1_relative_tdd
from iris.evaluate.cv import grouped_cv_scores
from iris.features.cycle import harmonic_features
from iris.features.person_day import finalize_person_day
from iris.tools import experiment_lib as xl


def run(ctx):
    raw, prov = xl.load_person_day(ctx, with_cycle_labels=True)
    pdf = finalize_person_day(raw.drop(columns=[c for c in ["isf_clinician"] if c in raw]))
    y = t1_relative_tdd(pdf); ok = y.notna()
    groups = pdf.loc[ok, "person_id"].to_numpy(); yv = y[ok].to_numpy()
    base = xl.derived_prov(ctx, prov[:1], EvidenceClass.COMPUTED, "baseline_scores", "grouped CV baselines on T1", "iris.estimator.baselines")
    rows = []
    X0 = np.zeros((len(yv), 1))
    rows.append(dict(model="M0_naive_mean", **grouped_cv_scores(lambda: NaiveMean(), X0, yv, groups, ctx.cfg["cv"]["n_splits"])))
    pos = pdf.loc[ok, "cycle_pos"].to_numpy()
    if np.isfinite(pos).any():
        has = np.isfinite(pos)
        X = harmonic_features(pos[has], int(ctx.cfg["cv"]["K"]))
        rows.append(dict(model="M3_harmonic_cycle", **grouped_cv_scores(lambda: HarmonicRegression(), X, yv[has], groups[has], ctx.cfg["cv"]["n_splits"])))
    else:
        ctx.blockers.append(dict(part="M3_harmonic_cycle", reason="no cycle labels in the data: cycle baselines not evaluated"))
    ctx.save_table(pd.DataFrame(rows), "baseline_scores", [base])
