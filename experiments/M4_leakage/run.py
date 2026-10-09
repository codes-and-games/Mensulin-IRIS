"""M4: explicit leakage tests. (1) grouped splits are subject-disjoint; (2) a ROW-level split demonstrably leaks subjects (the failure the design prevents);
(3) future / same-day features are rejected; (4) the identity canary: a pure-subject-identity target must be unpredictable on held-out subjects under grouped CV
and PREDICTABLE under a leaky row-level scheme (proving the canary can detect leakage)."""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from iris.common.exceptions import LeakageError
from iris.common.provenance import EvidenceClass
from iris.evaluate.leakage import rowwise_split_leak_demo, verify_grouped_split
from iris.features import leakage_guard as lg
from iris.tools import experiment_lib as xl


def run(ctx):
    raw, prov = xl.load_person_day(ctx, with_cycle_labels=False)
    g = raw["person_id"].to_numpy(); rng = ctx.rng.generator("M4")
    rows = [dict(test="grouped_split_disjoint", **verify_grouped_split(g), passed=True)]
    demo = rowwise_split_leak_demo(g, rng); rows.append(dict(test="rowwise_split_leaks_subjects(demonstration)", **demo, passed=demo["shared_subjects"] > 0))
    for name, avail, tdd in (("future_feature", {"x": "future"}, False), ("same_day_feature", {"x": "same_day"}, False), ("same_day_glucose_for_tdd", {"mean_glucose_mgdl": "past"}, True)):
        feats = ["x"] if "x" in avail else ["mean_glucose_mgdl"]
        try:
            lg.check_feature_availability(feats, avail, target_is_tdd=tdd); rows.append(dict(test=f"reject_{name}", passed=False))
        except LeakageError:
            rows.append(dict(test=f"reject_{name}", passed=True))
    X = pd.DataFrame({"noise": rng.standard_normal(len(g))})
    ids = pd.get_dummies(raw["person_id"]).astype(float)                      # subject-identity features (the leak)
    mk = lambda: RandomForestRegressor(n_estimators=40, min_samples_leaf=3, random_state=0)
    clean = lg.subject_identity_canary(mk, X, np.zeros(len(g)), g, rng)
    from iris.evaluate.cv import grouped_cv_predict
    def rowwise_predict(model_factory, Xm, y, groups, n_splits=5):
        pred = np.full(len(y), np.nan); idx = rng.permutation(len(y)); folds = np.array_split(idx, n_splits)
        Xa = Xm.to_numpy() if hasattr(Xm, "to_numpy") else np.asarray(Xm)
        for f in folds:
            tr = np.setdiff1d(idx, f); m = model_factory().fit(Xa[tr], y[tr]); pred[f] = m.predict(Xa[f])
        return pred
    leaky = lg.subject_identity_canary(mk, ids, np.zeros(len(g)), g, rng, cv_predict=rowwise_predict)
    rows.append(dict(test="canary_grouped_cv_no_leak", canary_r2=clean["canary_r2"], passed=not clean["leak_detected"]))
    rows.append(dict(test="canary_detects_rowwise_identity_leak", canary_r2=leaky["canary_r2"], passed=leaky["leak_detected"]))
    df = pd.DataFrame(rows)
    ctx.save_table(df, "leakage_tests", [xl.derived_prov(ctx, prov[:1], EvidenceClass.COMPUTED, "leakage_tests", "grouped-CV leakage checks and canary", "iris.evaluate.leakage")])
    if not df["passed"].all():
        ctx.log.warn("FAILED_CONTROL: leakage test(s) failed: " + ", ".join(df.loc[~df.passed, "test"]))
