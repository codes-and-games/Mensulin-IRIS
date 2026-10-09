"""F3 (secondary): compounding. Cells 1-4: (no sens loss, no thermal) / (sens only) / (thermal only) / (both). Joint exceedance vs the
product of marginals by swing band, under shared (independent) and coupled (dependent) assignment. Ratio ~ 1 is reported as the NULL."""
import numpy as np
import pandas as pd

from iris.common.provenance import EvidenceClass
from iris.fusion import analytic as an
from iris.fusion import metrics as mt
from iris.fusion.mc_engine import assign_loss, population_arrays
from iris.thermal.potency_draws import full_key
from iris.tools import experiment_lib as xl


def run(ctx):
    cfg = ctx.cfg
    pop, ppop = xl.load_population(ctx, float(cfg["population"]["h"])); pot, ppot = xl.load_potency(ctx); arr = population_arrays(pop)
    rows = []
    for sid in cfg["thermal"]["scenarios"]:
        key = full_key(sid, cfg["fusion"]["duration_d"], float(cfg["fusion"]["transfer_sd"]))
        sub = pot[pot.scenario_id == key].sort_values("epistemic_draw_j")
        if sub.empty:
            ctx.blockers.append(dict(part=key, reason="no stored potency draws")); continue
        pool = 1.0 - sub["potency"].to_numpy()
        for r_pb in cfg["r_pb_levels"]:
            ell = assign_loss(pool, 0, len(pop), "coupled", float(r_pb), arr["rank"], ctx.rng.generator("F3", key, f"{r_pb}"))
            s_red = 1.0 - arr["S"][:, 4]
            a = ell > np.quantile(ell, cfg["quantile"]) if np.ptp(ell) > 0 else np.zeros(len(ell), bool)
            b = s_red > np.quantile(s_red, cfg["quantile"])
            band = mt.swing_band(arr["rank"])
            ret, inter = an.compounding_retained(s_red, ell)
            for bi in range(4):
                m = band == bi
                jp = mt.joint_vs_product(a[m], b[m])
                rows.append(dict(scenario=key, r_pb=float(r_pb), swing_band=bi, **jp, ratio=(jp["joint"] / jp["product"]) if jp["product"] > 0 else np.nan,
                                 mean_interaction_s_times_ell=float(inter[m].mean()), cell_sens_only=float(((~a) & b)[m].mean()), cell_thermal_only=float((a & ~b)[m].mean()), cell_both=float((a & b)[m].mean())))
    df = pd.DataFrame(rows)
    ctx.save_table(df, "compounding", [xl.derived_prov(ctx, ppop[:1] + ppot[:1], EvidenceClass.PROJECTED, "compounding", "joint exceedance vs product of marginals", "iris.fusion.metrics")])
    if len(df) and df.query("r_pb == 0")["ratio"].between(0.8, 1.2).all():
        ctx.log.info("F3 NULL: joint tail ~ product of marginals under independence (algebraic expectation); reported, not hidden")
