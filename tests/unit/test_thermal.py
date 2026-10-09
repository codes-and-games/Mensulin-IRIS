import numpy as np
import pytest

from iris.common.exceptions import NumericalError, ScientificBlocker
from iris.common.units import celsius_to_kelvin
from iris.thermal import lag
from iris.thermal.exposure import exposure_summary, generate_parametric
from iris.thermal.kinetics.k0 import K0
from iris.thermal.kinetics.k1 import K1, arrhenius_ratio, arrhenius_rate, mean_kinetic_temperature_c
from iris.thermal.kinetics.k3 import K3
from iris.thermal.kinetics.k4 import K4
from iris.thermal.kinetics.k5 import K5
from iris.thermal.qc import fill_gaps
from iris.thermal.reconstruct import PartonLoganParams, parton_logan, sinusoid, naive_constant


def test_kelvin_guard():
    assert celsius_to_kelvin(25.0) == pytest.approx(298.15)
    with pytest.raises(NumericalError):
        arrhenius_rate(25.0, 1.0, 80e3, 298.15)             # Celsius passed as Kelvin
    with pytest.raises(NumericalError):
        celsius_to_kelvin(np.array([np.nan]))


def test_arrhenius_reference_ratio_exactly_one():
    assert arrhenius_ratio(25.0, 83100.0, 25.0) == 1.0
    assert arrhenius_ratio(np.array([37.0]), 83100.0, 25.0)[0] > 1.0


def test_arrhenius_invalid_parameters():
    with pytest.raises(NumericalError):
        arrhenius_rate(310.0, 1.0, -1.0, 298.15)
    with pytest.raises(NumericalError):
        arrhenius_rate(310.0, -1.0, 80e3, 298.15)
    with pytest.raises(NumericalError):
        arrhenius_rate(310.0, 1.0, 1e9, 298.15)             # overflow refused, not clipped


def test_k1_hazard_and_closed_form():
    m = K1(0.01, 80e3, 25.0)
    t = np.full(100, 25.0)
    assert m.potency(t, 0.1)[0] == pytest.approx(np.exp(-0.01 * 10.0))


def test_k0_point_mass_and_k3_k4_closed_form():
    assert (K0().potency(np.full((3, 10), 40.0), 1.0) == 1.0).all()
    k1 = arrhenius_rate(310.15, 0.02, 80e3, 298.15); k2 = arrhenius_rate(310.15, 0.5, 60e3, 298.15)
    t_days = 20.0
    exact = (k1 + k2) / (k1 * np.exp((k1 + k2) * t_days) + k2)
    assert K3(0.02, 0.5, 80e3, 60e3, 25.0).potency(np.full(2000, 37.0), 0.01)[0] == pytest.approx(exact, rel=1e-9)
    ka, kb = arrhenius_rate(310.15, 0.01, 70e3, 298.15), arrhenius_rate(310.15, 0.005, 50e3, 298.15)
    assert K4(0.01, 70e3, 0.005, 50e3, 25.0).potency(np.full(2000, 37.0), 0.01)[0] == pytest.approx(np.exp(-(ka + kb) * 20.0))


def test_k5_no_extrapolation_and_no_invented_composition_rule():
    k5 = K5([5, 5, 25, 25, 40, 40], [10, 30, 10, 30, 10, 30], [1, .99, .98, .95, .9, .8])
    assert 0.9 < k5.potency(np.full(100, 25.0), 0.2)[0] <= 1
    with pytest.raises(ScientificBlocker):
        k5.potency(np.r_[np.full(50, 25.0), np.full(50, 40.0)], 0.2)
    with pytest.raises(NumericalError):
        k5.potency(np.full(100, 25.0), 5.0)


def test_mkt_worked_example():
    h = np.r_[np.full(12, 20.0), np.full(12, 40.0)]
    assert mean_kinetic_temperature_c(h, 83100.0) == pytest.approx(34.4, abs=0.1)


def test_lag_step_response_matches_integrator():
    tau, dt = 900.0, 10.0
    t = np.arange(0, 3600, dt)
    air = np.full(t.size, 40.0)
    num = lag.exponential_integrator(air, dt, tau, tv0=5.0, output='edge')
    assert np.allclose(num, lag.analytic_step_response(t, 40.0, 5.0, tau), atol=1e-9)


def test_lag_limits():
    air = np.sin(np.linspace(0, 6, 200)) * 10 + 25
    assert np.array_equal(lag.exponential_integrator(air, 60.0, 0.0), air)                # tau -> 0
    assert np.allclose(lag.exponential_integrator(np.full(50, 30.0), 60.0, 600.0), 30.0)   # constant ambient
    assert np.allclose(lag.exponential_integrator(air, 60.0, 1e-6), air, atol=1e-6)         # tau -> 0 (no spurious lag)
    big = lag.exponential_integrator(air, 60.0, 1e9)
    assert np.ptp(big) < 1e-3                                                              # huge inertia: ~constant
    two = lag.exponential_integrator(np.vstack([air, air]), 60.0, np.array([0.0, 600.0]))
    assert np.array_equal(two[0], air) and not np.allclose(two[1], air)


def test_lag_timestep_refinement_is_exact_for_piecewise_constant_input():
    tau = 600.0
    base = np.r_[np.full(30, 25.0), np.full(30, 40.0)]               # step at t = 30 min (dt = 60 s)
    fine = np.repeat(base, 4)                                         # same input at dt = 15 s
    v1 = lag.exponential_integrator(base, 60.0, tau, tv0=25.0)
    v2 = lag.exponential_integrator(fine, 15.0, tau, tv0=25.0).reshape(-1, 4).mean(axis=1)   # mean of 4 fine means = coarse mean
    assert np.allclose(v1, v2, atol=1e-9)
    e1 = lag.exponential_integrator(base, 60.0, tau, tv0=25.0, output="edge")
    e2 = lag.exponential_integrator(fine, 15.0, tau, tv0=25.0, output="edge")[::4]
    assert np.allclose(e1, e2, atol=1e-9)


def test_finite_volume_agrees_with_lumped_for_small_biot():
    rho, cp, k, h, R = 1000.0, 4180.0, 0.6, 8.0, 0.012
    bi = lag.biot_number(h, np.pi * R ** 2, 2 * np.pi * R, k)
    assert lag.lumped_valid(bi)
    tau = lag.cylinder_tau_s(R, rho, cp, h)
    dt, n = 30.0, 240
    air = np.full(n, 35.0)
    fv = lag.finite_volume_cylinder(air, dt, radius_m=R, rho_kg_m3=rho, cp_j_kgk=cp, k_w_mk=k, h_w_m2k=h, tv0=5.0)
    lumped = lag.exponential_integrator(air, dt, tau, tv0=5.0, output='edge')
    assert np.max(np.abs(fv - lumped)) < 0.5       # K, small Bi


def test_exposure_summary_and_gaps():
    s = exposure_summary(np.r_[np.full(10, 20.0), np.full(10, 41.0)], 1.0, mkt_ea_j_mol=83100.0)
    assert s["hours_gt_40C"] == 10.0 and s["degree_hours_gt_25C"] == pytest.approx(160.0) and s["max_c"] == 41.0
    t = np.array([20.0, np.nan, np.nan, 22.0, np.nan, np.nan, np.nan, np.nan, np.nan, 30.0])
    filled, imp, flags = fill_gaps(t, np.isnan(t), step_h=1.0, gmax_h=3.0, long_gap="pessimistic")
    assert flags[1] == "gap_interpolated" and flags[5] == "gap_missing" and imp.mean() == pytest.approx(0.7)
    assert filled[5] == 30.0
    _, _, f2 = fill_gaps(t, np.isnan(t), 1.0, 3.0, long_gap="missing")
    assert f2[5] == "gap_missing"


def test_reconstruction_basics_and_parton_logan_fails_closed():
    d = sinusoid(np.array([30.0]), np.array([20.0]), 15.0)
    assert d.max() <= 30.0 + 1e-9 and d.min() >= 20.0 - 1e-9 and d.size == 24
    assert np.allclose(naive_constant(np.array([30.0]), np.array([20.0])), 25.0)
    with pytest.raises(ScientificBlocker):
        parton_logan([30.0], [20.0], [20.0], 6.0, 18.0, PartonLoganParams(1.0, 1.0, 0.0))


def test_parametric_scenarios_and_blockers(rng_tree):
    cfg = {"id": "S6", "kind": "heat_spikes", "params": {"base_c": 25.0, "episode_min_h": 1.0, "episode_max_h": 3.0,
                                                          "peak_min_c": 40.0, "peak_max_c": 45.0, "episodes_per_week": 7.0}}
    series, _ = generate_parametric(cfg, 14, 5.0, rng_tree.generator("h"))
    assert series.max() >= 40.0 and series.min() == 25.0
    with pytest.raises(ScientificBlocker):
        generate_parametric({"id": "S5", "kind": "reanalysis_driven", "blocked_on": "climate"}, 7, 5.0, rng_tree.generator("h"))
