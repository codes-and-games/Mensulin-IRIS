"""S1: estimator ground-truth recovery (SIMULATED). Inject S_t = 1 + A sin(2 pi t/Lc + theta); run EKF + RTS smoother; fit a harmonic to the daily S;
report amplitude/phase error, interval coverage, and the FALSE-DETECTION rate at A = 0 (the estimator must not invent a cycle).
Time constants in the simulator and estimator are ASSUMPTION levels (document T4); a misspecified-tau control is included."""
import numpy as np
import pandas as pd

from iris.common.provenance import EvidenceClass, Provenance
from iris.estimator.ekf import NoiseSpec, run_ekf
from iris.estimator.glucose_insulin_model import IDX, N_STATE, ModelConstants
from iris.estimator.simulator import SimDesign, simulate
from iris.estimator.smoother import daily_sensitivity, rts_smooth
from iris.evaluate.calibration_metrics import amplitude_phase, gaussian_coverage, phase_error


def _one(ctx, A, Lc, cgm_sd, carb_err, gap, rep, k_true, k_est, label):
    c = ctx.cfg
    rng = ctx.rng.generator("S1", label, f"A{A}", f"L{Lc}", f"n{cgm_sd}", f"c{carb_err}", f"g{gap}", f"#{rep}")
    theta = float(rng.uniform(0, 2 * np.pi))
    d = SimDesign(days=int(c["days"]), amplitude=A, cycle_len_d=Lc, phase_rad=theta, cgm_sd=cgm_sd, carb_error_sd=carb_err, gap_fraction=gap,
                  g_target=c["g_target"], e_offset=c["e_offset"], process_sd_g=c["process_sd_g"])
    sim = simulate(d, k_true, rng)
    noise = NoiseSpec(q_lns=c["q_lns"], q_e=c["q_e"], q_g=c["q_g"], q_small=1e-6, r=cgm_sd ** 2)
    x0 = np.zeros(N_STATE); x0[IDX["I1"]] = x0[IDX["I2"]] = sim["u_basal_u_per_min"] * k_est.tau_i_min; x0[IDX["G"]] = c["g_target"]; x0[IDX["E"]] = c["e_offset"]
    res = run_ekf(sim["cgm"], sim["u"], sim["carb_logged"], k_est, noise, x0, np.diag([1, 1, 1, 1, 100, 0.05, 0.01]))
    xs, Ps = rts_smooth(res)
    s, sd, lm = daily_sensitivity(xs, Ps, sim["steps_per_day"])
    truth = sim["s_daily_true"] / sim["s_daily_true"].mean()
    amp, ph, p = amplitude_phase(s, Lc)
    return dict(label=label, A=A, Lc=Lc, cgm_sd=cgm_sd, carb_err=carb_err, gap=gap, rep=rep, amp_est=amp, amp_err=amp - A,
                phase_err=phase_error(ph, (np.pi / 2 - theta) % (2 * np.pi)) if A > 0 else np.nan,   # true S = cos(2 pi t/Lc - (pi/2 - theta))
                f_pvalue=p, detected=bool(p < c["alpha"]), cover95=gaussian_coverage(truth, s, sd), rmse=float(np.sqrt(np.mean((s - truth) ** 2))))


def run(ctx):
    c = ctx.cfg
    dt = float(c["dt_min"])
    k_true = ModelConstants(c["tau_i_min"], c["tau_c_min"], c["ag"], c["isf0"], c["csf0"], dt)
    k_mis = ModelConstants(c["tau_i_min"] * c["misspec_factor"], c["tau_c_min"] * c["misspec_factor"], c["ag"], c["isf0"], c["csf0"], dt)
    prov = Provenance(EvidenceClass.SIMULATED, "S1_virtual_people", transformation="simulate -> EKF -> RTS -> harmonic", generated_by="iris.estimator", run_id=ctx.run_id,
                      synthetic=True, parent_source_ids=("TEST_ONLY:S1_simulator_constants",))
    rows = []
    for A in c["amplitudes"]:
        for Lc in c["cycle_lengths"]:
            for rep in range(int(c["n_reps"])):
                rows.append(_one(ctx, A, Lc, c["cgm_sd"], c["carb_err"], c["gap"], rep, k_true, k_true, "correct_model"))
    for rep in range(int(c["n_reps"])):                                     # misspecified time-constant control
        rows.append(_one(ctx, c["control_A"], c["cycle_lengths"][0], c["cgm_sd"], c["carb_err"], c["gap"], rep, k_true, k_mis, "misspecified_tau"))
    df = pd.DataFrame(rows)
    ctx.save_table(df, "recovery_trials", [prov])
    summ = df.groupby(["label", "A", "Lc"]).agg(n=("rep", "count"), amp_bias=("amp_err", "mean"), amp_rmse=("amp_err", lambda x: float(np.sqrt(np.mean(x ** 2)))),
                                               detect_rate=("detected", "mean"), coverage95=("cover95", "mean"), rmse=("rmse", "mean")).reset_index()
    ctx.save_table(summ, "recovery_summary", [prov])
    fa = df[(df.A == 0.0) & (df.label == "correct_model")]["detected"].mean()
    ctx.log.info(f"S1 false-detection rate at A=0: {fa:.3f} (nominal alpha={c['alpha']})")
    if fa > 2 * c["alpha"] + 0.05:
        ctx.log.warn("S1 FAILED_CONTROL: estimator invents a cycle at A=0 (false-detection rate above tolerance)")
