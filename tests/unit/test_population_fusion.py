import numpy as np
import pandas as pd
import pytest

from iris.common.exceptions import CircularityError, ScientificBlocker, IrisError
from iris.common.parameters import RunMode
from iris.common.rng import RngTree
from iris.fusion import analytic as an
from iris.fusion import bounds, controls, metrics as mt
from iris.fusion.admissible_set import AdmissibleSet, Theta, assert_single_set, classify_conclusion, COMPONENTS
from iris.fusion.adversary import adversarial_search
from iris.fusion.mc_engine import FusionConfig, run_fusion, summarise_epistemic
from iris.population.checks import dependence_diagnostics, run_checks
from iris.population.generator import build_spec_from_config, generate, lognormal_params, phase_matrix
from iris.population.requirement import build_requirement
from iris.population.dependence import BiologicalDependence, standardized_margin
from conftest import REPO, TEST_COMPLETION


# ------------------------------------------------ population
def test_lognormal_anchor_matches_document():
    mu, sg = lognormal_params(37.3, 12.2)
    assert mu == pytest.approx(3.568, abs=1e-3) and sg == pytest.approx(0.319, abs=1e-3)


def test_population_moments_and_centering(test_population):
    S, R = phase_matrix(test_population, "S_p"), phase_matrix(test_population, "rho_p")
    assert np.allclose(S.mean(axis=1), 1.0) and np.allclose(R.mean(axis=1), 1.0)
    assert test_population.cycle_len.between(21, 40).all()
    assert abs(test_population.tdd_u.mean() - 37.3) < 1.0
    assert (S[:, 0].mean() > 1.0) and (S[:, 4].mean() < 1.0)           # published direction: EF high, ML low


def test_rho_is_not_one_over_s_and_circular_case_refused(test_population):
    S, R = phase_matrix(test_population, "S_p"), phase_matrix(test_population, "rho_p")
    inv = 1.0 / S; inv = inv / inv.mean(axis=1, keepdims=True)
    assert not np.allclose(R, inv, rtol=1e-3)
    gamma1 = np.ones_like(S)
    with pytest.raises(CircularityError):
        build_requirement(S, gamma1, 1.0, 0.0, np.random.default_rng(0))
    ok = build_requirement(S, gamma1, 1.0, 0.0, np.random.default_rng(0), allow_circular_control=True)   # ablation A4 only
    assert np.allclose(ok, inv, rtol=1e-9)


def test_unresolved_parameters_block_not_default(pop_cfg):
    with pytest.raises(ScientificBlocker):
        build_spec_from_config(pop_cfg, RunMode.PROVISIONAL, eta=0.5, h_multiplier=1.0, completion={})
    with pytest.raises(ScientificBlocker):                           # anovulatory prevalence unresolved
        spec = build_spec_from_config(pop_cfg, RunMode.PROVISIONAL, eta=0.5, h_multiplier=1.0,
                                      completion={k: v for k, v in TEST_COMPLETION.items() if k != "anovulatory_prevalence"}, n=100)
        generate(spec, RngTree(1))
    with pytest.raises(ScientificBlocker):                           # production refuses PENDING_VERIFY anchors
        build_spec_from_config(pop_cfg, RunMode.PRODUCTION, eta=0.5, h_multiplier=1.0, completion=TEST_COMPLETION)


def test_stress_components_recorded(pop_cfg):
    spec = build_spec_from_config(pop_cfg, RunMode.PROVISIONAL, eta=0.5, h_multiplier=1.0, completion=TEST_COMPLETION,
                                  family="student_t_5")
    assert any("family=student_t_5" in s for s in spec.stress_components)
    assert any("profile_completion" in s for s in spec.stress_components)


def test_standardized_margins_unit_variance():
    u = np.random.default_rng(0).standard_normal(400000)
    for fam, opts in [("normal", {}), ("student_t_5", {}), ("skewnormal_3", {}), ("mixture_0.05", {"mixture_shift_sd": 3.0})]:
        z = standardized_margin(fam, opts)(u)
        assert abs(z.mean()) < 0.03 and abs(z.std() - 1.0) < 0.05, fam
    with pytest.raises(ScientificBlocker):
        standardized_margin("mixture_0.05", {})(u)


def test_dependence_matrix_validation_and_effect(pop_cfg):
    with pytest.raises(Exception):
        BiologicalDependence(np.array([[1, 2, 0], [2, 1, 0], [0, 0, 1.0]]))
    dep = BiologicalDependence.from_pairs({("tdd", "sens"): 0.6}, "STRESS_TEST", "tdd_sigma_pos")
    spec = build_spec_from_config(pop_cfg, RunMode.PROVISIONAL, eta=0.5, h_multiplier=1.0, completion=TEST_COMPLETION, dependence=dep, n=6000)
    d = dependence_diagnostics(generate(spec, RngTree(5)))
    assert d["corr_tdd_S_contrast"] > 0.2


def test_s3_checks_block_when_target_unresolved(test_population):
    res = run_checks(test_population, {"tdd_mean": 37.3, "tdd_sd": 12.2, "cycle_mean": 28.4, "cycle_sd": 3.1, "sens_ef": None})
    assert res.set_index("check").loc["sens_early_follicular_mean", "status"] == "BLOCKED"
    assert res.set_index("check").loc["cycle_mean_of_S_equals_1", "status"] == "PASS"


# ------------------------------------------------ analytic
def test_zero_loss_exact():
    d = an.shortfall_case_a(np.array([3.0, 40.0]), np.array([1.0, 1.0]))
    assert (d == 0.0).all() and (an.loss(1.0) == 0.0)
    with pytest.raises(IrisError):
        an.loss(1.0000001)


def test_atom_aware_mixture_matches_direct_moments_without_epsilon():
    rng = np.random.default_rng(3)
    n = 100000
    ell = np.where(rng.uniform(size=n) < 0.35, 0.0, rng.uniform(0.01, 0.3, n))
    r = rng.lognormal(3.5, 0.3, n)
    du = r * ell
    m = an.mixture_summary(du, ell)
    assert m["pi0"] == pytest.approx(0.35, abs=0.01)
    assert m["mean"] == pytest.approx(m["direct_mean"], rel=1e-10) and m["var"] == pytest.approx(m["direct_var"], rel=1e-9)
    with pytest.raises(IrisError):                                     # logs of exact zero refused, not epsilon-patched
        an.log_variance_decomposition(np.log(r), np.zeros(n), np.log(ell))


def test_log_variance_decomposition_identity():
    rng = np.random.default_rng(4)
    a = rng.normal(0, 0.3, 50000); b = 0.5 * a + rng.normal(0, 0.1, 50000); c = rng.normal(-2, 0.8, 50000)
    d = an.log_variance_decomposition(a, b, c)
    assert sum(d["shares"].values()) == pytest.approx(1.0, abs=1e-9)
    assert d["cov2"]["tdd_rho"] != 0.0
    assert an.log_variance_decomposition(a, b, c, assume_independent=True)["independence_imposed"]


def test_case_b_signed_and_scaling():
    assert an.shortfall_case_b(np.array([5.0]), np.array([4.0]), 1.0)[0] == pytest.approx(1.0)
    r = np.array([2.0, 4.0]); p = 0.9
    assert np.allclose(an.shortfall_case_a(2 * r, p), 2 * an.shortfall_case_a(r, p))


def test_glucose_cancelling_model_ignores_biology():
    ell = np.array([0.1, 0.2])
    assert np.allclose(an.glucose_equivalent_cancelling(1700, ell), 1700 * ell)


def test_bounds_bracket_empirical_tail():
    rng = np.random.default_rng(5)
    r = rng.lognormal(3.5, 0.3, 20000); ell = rng.uniform(0, 0.2, 20000)
    lo, hi = bounds.product_tail_bounds(r, ell, 2.0)
    p = np.mean(r * ell > 2.0)
    assert lo <= p <= hi
    assert bounds.cantelli_upper(2.0) == pytest.approx(0.2)
    with pytest.raises(IrisError):
        bounds.vysochanskij_petunin_upper(1.0)


def test_controls():
    rng = np.random.default_rng(6)
    m = rng.random((50, 6))
    perm = controls.control_c3_permute_phases(m, rng)
    assert np.allclose(np.sort(perm, axis=1), np.sort(m, axis=1)) and not np.array_equal(perm, m)
    assert controls.control_c1_no_loss(np.array([0.3, 0.2])).min() == 1.0
    ell = np.full(100, 0.1); rank = np.linspace(0, 1, 100)
    inj = controls.control_p1_inject_dependence(ell, rank, 1.0)
    assert inj[rank > 0.8].min() == pytest.approx(0.2) and inj[rank <= 0.8].max() == 0.1


# ------------------------------------------------ MC engine
def _cfg(**kw):
    base = dict(run_id="T", scenario_id="TEST@7d", J=8, dosing_cases=("A",), isf_model="K_over_tdd_times_S", isf_const=(1700.0,),
                thr_units=(0.5, 1.0), thr_pct_tdd=(5.0,), thr_glucose=(30.0,), mode="shared", r_pb=0.0)
    base.update(kw); return FusionConfig(**base)


def test_engine_zero_loss_control_gives_zero_everywhere(test_population, test_potency):
    pot = test_potency.assign(potency=1.0)
    out = run_fusion(test_population, pot, _cfg(), RngTree(1), phases=("high_pop",))
    assert (out[out.metric.str.startswith("exceed")]["value"] == 0.0).all()
    assert (out[out.metric == "mean_positive_part_u"]["value"] == 0.0).all()


def test_engine_is_reproducible_and_reports_mc_se(test_population, test_potency):
    a = run_fusion(test_population, test_potency, _cfg(), RngTree(9), phases=("high_pop",))
    b = run_fusion(test_population, test_potency, _cfg(), RngTree(9), phases=("high_pop",))
    pd.testing.assert_frame_equal(a, b)
    assert a["mc_se"].dropna().ge(0).all() and a[a.metric == "exceed_units"]["mc_se"].notna().all()
    s = summarise_epistemic(a)
    assert (s["evidence_class"] == "PROJECTED").all()


def test_instrument_controls_n1_shared_excess_is_zero_and_p1_detects_injection(test_population, test_potency):
    out = run_fusion(test_population, test_potency, _cfg(thr_units=(2.0,), mode="shared"), RngTree(2), phases=("high_pop",))
    ex = out[out.metric == "tci_excess"]["value"].dropna()
    assert ex.abs().max() < 1e-9                                       # N1: dependence absent => no excess
    # P1: injected dependence is detected as positive excess concentration
    arr_rank = test_population["swing_rank"].to_numpy(); swing = test_population["swing_unit"].to_numpy()
    r_high = test_population["R_p5_u"].to_numpy()
    ell = np.full(len(r_high), 0.15)
    inj = controls.control_p1_inject_dependence(ell, arr_rank, 1.0)
    tau = 4.0
    e = r_high * inj > tau
    base = mt.algebraic_baseline(lambda l: r_high * l, inj, swing, arr_rank, tau, np.random.default_rng(0), n_perm=15)
    assert mt.tci(e, arr_rank) - base["tci_alg"] > 0.1


def test_coupled_mode_with_r0_is_independent_and_with_positive_r_concentrates(test_population, test_potency):
    pot = test_potency.assign(potency=np.linspace(0.5, 0.99, 12))
    cfg0 = _cfg(thr_units=(3.0,), mode="coupled", r_pb=0.0, J=6)
    cfg1 = _cfg(thr_units=(3.0,), mode="coupled", r_pb=0.9, J=6)
    e0 = run_fusion(test_population, pot, cfg0, RngTree(3), phases=("high_pop",)).query("metric=='tci_excess'")["value"].dropna()
    e1 = run_fusion(test_population, pot, cfg1, RngTree(3), phases=("high_pop",)).query("metric=='tci_excess'")["value"].dropna()
    assert abs(e0.mean()) < 0.35 and e1.mean() > e0.mean()


def test_heterogeneity_penalty_uses_direct_tails_and_flags_zero_denominator():
    a = np.array([0.0, 0.0, 5.0, 5.0]); b = np.array([1.0, 1.0, 1.0, 1.0])
    hp = mt.heterogeneity_penalty(a, b, 2.0)
    assert hp["denominator_zero"] and np.isinf(hp["hp"])
    hp2 = mt.heterogeneity_penalty(a, b * 3, 2.0)
    assert hp2["hp"] == pytest.approx(0.5)


def test_shortfall_scales_linearly_with_R_in_engine(test_population, test_potency):
    big = test_population.copy()
    for k in range(1, 7):
        big[f"R_p{k}_u"] *= 2.0
    a = run_fusion(test_population, test_potency, _cfg(thr_units=(1.0, 2.0)), RngTree(4), phases=("high_pop",))
    b = run_fusion(big, test_potency, _cfg(thr_units=(1.0, 2.0)), RngTree(4), phases=("high_pop",))
    ea = a.query("metric=='exceed_units' and threshold==1.0 and epistemic_draw_j==3")["value"].iloc[0]
    eb = b.query("metric=='exceed_units' and threshold==2.0 and epistemic_draw_j==3")["value"].iloc[0]
    assert ea == pytest.approx(eb)


# ------------------------------------------------ admissible set / adversary
def test_theta_E_and_S_are_separate_and_never_pooled():
    a = AdmissibleSet.from_yaml(REPO / "configs/fusion/admissible_set.yaml")
    pe, _ = a.factorial("E", None, np.random.default_rng(0))
    ps, cov = a.factorial("S", 40, np.random.default_rng(0))
    assert a.size("E") < a.size("S") and cov["subsampled"]
    assert assert_single_set(pe) == "E" and assert_single_set(ps) == "S"
    with pytest.raises(IrisError):
        assert_single_set(pe[:2] + ps[:2])
    assert set(a.conditioned_on_E()) >= {"f", "eta", "r_PB", "R_B"}
    assert all(a.is_in_E(t) for t in pe)


def test_adversary_finds_planted_counterexample_and_is_reproducible():
    a = AdmissibleSet.from_yaml(REPO / "configs/fusion/admissible_set.yaml")
    margin = lambda th: 0.5 - 1.0 * max(th.as_dict()["r_PB"], 0.0)       # fails for r_PB > 0.5 (in Theta_S only)
    r1 = adversarial_search(margin, a, "S", RngTree(1), budget=400)
    r2 = adversarial_search(margin, a, "S", RngTree(1), budget=400)
    assert r1["counterexample_found"] and r1 == r2 and r1["evaluations"] <= 400
    assert not adversarial_search(margin, a, "E", RngTree(1), budget=400)["counterexample_found"]


def test_classification_robust_conditional_unsupported():
    a = AdmissibleSet.from_yaml(REPO / "configs/fusion/admissible_set.yaml")
    pts, _ = a.factorial("S", 60, np.random.default_rng(0))
    rows = [dict(zip(COMPONENTS, p.values)) for p in pts]
    df = pd.DataFrame(rows)
    df["blocked"] = False
    df["margin"] = 1.0
    assert classify_conclusion("c", "S", df, {"counterexample_found": False}, []).classification == "computationally_robust"
    assert classify_conclusion("c", "S", df, {"counterexample_found": True}, []).classification == "conditional"
    df2 = df.copy(); df2["margin"] = np.where(df2["d"] == "A", 1.0, -1.0)
    res = classify_conclusion("c", "S", df2, {"counterexample_found": False}, [])
    assert res.classification == "conditional" and res.controlling_component == "d"
    df3 = df.copy(); df3["blocked"] = True; df3["blocked_reason"] = "missing evidence"
    assert classify_conclusion("c", "E", df3, None, ["f"]).classification == "unsupported"
