"""M7: first supervised ML benchmark: predict a person's NEXT-DAY observed total daily dose (TDD) from past-only features.
Target = TDD(day t) relative to the person's trailing 7-day mean TDD (days < t); predictions are converted back to units/day and scored
against persistence (P1: yesterday), the trailing mean (P7) and a naive training mean (M0) under participant-held-out CV
(LeaveOneGroupOut = primary, GroupKFold = secondary). Person-clustered bootstrap CIs, a within-person shuffled-target placebo and a
fixed verdict rule (config) keep the claim honest. No cycle labels are used: this says NOTHING about the menstrual cycle, and TDD under
automated insulin delivery reflects controller behaviour as well as physiology."""
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from iris.common.exceptions import ScientificBlocker
from iris.common.provenance import EvidenceClass
from iris.estimator.baselines import NaiveMean
from iris.estimator.ml_benchmarks import gradient_boosting, random_forest
from iris.evaluate.cluster_bootstrap import cluster_bootstrap_skill
from iris.evaluate.cv import grouped_cv_predict, grouped_splits
from iris.features import leakage_guard as lg
from iris.features.next_day import CANDIDATE_FEATURES, FEATURE_AVAILABILITY, build_next_day_table
from iris.tools import experiment_lib as xl

SIMPLE = ("M0_naive_mean", "P1_persistence", "P7_trailing_mean")
ML = ("R1_ridge_ratio", "R2_random_forest_ratio", "R3_gradient_boosting_ratio")


def _metrics(y, p) -> dict:
    e = y - p
    return {"n": int(len(y)), "rmse_u": float(np.sqrt(np.mean(e ** 2))), "mae_u": float(np.mean(np.abs(e))),
            "mape_pct": float(100 * np.mean(np.abs(e) / y)), "bias_u": float(np.mean(e)),
            "r2_u": float(1 - np.sum(e ** 2) / np.sum((y - y.mean()) ** 2))}


def _placebo_predict(factory, X, ratio, groups, n_splits, rng):
    """Train on targets shuffled WITHIN each training person (temporal link destroyed), test on the true held-out people."""
    Xa = X.to_numpy(float); pred = np.full(len(ratio), np.nan)
    for tr, te in grouped_splits(groups, n_splits):
        ytr = ratio[tr].copy(); gtr = groups[tr]
        for pid in np.unique(gtr):
            ix = np.where(gtr == pid)[0]; ytr[ix] = rng.permutation(ytr[ix])
        pred[te] = factory().fit(Xa[tr], ytr).predict(Xa[te])
    return pred


def run(ctx):
    cfg = ctx.cfg
    raw, prov = xl.load_person_day(ctx, with_cycle_labels=False)
    tab, counts = build_next_day_table(raw, int(cfg["features"]["window_days"]), int(cfg["features"]["min_history_days"]))
    base = lambda sid, what: xl.derived_prov(ctx, prov[:1], EvidenceClass.COMPUTED, sid, what, "iris.features.next_day / experiments.M7")
    for k, v in counts.items():
        if k.startswith(("excluded", "included")) and v:
            ctx.log.exclude(f"{v} person-days: {k}")

    # ---- cohort flow (per dataset) --------------------------------------------------------------------------------------------
    n_min = int(cfg["min_rows_per_person"])
    per = tab.groupby("person_id").size()
    small = per[per < n_min].index
    if len(small):
        ctx.log.exclude(f"{len(small)} persons with < {n_min} eligible next-day rows removed from M7")
    tab = tab[~tab["person_id"].isin(small)].reset_index(drop=True)
    flow = [dict(dataset="ALL", stage=k, n=v) for k, v in counts.items()]
    for ds, t in tab.groupby("dataset"):
        flow += [dict(dataset=ds, stage="m7_people", n=int(t["person_id"].nunique())), dict(dataset=ds, stage="m7_rows", n=int(len(t)))]
    ctx.save_table(pd.DataFrame(flow), "cohort_flow", [base("m7_cohort_flow", "inclusion counts for the next-day table")])
    if tab["person_id"].nunique() < 6:
        raise ScientificBlocker("m7_cohort", "fewer than 6 participants with usable consecutive-day TDD history", "ingest more person-days or lower min_rows_per_person with a recorded decision")

    # ---- feature audit + leakage guard ----------------------------------------------------------------------------------------
    miss = tab.groupby("dataset")[list(CANDIDATE_FEATURES)].apply(lambda d: d.isna().mean()).T
    keep = [f for f in CANDIDATE_FEATURES if miss.loc[f].max() <= float(cfg["features"]["max_feature_missing"])]
    for f in set(CANDIDATE_FEATURES) - set(keep):
        ctx.log.warn(f"feature dropped (missing > {cfg['features']['max_feature_missing']} in some dataset): {f}")
    audit = miss.reset_index().rename(columns={"index": "feature"}).assign(kept=lambda d: d["feature"].isin(keep))
    ctx.save_table(audit, "feature_audit", [base("m7_feature_audit", "missing fraction per feature and dataset")])
    lg.check_feature_availability(keep, FEATURE_AVAILABILITY, prediction_time="day_start", target_is_tdd=True)

    # ---- design ---------------------------------------------------------------------------------------------------------------
    y = tab["y_tdd_u"].to_numpy(float); roll = tab["roll7_mean_tdd_u"].to_numpy(float); ratio = y / roll
    g = tab["person_id"].to_numpy(); X = tab[keep]; n = len(y)
    seed, ne = int(cfg["seed"]), int(cfg["models"]["n_estimators"])
    imp = lambda: SimpleImputer(strategy="median")
    fac = {"R1_ridge_ratio": lambda: make_pipeline(imp(), StandardScaler(), Ridge(alpha=float(cfg["models"]["ridge_alpha"]))),
           "R2_random_forest_ratio": lambda: make_pipeline(imp(), random_forest(seed, n_estimators=ne)),
           "R3_gradient_boosting_ratio": lambda: make_pipeline(imp(), gradient_boosting(seed, n_estimators=ne))}
    schemes = [("GroupKFold", int(cfg["cv"]["n_splits"])), ("LeaveOneGroupOut", None)]
    primary = cfg["cv"]["primary"]
    min_skill = float(cfg["min_skill"])
    B = int(cfg["bootstrap"]["B"]); rng = ctx.rng.generator("M7", "bootstrap")

    score_rows, verdict_rows, primary_pred = [], [], None
    for sname, ns in schemes:
        P = {"M0_naive_mean": grouped_cv_predict(lambda: NaiveMean(), np.zeros((n, 1)), y, g, ns),
             "P1_persistence": tab["lag1_tdd_u"].to_numpy(float), "P7_trailing_mean": roll}
        for name, f in fac.items():
            P[name] = grouped_cv_predict(f, X, ratio, g, ns) * roll
        ae = {k: np.abs(y - v) for k, v in P.items()}
        best = min(("P1_persistence", "P7_trailing_mean"), key=lambda k: ae[k].mean())
        for name, p in P.items():
            row = dict(scheme=sname, model=name, **_metrics(y, p))
            for bname in ("P1_persistence", "P7_trailing_mean"):
                b = cluster_bootstrap_skill(g, ae[name], ae[bname], rng, B)
                row.update({f"skill_vs_{bname[:2]}_mae": b["skill"], f"skill_vs_{bname[:2]}_lo": b["ci_lo"], f"skill_vs_{bname[:2]}_hi": b["ci_hi"]})
            score_rows.append(row)
            if name in ML:
                b = cluster_bootstrap_skill(g, ae[name], ae[best], rng, B)
                verdict_rows.append(dict(scheme=sname, model=name, baseline=best, skill_mae=b["skill"], ci_lo=b["ci_lo"], ci_hi=b["ci_hi"],
                                         n_people=b["n_people"], primary=(sname == primary), ml_beats_best_simple_baseline=bool(b["ci_lo"] > 0 and b["skill"] >= min_skill)))
        if sname == primary:
            primary_pred = P
    ctx.save_table(pd.DataFrame(score_rows), "scores", [base("m7_scores", "participant-held-out CV scores with clustered bootstrap CIs")])
    verdict = pd.DataFrame(verdict_rows)
    ctx.save_table(verdict, "verdict", [base("m7_verdict", "fixed-rule comparison against the better simple baseline")])

    # ---- breakdowns on the primary scheme -------------------------------------------------------------------------------------
    P = primary_pred
    ds_rows, pp_rows = [], []
    for ds in sorted(tab["dataset"].unique()):
        m = (tab["dataset"] == ds).to_numpy()
        for name, p in P.items():
            ds_rows.append(dict(dataset=ds, model=name, n_people=int(len(np.unique(g[m]))), **_metrics(y[m], p[m])))
    for pid in np.unique(g):
        m = g == pid
        pp_rows.append(dict(person_id=pid, dataset=tab.loc[m, "dataset"].iloc[0], n=int(m.sum()), **{f"mae_{k}": float(np.mean(np.abs(y[m] - v[m]))) for k, v in P.items()}))
    ctx.save_table(pd.DataFrame(ds_rows), "scores_by_dataset", [base("m7_scores_by_dataset", "primary-scheme scores per dataset")])
    ctx.save_table(pd.DataFrame(pp_rows), "scores_by_person", [base("m7_scores_by_person", "primary-scheme MAE per participant")])
    pred = tab[["dataset", "person_id", "date_local", "y_tdd_u"]].copy()
    for k, v in P.items():
        pred[f"pred_{k}"] = v
    ctx.save_table(pred, "predictions", [base("m7_predictions", "out-of-fold predictions (primary scheme)")])

    # ---- placebo: shuffled targets must not manufacture skill -----------------------------------------------------------------
    best_b = min(("P1_persistence", "P7_trailing_mean"), key=lambda k: np.abs(y - P[k]).mean())
    ns2 = int(cfg["cv"]["n_splits"]); prow = []
    for name in ("R2_random_forest_ratio", "R3_gradient_boosting_ratio"):
        pp = _placebo_predict(fac[name], X, ratio, g, ns2, ctx.rng.generator("M7", "placebo", name)) * roll
        b = cluster_bootstrap_skill(g, np.abs(y - pp), np.abs(y - P[best_b]), rng, B)
        prow.append(dict(model=name + "_target_shuffled_within_person", scheme=f"GroupKFold{ns2}", baseline=best_b, skill_mae=b["skill"], ci_lo=b["ci_lo"], ci_hi=b["ci_hi"],
                         placebo_passed=bool(b["ci_lo"] <= 0 and b["skill"] <= 0.02)))
    ctx.save_table(pd.DataFrame(prow), "placebo_control", [base("m7_placebo", "within-person shuffled-target control")])
    if not all(r["placebo_passed"] for r in prow):
        ctx.log.warn("FAILED_CONTROL: shuffled-target placebo showed apparent skill; do not interpret the verdict")
    win = verdict[verdict["primary"] & verdict["ml_beats_best_simple_baseline"]]["model"].tolist()
    ctx.log.info(f"M7 verdict (primary={primary}): ML models beating the best simple baseline by the fixed rule: {win or 'none'}")
