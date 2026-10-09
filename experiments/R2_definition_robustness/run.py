"""R2: robustness to definitions: thresholds, eta grid, dosing case, ISF constant. Phase representation (three-phase) and +/-2-day boundary shifts
need the extracted day windows ([TO EXTRACT]) and are recorded as BLOCKED, not approximated. Output: stability matrix."""
import numpy as np
import pandas as pd

from iris.common.provenance import EvidenceClass
from iris.fusion.admissible_set import COMPONENTS, Theta
from iris.tools import experiment_lib as xl


def run(ctx):
    cfg = ctx.cfg
    taus = [float(t) for t in cfg["thresholds_units"]]
    ev, aset = xl.evaluator_for(ctx, taus, int(cfg["n_eval"]))
    concl = xl.cfg_yaml(ctx, "docs/prereg/conclusions.yaml")["conclusions"]
    ref = {c: aset[c]["reference"] for c in COMPONENTS}; ref["s"] = cfg["scenario"]
    rows = []
    variants = [("threshold", {}, t) for t in taus] + [("eta", {"eta": e}, None) for e in cfg["eta_grid"]] + \
               [("dosing_case", {"d": d}, None) for d in ("A", "B")] + [("isf_constant", {"isf": k}, None) for k in aset["isf"]["stress_levels"][:2] + [aset["isf"]["reference"]]]
    for kind, over, tau in variants:
        th = {**ref, **over}
        m = ev.metrics(Theta(tuple(th[c] for c in COMPONENTS), "S"))
        for c in concl:
            t = tau if tau is not None else float(c["threshold_units"])
            if f"{c['metric']}@{t:g}" not in m:
                continue
            v = m[f"{c['metric']}@{t:g}"]
            hold = bool(np.isfinite(v) and ((v > c["value"]) if c["comparator"] == ">" else (v < c["value"])))
            rows.append(dict(conclusion=c["id"], variation=kind, setting=str(over or t), threshold_units=t, value=float(v), holds=hold))
    for kind in ("three_phase_representation", "boundary_shift_plus_minus_2d"):
        for c in concl:
            rows.append(dict(conclusion=c["id"], variation=kind, setting="BLOCKED", threshold_units=np.nan, value=np.nan, holds=None))
    df = pd.DataFrame(rows)
    prov = xl.derived_prov(ctx, [xl.source_prov(ctx, "S1")], EvidenceClass.PROJECTED, "stability_matrix", "F1-style evaluation under alternative definitions", "iris.fusion.theta_eval")
    ctx.save_table(df, "stability_matrix", [prov])
    summ = df[df.setting != "BLOCKED"].groupby("conclusion")["holds"].agg(n="count", n_hold="sum").reset_index()
    summ["stable"] = summ.n == summ.n_hold
    ctx.save_table(summ, "stability_summary", [prov])
    ctx.blockers.append(dict(part="R2.phase_representation", reason="day windows [TO EXTRACT]: three-phase and boundary-shift variants not run"))
