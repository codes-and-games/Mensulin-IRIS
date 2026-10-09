"""F4: ablations A0-A10 (reduced documented set A1,A3,A5,A6 plus A0,A2,A4,A8,A9). Common random numbers: every configuration uses the same
population, same loss pool and same assignment stream; only the ablated element changes. A4 (circularity control) must push phi toward 1;
if it does not, that is flagged as a possible circularity/bug and the run records FAILED_CONTROL."""
import numpy as np
import pandas as pd

from iris.common.provenance import EvidenceClass
from iris.evaluate import ablations as ab
from iris.fusion import analytic as an
from iris.fusion import controls
from iris.fusion import metrics as mt
from iris.fusion.mc_engine import assign_loss, population_arrays
from iris.thermal.potency_draws import full_key
from iris.tools import experiment_lib as xl


def _stats(arr, ell, taus, label, rng):
    r_hi = arr["R"][:, 4]; du = r_hi * ell
    ph = xl.phi_ratio(arr)
    row = dict(config=label, phi=ph["phi"], rho_ratio=ph["rho_ratio"], mean_shortfall_u=float(du.mean()))
    for t in taus:
        row[f"exceed@{t:g}"] = float((du > t).mean())
        e = du > t
        row[f"tci@{t:g}"] = mt.tci(e, arr["rank"])
    return row


def run(ctx):
    cfg = ctx.cfg
    pop, ppop = xl.load_population(ctx, float(cfg["population"]["h"])); pot, ppot = xl.load_potency(ctx)
    base = population_arrays(pop); n = len(pop); taus = cfg["thresholds_units"]
    key = full_key(cfg["scenario"], cfg["fusion"]["duration_d"], float(cfg["fusion"]["transfer_sd"]))
    sub = pot[pot.scenario_id == key].sort_values("epistemic_draw_j")
    if sub.empty:
        from iris.common.exceptions import ScientificBlocker
        raise ScientificBlocker(key, "no stored potency draws", "run E4")
    pool = 1.0 - sub["potency"].to_numpy()
    rows = []
    for j in range(min(int(cfg["fusion"]["J"]), len(pool))):
        ell = np.full(n, pool[j])                                           # shared mode: loss of epistemic draw j
        rg = lambda name: ctx.rng.generator("F4", name, f"#{j}")
        rows.append({**_stats(base, ell, taus, "A0_baseline", rg("a0")), "j": j})
        rows.append({**_stats(base, 1.0 - ab.a1_no_thermal(1 - ell), taus, "A1_no_thermal", rg("a1")), "j": j})
        S2, R2 = ab.a2_no_cycle(base["S"], base["rho"]); a2 = dict(base, S=S2, rho=R2, R=base["tdd"][:, None] * R2)
        rows.append({**_stats(a2, ell, taus, "A2_no_cycle", rg("a2")), "j": j})
        a3 = dict(base, R=ab.a3_mean_biology(base["R"]))
        rows.append({**_stats(a3, ell, taus, "A3_mean_biology", rg("a3")), "j": j})
        rho4 = ab.a4_circular(base["S"]); a4 = dict(base, rho=rho4, R=base["tdd"][:, None] * rho4)
        rows.append({**_stats(a4, ell, taus, "A4_circularity_control", rg("a4")), "j": j})
        rows.append({**_stats(base, ab.a5_deterministic_potency(pool)[0] * np.ones(n), taus, "A5_deterministic_potency", rg("a5")), "j": j})
        p8 = controls.control_c3_permute_phases(base["R"], rg("a8")); a8 = dict(base, R=p8)
        rows.append({**_stats(a8, ell, taus, "A8_permuted_phase_labels", rg("a8b")), "j": j})
        # A9: Case B shortfall at the high phase
        db = an.shortfall_case_b(base["R"][:, 4], base["tdd"], 1 - ell)
        r9 = dict(config="A9_case_B", j=j, mean_shortfall_u=float(np.maximum(db, 0).mean()), phi=xl.phi_ratio(base)["phi"], rho_ratio=xl.phi_ratio(base)["rho_ratio"])
        for t in taus:
            r9[f"exceed@{t:g}"] = float((db > t).mean())
        rows.append(r9)
    # A6: each kinetic study alone (single-structure ablation)
    for study, g in pot[(pot.scenario_id == key) & (~pot.is_null_model)].groupby("kinetic_study"):
        l = 1.0 - g["potency"].to_numpy()
        r = _stats(base, np.full(n, np.median(l)), taus, f"A6_single_study:{study}", ctx.rng.generator("F4", "a6", study)); r["j"] = -1; rows.append(r)
    df = pd.DataFrame(rows)
    ctx.save_table(df, "ablation_rows", [xl.derived_prov(ctx, ppop[:1] + ppot[:1], EvidenceClass.PROJECTED, "ablation_rows", "A0-A9 with common random numbers", "iris.evaluate.ablations")])
    col = [c for c in df.columns if c.startswith("exceed@") or c in ("phi", "mean_shortfall_u")]
    agg = df.groupby("config")[col].agg(["median", lambda x: x.quantile(0.025), lambda x: x.quantile(0.975)])
    agg.columns = ["_".join(map(str, c)).replace("<lambda_0>", "lo").replace("<lambda_1>", "hi") for c in agg.columns]
    ctx.save_table(agg.reset_index(), "ablation_table", [xl.derived_prov(ctx, ppop[:1] + ppot[:1], EvidenceClass.PROJECTED, "ablation_table", "epistemic intervals across draws", "iris.evaluate.ablations")])
    phi0 = df.loc[df.config == "A0_baseline", "phi"].median(); phi4 = df.loc[df.config == "A4_circularity_control", "phi"].median()
    ctx.log.info(f"phi A0={phi0:.4f} A4={phi4:.4f}")
    if not abs(phi4 - 1.0) < abs(phi0 - 1.0) + 1e-12 and abs(phi4 - 1.0) > 1e-6:
        ctx.log.warn("FAILED_CONTROL: A4 did not push phi toward 1 (investigate circularity or bug)")
