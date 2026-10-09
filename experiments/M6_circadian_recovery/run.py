"""M6: circadian (24 h) sensitivity recovery on REAL person-level CGM/insulin/carbohydrate series (document V2).

Pipeline per person: longest run of analysable days -> EKF + RTS smoother -> hourly mean of smoothed ln S (relative to the person mean).
Population statistics: mean profile, 24 h harmonic amplitude and peak hour with a person-level bootstrap interval; PLACEBO control
(random per-person circular shifts of the profile: destroys a shared phase, keeps shapes); split-half reproducibility (even vs odd days);
nuisance-scale sensitivity (ISF0/CSF0 scale x0.7/1/1.4). Supports METHOD PLAUSIBILITY ONLY; says nothing about the menstrual cycle."""
import numpy as np
import pandas as pd

from iris.common.exceptions import ScientificBlocker
from iris.common.provenance import EvidenceClass
from iris.estimator.circadian import circ_diff_h, harmonic24, person_profile
from iris.estimator.ekf import NoiseSpec
from iris.estimator.glucose_insulin_model import ModelConstants
from iris.tools import experiment_lib as xl


def _longest_run(ok: np.ndarray) -> tuple[int, int]:
    best, cur, start, bs = 0, 0, 0, 0
    for i, v in enumerate(ok):
        if v:
            if cur == 0:
                start = i
            cur += 1
            if cur > best:
                best, bs = cur, start
        else:
            cur = 0
    return bs, best


def _select(ev: pd.DataFrame, c: dict):
    """Yield (person_id, cgm, insulin, carb, tdd_u) over each person's longest analysable window."""
    spd = 1440 // int(c["grid_minutes"])
    for pid, d in ev.sort_values(["person_id", "ts_local"]).groupby("person_id"):
        day = d.groupby("date_local")
        cov = (day["glucose_mgdl"].count() / spd).to_numpy()
        icov = (day["insulin_u"].count() / spd).to_numpy()
        ok = (cov >= c["min_cgm_coverage"]) & (icov >= c["min_insulin_coverage"])
        s, n = _longest_run(ok)
        if n < c["min_days"]:
            yield pid, None, None, None, None
            continue
        n = min(n, int(c["max_days"]))
        sl = slice(s * spd, (s + n) * spd)
        g, i, cb = d["glucose_mgdl"].to_numpy()[sl], d["insulin_u"].to_numpy()[sl], d["carb_g"].to_numpy()[sl]
        tdd = float(np.nansum(i) / n)
        yield pid, g, i, cb, tdd


def _circ_shift(profile: np.ndarray, k: int) -> np.ndarray:
    return np.roll(profile, k)


def run(ctx):
    c = ctx.cfg
    dt = float(c["grid_minutes"])
    ev_list, provs, blockers = [], [], []
    for ds in c["datasets"]:
        try:
            ev, pv = xl.load_events(ctx, ds)
            ev_list.append((ds, ev)); provs += pv
        except ScientificBlocker as exc:
            ctx.blockers.append(dict(part=f"dataset:{ds}", reason=str(exc)))
            blockers.append(ds)
    if not ev_list:
        raise ScientificBlocker("events_grid", "no ingested dataset available for any configured dataset", "ingest HUPA-UCM / BrisT1D first (docs/data guides)")
    base = xl.derived_prov(ctx, provs[:1], EvidenceClass.COMPUTED, "circadian_profiles", "EKF+RTS hourly relative ln S", "iris.estimator.circadian")
    noise = NoiseSpec(q_lns=c["q_lns"], q_e=c["q_e"], q_g=c["q_g"], q_small=1e-6, r=float(c["cgm_sd"]) ** 2)
    rng = ctx.rng.generator("M6")
    person_rows, pop_rows, sens_rows, prof_rows = [], [], [], []
    for ds, ev in ev_list:
        sel = [(pid, g, i, cb, tdd) for pid, g, i, cb, tdd in _select(ev, c)]
        n_excl = sum(1 for s in sel if s[1] is None)
        profs = {}
        for scale in c["nuisance_scales"]:
            P, E, O, ids = [], [], [], []
            for pid, g, i, cb, tdd in sel:
                if g is None:
                    continue
                isf0 = float(c["isf_rule_k"]) / tdd * scale
                k = ModelConstants(c["tau_i_min"], c["tau_c_min"], c["ag"], isf0, isf0 * tdd / float(c["icr_rule_k"]), dt)
                r = person_profile(g, i, cb, k, noise, c["g_target"])
                P.append(r["profile"]); E.append(r["profile_even"]); O.append(r["profile_odd"]); ids.append(pid)
                if scale == 1.0:
                    person_rows.append(dict(dataset=ds, person_id=pid, n_days=r["n_days"], amp_ln=r["amp"], peak_hour=r["peak_h"],
                                            split_half_r=float(np.corrcoef(r["profile_even"], r["profile_odd"])[0, 1]), tdd_u=tdd))
            profs[scale] = (np.array(P), np.array(E), np.array(O), ids)
        if 1.0 not in profs or len(profs[1.0][0]) < 3:
            ctx.blockers.append(dict(part=f"population:{ds}", reason=f"only {0 if 1.0 not in profs else len(profs[1.0][0])} analysable persons (<3); excluded {n_excl}"))
            continue
        P, E, O, ids = profs[1.0]
        mean_prof = P.mean(0); amp, peak = harmonic24(mean_prof)
        boot = []
        for _ in range(int(c["n_boot"])):
            b = rng.integers(0, len(P), len(P)); a_, p_ = harmonic24(P[b].mean(0)); boot.append((a_, p_))
        boot = np.array(boot)
        peak_dev = np.array([circ_diff_h(p_, peak) for p_ in boot[:, 1]])
        placebo = []
        for _ in range(int(c["n_placebo"])):
            sh = rng.integers(0, 24, len(P)); placebo.append(harmonic24(np.array([_circ_shift(p, s) for p, s in zip(P, sh)]).mean(0))[0])
        placebo = np.array(placebo)
        pval = float((np.sum(placebo >= amp) + 1) / (len(placebo) + 1))
        ae, pe = harmonic24(E.mean(0)); ao, po = harmonic24(O.mean(0))
        pop_rows.append(dict(dataset=ds, n_persons=len(P), n_excluded=n_excl, amp_ln=amp, amp_ci_low=float(np.percentile(boot[:, 0], 2.5)), amp_ci_high=float(np.percentile(boot[:, 0], 97.5)),
                             peak_hour=peak, peak_dev_ci_low_h=float(np.percentile(peak_dev, 2.5)), peak_dev_ci_high_h=float(np.percentile(peak_dev, 97.5)),
                             placebo_amp_mean=float(placebo.mean()), placebo_amp_p95=float(np.percentile(placebo, 95)), placebo_p_value=pval,
                             split_half_profile_r=float(np.corrcoef(E.mean(0), O.mean(0))[0, 1]), split_half_peak_diff_h=circ_diff_h(pe, po),
                             reproducible=bool(np.corrcoef(E.mean(0), O.mean(0))[0, 1] > 0.5 and abs(circ_diff_h(pe, po)) <= 3.0 and pval < c["alpha"]),
                             caveat="method plausibility only; no cycle claim; direction vs literature NOT assessed here"))
        for h in range(24):
            prof_rows.append(dict(dataset=ds, hour=h, mean_rel_ln_s=float(mean_prof[h]), sd_between_persons=float(P[:, h].std(ddof=1))))
        for scale, (Ps, *_rest) in profs.items():
            a_, p_ = harmonic24(Ps.mean(0)) if len(Ps) else (np.nan, np.nan)
            sens_rows.append(dict(dataset=ds, nuisance_scale=scale, amp_ln=a_, peak_hour=p_, n_persons=len(Ps)))
    if not pop_rows:
        raise ScientificBlocker("circadian_population", "no dataset had >= 3 analysable persons", "check ingest QC / min_days / coverage thresholds")
    ctx.save_table(pd.DataFrame(person_rows), "circadian_person", [base])
    ctx.save_table(pd.DataFrame(pop_rows), "circadian_population", [base])
    ctx.save_table(pd.DataFrame(prof_rows), "circadian_profile", [base])
    ctx.save_table(pd.DataFrame(sens_rows), "circadian_nuisance_sensitivity", [base])
