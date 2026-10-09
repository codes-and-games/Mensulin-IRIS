import numpy as np
import pandas as pd
import pytest

from iris.common.exceptions import IrisError, LeakageError, ScientificBlocker
from iris.estimator.ekf import NoiseSpec, run_ekf
from iris.estimator.glucose_insulin_model import IDX, N_STATE, ModelConstants, jacobian, transition
from iris.estimator.simulator import SimDesign, simulate
from iris.estimator.smoother import daily_sensitivity, rts_smooth
from iris.estimator.targets import t7_rule_of_thumb
from iris.evaluate.cv import grouped_cv_scores, grouped_splits
from iris.evaluate.calibration_metrics import amplitude_phase
from iris.features import cycle as cy
from iris.features import leakage_guard as lg
from iris.features.person_day import apply_inclusion, finalize_person_day
from iris.ingest.audit import audit_dataframe
from iris.ingest.harmonise import flag_glucose, glucose_to_mgdl
from iris.ingest.loaders.generic import load_with_mapping
from iris.tools.synthetic import synthetic_person_day

K = ModelConstants(55.0, 40.0, 0.9, 50.0, 3.0, 5.0)     # TEST-grade constants


def test_jacobian_matches_finite_difference():
    x = np.array([0.5, 0.4, 3.0, 2.0, 130.0, 0.05, 0.2])
    J = jacobian(x, K)
    num = np.empty_like(J)
    for j in range(N_STATE):
        d = np.zeros(N_STATE); d[j] = 1e-6
        num[:, j] = (transition(x + d, 0.01, 0.5, K) - transition(x - d, 0.01, 0.5, K)) / 2e-6
    assert np.allclose(J, num, atol=1e-5)


def test_model_constants_validation():
    with pytest.raises(ValueError):
        ModelConstants(55.0, 40.0, 0.9, 50.0, 3.0, 30.0)       # Euler step too coarse


def test_ekf_missing_data_no_update_and_ll_finite():
    rng = np.random.default_rng(0)
    d = SimDesign(days=6, amplitude=0.0, cycle_len_d=28, phase_rad=0.0, cgm_sd=8.0, carb_error_sd=0.1, gap_fraction=0.3, g_target=120.0, e_offset=0.2, process_sd_g=0.3)
    sim = simulate(d, K, rng)
    x0 = np.zeros(N_STATE); x0[IDX["G"]] = 120.0
    res = run_ekf(sim["cgm"], sim["u"], sim["carb_logged"], K, NoiseSpec(1e-6, 1e-8, 0.3, 1e-6, 64.0), x0, np.diag([1, 1, 1, 1, 100, .05, .01]))
    miss = np.isnan(sim["cgm"])
    assert miss.any() and np.isfinite(res.loglik)
    assert np.allclose(res.x_filt[miss], res.x_pred[miss])                    # no spurious update on missing samples
    xs, Ps = rts_smooth(res)
    assert np.all(np.linalg.eigvalsh(Ps[-1]) > -1e-8)


def test_target_t7_is_rejected():
    with pytest.raises(IrisError):
        t7_rule_of_thumb()


def test_cycle_representations():
    assert cy.normalised_position(1, 28) == 0.0
    seg, pos = cy.two_anchor_position(np.array([1, 14, 15, 28]), 28, 15)
    assert list(seg) == ["follicular", "follicular", "luteal", "luteal"] and pos.min() >= 0 and pos.max() <= 1
    h = cy.harmonic_features(np.array([0.0, 1.0]), 2)
    assert np.allclose(h[0], h[1])                                            # continuous across the cycle boundary
    with pytest.raises(IrisError):
        cy.normalised_position(30, 28)
    with pytest.raises(ScientificBlocker):
        cy.phase_from_windows(5, 28, 14, None)                                # windows [TO EXTRACT] => blocked


def test_leakage_guard_rejects_future_same_day_and_glucose_for_tdd():
    with pytest.raises(LeakageError):
        lg.check_feature_availability(["a"], {"a": "future"})
    with pytest.raises(LeakageError):
        lg.check_feature_availability(["a"], {"a": "same_day"})
    with pytest.raises(LeakageError):
        lg.check_feature_availability(["mean_glucose_mgdl"], {"mean_glucose_mgdl": "past"}, target_is_tdd=True)
    lg.check_feature_availability(["a"], {"a": "past"})


def test_lag_features_are_strictly_past():
    df = pd.DataFrame({"p": ["a"] * 4, "t": range(4), "x": [10, 20, 30, 40]})
    out = lg.lag_features(df, ["x"], "p", "t", 1)
    assert out["x_lag1"].isna().iloc[0] and list(out["x_lag1"].iloc[1:]) == [10, 20, 30]


def test_grouped_splits_disjoint_and_require_two_subjects():
    g = np.repeat(np.arange(8), 10)
    for tr, te in grouped_splits(g, 4):
        assert not (set(g[tr]) & set(g[te]))
    with pytest.raises(LeakageError):
        list(grouped_splits(np.zeros(10), 3))
    with pytest.raises(LeakageError):
        lg.assert_group_disjoint([1, 2], [2, 3])


def test_person_day_finalize_leaves_cycle_null_and_inclusion_flags_not_deletes():
    df = synthetic_person_day(np.random.default_rng(0), n_persons=3, n_days=10, with_cycle_labels=False).drop(columns=["isf_clinician"])
    out = finalize_person_day(df)
    assert out["cycle_day"].isna().all() and len(out) == len(df)
    df2 = out.copy(); df2.loc[:3, "cgm_coverage"] = 0.1
    flagged = apply_inclusion(df2, 0.7, 3)
    assert len(flagged) == len(df2) and flagged["exclude_flag"].sum() >= 4 and flagged.loc[0, "exclude_reason"].startswith("cgm_coverage")


def test_harmonise_units_and_flags_not_deletes():
    g = glucose_to_mgdl(pd.Series([5.0, 10.0]), "mmol/L")
    assert g.iloc[0] == pytest.approx(90.08, abs=0.1)
    f = flag_glucose(pd.Series([10.0, 100.0, 700.0]))
    assert list(f) == ["range_flag", "ok", "range_flag"]
    with pytest.raises(IrisError):
        glucose_to_mgdl(pd.Series([1.0]), "furlongs")


def test_audit_reports_columns_missingness_without_assuming(tmp_path):
    df = pd.DataFrame({"id": ["a", "a", "b", "b"], "t": ["2026-01-01", "2026-01-02", "2026-01-01", "2026-01-02"], "g": [100.0, np.nan, 120.0, 130.0]})
    a = audit_dataframe(df, "x.csv")
    assert a["columns"]["g"]["n_missing"] == 1 and a["columns"]["t"]["timestamp_like"] and a["columns"]["id"]["id_candidate"]


def test_loader_blocks_without_audited_mapping(tmp_path):
    f = tmp_path / "d.csv"; pd.DataFrame({"a": [1]}).to_csv(f, index=False)
    with pytest.raises(ScientificBlocker):
        load_with_mapping(f, tmp_path / "nope.yaml")
    m = tmp_path / "m.yaml"; m.write_text("audit_status: AUDITED\naudit_file: x.json\ncolumns: {glucose: not_a_column}\n")
    with pytest.raises(ScientificBlocker):
        load_with_mapping(f, m)


def test_amplitude_phase_recovery():
    d = np.arange(112)
    amp, ph, p = amplitude_phase(1 + 0.1 * np.cos(2 * np.pi * d / 28 - 0.5) + np.random.default_rng(1).normal(0, 0.01, d.size), 28)
    assert amp == pytest.approx(0.1, abs=0.01) and ph == pytest.approx(0.5, abs=0.1) and p < 1e-6
