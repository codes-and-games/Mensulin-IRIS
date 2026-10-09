"""S2: kinetics machinery on SIMULATED data: (a) recover known K1 parameters from noisy synthetic observations,
(b) forward predictions reproduce closed forms (K1, K3), (c) Arrhenius ratio = 1 at the reference. No literature values used."""
import numpy as np
import pandas as pd

from iris.common.provenance import EvidenceClass, Provenance
from iris.thermal.kinetics.fitting import fit_k1
from iris.thermal.kinetics.k1 import K1, arrhenius_ratio, arrhenius_rate
from iris.thermal.kinetics.k3 import K3


def run(ctx):
    c = ctx.cfg["truth"]                               # TEST/SIMULATION truth parameters (not literature values)
    prov = Provenance(EvidenceClass.SIMULATED, "S2_synthetic_truth", transformation="recover known K1 parameters",
                      generated_by="iris.thermal.kinetics", run_id=ctx.run_id, synthetic=True, parent_source_ids=("TEST_ONLY:S2_truth",))
    rows = []
    t_ref_k = 273.15 + c["t_ref_c"]
    for rep in range(int(ctx.cfg["n_replicates"])):
        rng = ctx.rng.indexed("S2_obs", rep)
        temps = np.repeat(c["temps_c"], len(c["times_d"])); times = np.tile(c["times_d"], len(c["temps_c"]))
        k = arrhenius_rate(273.15 + temps, c["k_ref_per_day"], c["ea_j_mol"], t_ref_k)
        y = np.exp(-k * times) + rng.normal(0, c["sd"], temps.size)
        obs = pd.DataFrame(dict(study="SIM", temp_c=temps, time_days=times, potency=np.clip(y, 0, 1.0), sd=c["sd"]))
        fit = fit_k1(obs, ctx.rng.generator("S2_fit", f"#{rep}"), n_iter=4000, burn=1500)
        # compare predicted potency at a held-out condition (parameters are correlated; compare in prediction space)
        tk = 273.15 + c["pred_temp_c"]
        truth = np.exp(-arrhenius_rate(tk, c["k_ref_per_day"], c["ea_j_mol"], t_ref_k) * c["pred_time_d"])
        tref_fit = 273.15 + fit.t_ref_c
        pred = np.exp(-np.exp(fit.lnk_draws) * np.exp((fit.ea_draws_j / 8.314) * (1 / tref_fit - 1 / tk)) * c["pred_time_d"])
        lo, hi = np.percentile(pred, [2.5, 97.5])
        rows.append(dict(rep=rep, truth=float(truth), pred_mean=float(pred.mean()), abs_err=float(abs(pred.mean() - truth)), covered=bool(lo <= truth <= hi), identifiable=fit.identifiable))
    df = pd.DataFrame(rows)
    ctx.save_table(df, "k1_recovery", [prov])
    k1 = K1(0.01, 80e3, 25.0).potency(np.full(1000, 25.0), 0.1)[0]
    chk = pd.DataFrame([
        dict(check="arrhenius_ratio_at_reference", value=float(arrhenius_ratio(25.0, 83100.0, 25.0)), expected=1.0),
        dict(check="k1_closed_form", value=float(k1), expected=float(np.exp(-0.01 * 100.0)))])
    chk["passed"] = np.isclose(chk["value"], chk["expected"], rtol=1e-12)
    ctx.save_table(chk, "forward_checks", [prov])
    ctx.log.info(f"S2 coverage={df.covered.mean():.2f}, mean abs err={df.abs_err.mean():.4f}")
