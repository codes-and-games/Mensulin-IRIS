"""R1: one-at-a-time tornado and Sobol global sensitivity of Pr(shortfall > tau) to biological and thermal epistemic inputs.
Thermal variance share = sum of total-order indices of thermal inputs (kinetic model choice, transfer discrepancy);
climate-input uncertainty is reported as 'not applicable' while the only climate-driven scenario (S5) is blocked. Indices are
checked for stability across seeds; unstable indices are flagged."""
import numpy as np
import pandas as pd

from iris.common.provenance import EvidenceClass
from iris.evaluate.sensitivity import sobol_indices, tornado
from iris.fusion.admissible_set import COMPONENTS, Theta
from iris.tools import experiment_lib as xl

THERMAL, BIOLOGY = ("st", "m_idx"), ("h", "eta", "r_PB")


def run(ctx):
    cfg = ctx.cfg
    tau = float(cfg["tau_units"])
    ev, aset = xl.evaluator_for(ctx, [tau], int(cfg["n_eval"]))
    ref = {c: aset[c]["reference"] for c in COMPONENTS}; ref["s"] = cfg["scenario"]
    models = cfg["model_choices"]; sts = cfg["st_levels"]

    def p_het(h, eta, r, st_i, m_i):
        th = dict(ref, h=round(float(h), 2), eta=round(float(eta), 2), r_PB=round(float(r), 2), st=sts[int(st_i)], m=models[int(m_i)])
        return ev.metrics(Theta(tuple(th[c] for c in COMPONENTS), "S"))[f"p_het@{tau:g}"]

    names = ["h", "eta", "r_PB", "st", "m_idx"]
    bounds = [(0.5, 2.0), (0.0, 1.0), (-0.8, 0.8), (0, len(sts) - 1e-9), (0, len(models) - 1e-9)]
    fn = lambda X: np.array([p_het(*row) for row in X])
    reps = []
    for seed in cfg["sobol_seeds"]:
        d = sobol_indices(fn, names, bounds, int(cfg["sobol_n"]), int(seed)); d["seed"] = seed; reps.append(d)
    allr = pd.concat(reps, ignore_index=True)
    agg = allr.groupby("parameter")[["S1", "ST"]].agg(["mean", "std"]).reset_index(); agg.columns = ["_".join(c).strip("_") for c in agg.columns]
    agg["unstable"] = agg["ST_std"] > float(cfg["instability_threshold"])
    thermal_share = float(allr[allr.parameter.isin(THERMAL)].groupby("seed")["ST"].sum().mean()); bio_share = float(allr[allr.parameter.isin(BIOLOGY)].groupby("seed")["ST"].sum().mean())
    prov = xl.derived_prov(ctx, [xl.source_prov(ctx, "S1")], EvidenceClass.COMPUTED, "sobol", "Sobol indices via SALib over declared epistemic parameters", "iris.evaluate.sensitivity")
    ctx.save_table(allr, "sobol_by_seed", [prov]); ctx.save_table(agg, "sobol_summary", [prov])
    ctx.save_table(pd.DataFrame([dict(thermal_total_order_sum=thermal_share, biology_total_order_sum=bio_share, climate_input="not applicable (S5 blocked; parametric scenarios carry no climate input)",
                                      note="total-order sums can exceed 1 under interactions")]), "thermal_variance_share", [prov])
    base = dict(h=1.0, eta=0.5, r=0.0, st_i=0, m_i=0)
    tor = tornado(lambda d: p_het(**d), base, {"h": (0.5, 2.0), "eta": (0.0, 1.0), "r": (-0.8, 0.8), "st_i": (0, len(sts) - 1), "m_i": (0, len(models) - 1)})
    ctx.save_table(tor, "tornado", [prov])
