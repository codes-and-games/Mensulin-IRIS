"""M7 feature table: past-only construction, zero-TDD handling, calendar gaps, clustered bootstrap, and a smoke run."""
import numpy as np
import pandas as pd

from iris.evaluate.cluster_bootstrap import cluster_bootstrap_skill
from iris.features.next_day import CANDIDATE_FEATURES, build_next_day_table
from iris.tools.synthetic import synthetic_person_day

NUM = ["tdd_u", "basal_u", "bolus_u", "carb_g", "carb_entries", "cgm_coverage", "mean_glucose_mgdl", "tir_pct", "tbr_pct", "tar_pct"]


def _pd(n_persons=3, n_days=30, seed=1):
    return synthetic_person_day(np.random.default_rng(seed), n_persons=n_persons, n_days=n_days, with_cycle_labels=False)


def test_features_depend_only_on_earlier_days():
    df = _pd()
    base, _ = build_next_day_table(df)
    t0 = base.iloc[10]
    mask = (df["person_id"] == t0["person_id"]) & (pd.to_datetime(df["date_local"]) >= pd.Timestamp(t0["date_local"]))
    pert = df.copy()
    pert[NUM] = pert[NUM].astype(float)
    rng = np.random.default_rng(0)
    for c in NUM:
        pert.loc[mask, c] = rng.uniform(1, 500, mask.sum())
    new, _ = build_next_day_table(pert)
    a = base[(base.person_id == t0["person_id"]) & (base.date_local == t0["date_local"])][list(CANDIDATE_FEATURES) + ["lag1_tdd_u", "lag2_tdd_u", "roll7_mean_tdd_u"]].iloc[0]
    b = new[(new.person_id == t0["person_id"]) & (new.date_local == t0["date_local"])][list(CANDIDATE_FEATURES) + ["lag1_tdd_u", "lag2_tdd_u", "roll7_mean_tdd_u"]].iloc[0]
    pd.testing.assert_series_equal(a.astype(float), b.astype(float))
    assert base.iloc[10]["y_tdd_u"] != new[(new.person_id == t0["person_id"]) & (new.date_local == t0["date_local"])]["y_tdd_u"].iloc[0]   # the target itself did change


def test_persistence_column_is_previous_day_and_trailing_mean_is_past_only():
    df = _pd(1, 20)
    tab, _ = build_next_day_table(df)
    s = df.set_index("date_local")["tdd_u"]
    r = tab.iloc[5]
    prev = (pd.Timestamp(r["date_local"]) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    assert np.isclose(r["lag1_tdd_u"], s[prev])
    past7 = s[[(pd.Timestamp(r["date_local"]) - pd.Timedelta(days=k)).strftime("%Y-%m-%d") for k in range(1, 8) if (pd.Timestamp(r["date_local"]) - pd.Timedelta(days=k)).strftime("%Y-%m-%d") in s.index]]
    assert np.isclose(r["roll7_mean_tdd_u"], past7.mean())


def test_zero_tdd_is_not_recorded_not_physiology_and_gaps_are_not_bridged():
    df = _pd(1, 30)
    df.loc[df.index[12], "tdd_u"] = 0.0                      # insulin not captured that day
    df = df.drop(df.index[20]).reset_index(drop=True)         # a missing calendar day
    tab, counts = build_next_day_table(df)
    assert counts["included_tdd_zero_or_negative_treated_as_not_recorded"] == 1
    dates = set(tab["date_local"])
    assert df.loc[12, "date_local"] not in dates                                           # zero day is never a target
    day_after_zero = (pd.Timestamp(df.loc[12, "date_local"]) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    assert day_after_zero not in dates                                                     # ...nor the day after it (no valid lag1)
    assert (tab["lag1_tdd_u"] > 0).all() and (tab["y_tdd_u"] > 0).all()
    day_after_gap = (pd.Timestamp(df.loc[19, "date_local"]) + pd.Timedelta(days=2)).strftime("%Y-%m-%d")
    assert day_after_gap not in dates                                                      # day after a missing day has no lag1


def test_excluded_days_never_feed_history():
    df = _pd(1, 20)
    df.loc[5, "exclude_flag"] = True
    tab, _ = build_next_day_table(df)
    nxt = (pd.Timestamp(df.loc[5, "date_local"]) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    assert df.loc[5, "date_local"] not in set(tab["date_local"]) and nxt not in set(tab["date_local"])


def test_cluster_bootstrap_detects_gain_and_null():
    rng = np.random.default_rng(3)
    g = np.repeat(np.arange(30), 20)
    base = rng.uniform(1, 3, len(g))
    better = cluster_bootstrap_skill(g, base * 0.8, base, rng, 500)
    same = cluster_bootstrap_skill(g, base, base, rng, 500)
    assert better["ci_lo"] > 0.15 and abs(same["skill"]) < 1e-12 and same["ci_lo"] <= 0 <= same["ci_hi"]


def test_m7_smoke_run_in_test_mode(tmp_path):
    from iris.tools.run_experiment import run_experiment
    ctx = run_experiment("M7_next_day_tdd_ml", mode="test", smoke=True, runs_root=tmp_path)
    t = pd.read_parquet(ctx.dir / "tables" / "verdict.parquet")
    assert set(t["scheme"]) == {"GroupKFold", "LeaveOneGroupOut"} and t["primary"].any()
    pc = pd.read_parquet(ctx.dir / "tables" / "placebo_control.parquet")
    assert len(pc) == 2
