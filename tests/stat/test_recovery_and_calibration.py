import numpy as np
import pytest

from iris.common.rng import RngTree
from iris.estimator.ekf import NoiseSpec, run_ekf
from iris.estimator.glucose_insulin_model import IDX, N_STATE, ModelConstants
from iris.estimator.simulator import SimDesign, simulate
from iris.estimator.smoother import daily_sensitivity, rts_smooth
from iris.evaluate.calibration_metrics import amplitude_phase
from iris.thermal.kinetics.fitting import fit_k1, loso_k1
from iris.thermal.kinetics.k1 import arrhenius_rate
import pandas as pd

K = ModelConstants(55.0, 40.0, 0.9, 50.0, 3.0, 10.0)      # TEST-grade


def _trial(A, seed, days=70):
    rng = np.random.default_rng(seed)
    d = SimDesign(days=days, amplitude=A, cycle_len_d=28, phase_rad=0.7, cgm_sd=10.0, carb_error_sd=0.1, gap_fraction=0.1, g_target=120.0, e_offset=0.2, process_sd_g=0.5)
    sim = simulate(d, K, rng)
    x0 = np.zeros(N_STATE); x0[IDX["I1"]] = x0[IDX["I2"]] = sim["u_basal_u_per_min"] * K.tau_i_min; x0[IDX["G"]] = 120.0; x0[IDX["E"]] = 0.2
    res = run_ekf(sim["cgm"], sim["u"], sim["carb_logged"], K, NoiseSpec(1e-6, 1e-8, 0.3, 1e-6, 100.0), x0, np.diag([1, 1, 1, 1, 100, .05, .01]))
    xs, Ps = rts_smooth(res)
    s, sd, _ = daily_sensitivity(xs, Ps, sim["steps_per_day"])
    return s, sim["s_daily_true"] / sim["s_daily_true"].mean()


@pytest.mark.slow
def test_estimator_recovers_injected_cycle():
    cors = []
    for seed in range(3):
        s, truth = _trial(0.15, seed)
        cors.append(np.corrcoef(s, truth)[0, 1])
    assert np.mean(cors) > 0.85


@pytest.mark.slow
def test_no_signal_control_does_not_invent_large_cycle():
    amps = [amplitude_phase(_trial(0.0, seed)[0], 28)[0] for seed in range(4)]
    assert max(amps) < 0.08          # far below the injected amplitudes the estimator must detect (A >= 0.1)


def test_k1_fit_interval_calibration_and_identifiability_flag():
    rng_tree = RngTree(3)
    cover, n = 0, 12
    for rep in range(n):
        r = rng_tree.indexed("obs", rep)
        temps = np.repeat([5.0, 25.0, 37.0, 45.0], 4); times = np.tile([7.0, 14.0, 28.0, 56.0], 4)
        y = np.exp(-arrhenius_rate(273.15 + temps, 0.001, 90e3, 298.15) * times) + r.normal(0, 0.01, 16)
        obs = pd.DataFrame(dict(study="s", temp_c=temps, time_days=times, potency=np.clip(y, 0, 1), sd=0.01))
        fit = fit_k1(obs, rng_tree.indexed("fit", rep), n_iter=2500, burn=800)
        tk = 273.15 + 30.0; tref = 273.15 + fit.t_ref_c
        pred = np.exp(-np.exp(fit.lnk_draws) * np.exp((fit.ea_draws_j / 8.314) * (1 / tref - 1 / tk)) * 28.0)
        truth = np.exp(-arrhenius_rate(tk, 0.001, 90e3, 298.15) * 28.0)
        cover += np.percentile(pred, 2.5) <= truth <= np.percentile(pred, 97.5)
    assert cover / n >= 0.75
    two = pd.DataFrame(dict(study="s", temp_c=[25.0] * 4 + [37.0] * 0, time_days=[7.0, 14.0, 28.0, 56.0], potency=[.99, .98, .96, .92], sd=0.01))
    assert not fit_k1(two, rng_tree.generator("f2"), n_iter=1500, burn=500).identifiable
