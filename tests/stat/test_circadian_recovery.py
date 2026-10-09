"""Statistical verification of the circadian profile estimator on SIMULATED people (TEST-grade constants)."""
import numpy as np

from iris.estimator.circadian import circ_diff_h, harmonic24, person_profile
from iris.estimator.ekf import NoiseSpec
from iris.estimator.glucose_insulin_model import ModelConstants
from iris.estimator.simulator import SimDesign, simulate

K = ModelConstants(55.0, 40.0, 0.9, 50.0, 3.0, 5.0)
NZ = NoiseSpec(q_lns=1e-4, q_e=1e-8, q_g=0.3, q_small=1e-6, r=100.0)


def _profile(amp, seed, peak=8.0, k_est=K):
    d = SimDesign(days=14, amplitude=0.0, cycle_len_d=28, phase_rad=0.0, cgm_sd=10.0, carb_error_sd=0.2, gap_fraction=0.1, g_target=120.0,
                  e_offset=0.2, process_sd_g=0.5, circadian_amp=amp, circadian_peak_h=peak)
    sim = simulate(d, K, np.random.default_rng(seed))
    return person_profile(sim["cgm"], sim["u"] * 5.0, sim["carb_logged"] * 5.0, k_est, NZ, 120.0)


def test_harmonic24_exact():
    h = np.arange(24) + 0.5
    amp, peak = harmonic24(0.3 * np.cos(2 * np.pi * (h - 6.0) / 24))
    assert abs(amp - 0.3) < 1e-9 and abs(circ_diff_h(peak, 6.0)) < 1e-6


def test_recovers_injected_peak_and_is_reproducible():
    rs = [_profile(0.3, s) for s in range(4)]
    assert all(abs(circ_diff_h(r["peak_h"], 8.0)) < 1.5 for r in rs)
    assert all(np.corrcoef(r["profile_even"], r["profile_odd"])[0, 1] > 0.8 for r in rs)
    assert 0.15 < np.mean([r["amp"] for r in rs]) < 0.35          # attenuated but clearly present (true 0.3)


def test_null_gives_small_amplitude_and_no_shared_phase():
    rs = [_profile(0.0, 50 + s) for s in range(6)]
    assert np.mean([r["amp"] for r in rs]) < 0.08                  # no cycle invented
    mean_prof = np.mean([r["profile"] for r in rs], axis=0)
    assert harmonic24(mean_prof)[0] < 0.05                         # random phases average out at population level
