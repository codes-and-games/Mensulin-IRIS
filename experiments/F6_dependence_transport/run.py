"""F6: dependence (r_PB, R_B) and transportability (st) sweeps; flip points recorded. A conclusion that flips at the smallest non-zero
dependence is reported as conditional on exact independence."""
import numpy as np
import pandas as pd

from iris.common.provenance import EvidenceClass
from iris.fusion.admissible_set import COMPONENTS, Theta
from iris.fusion.theta_eval import evaluate_points
from iris.tools import experiment_lib as xl


def _theta(ref: dict, **over) -> Theta:
    d = {**ref, **over}
    return Theta(tuple(d[c] for c in COMPONENTS), "S")


def _flip(xs, ms):
    xs, ms = np.asarray(xs, float), np.asarray(ms, float)
    for i in range(len(xs) - 1):
        if np.isfinite(ms[i]) and np.isfinite(ms[i + 1]) and ms[i] * ms[i + 1] < 0:
            return float(xs[i] + (xs[i + 1] - xs[i]) * (0 - ms[i]) / (ms[i + 1] - ms[i]))
    return np.nan


def run(ctx):
    cfg = ctx.cfg
    concl = xl.cfg_yaml(ctx, "docs/prereg/conclusions.yaml")["conclusions"]
    taus = sorted({float(c["threshold_units"]) for c in concl})
    ev, aset = xl.evaluator_for(ctx, taus, int(cfg["n_eval"]))
    ref = {c: aset[c]["reference"] for c in COMPONENTS}; ref["s"] = cfg["scenario"]
    rows, flips = [], []
    for c in concl:
        for axis, values, key in (("r_PB", cfg["r_pb_grid"], "r_PB"), ("st", cfg["st_grid"], "st"), ("R_B", ["independent", "tdd_sigma_pos", "tdd_sigma_neg", "s_gamma_pos", "s_gamma_neg"], "R_B")):
            pts = [_theta(ref, **{key: v}) for v in values]
            e = evaluate_points(ev, pts, c["metric"], float(c["threshold_units"]), c["comparator"], float(c["value"]))
            e["conclusion"], e["axis"] = c["id"], axis; e["axis_value"] = [str(v) for v in values]; rows.append(e[["conclusion", "axis", "axis_value", "margin", "blocked", "blocked_reason"]])
            if axis != "R_B":
                fp = _flip(values, e["margin"].to_numpy())
                flips.append(dict(conclusion=c["id"], axis=axis, flip_point=fp, margin_at_zero_dependence=float(e["margin"].iloc[list(values).index(0.0)]) if 0.0 in values else np.nan,
                                  note="conditional on exact independence if sign changes at the smallest non-zero value" if (axis == "r_PB" and np.isfinite(fp) and abs(fp) <= min(abs(v) for v in values if v != 0) * 1.01) else ""))
    prov = xl.derived_prov(ctx, [xl.source_prov(ctx, "S1")], EvidenceClass.PROJECTED, "dependence_sweeps", "r_PB, st and R_B sweeps at the reference theta", "iris.fusion.theta_eval")
    ctx.save_table(pd.concat(rows, ignore_index=True), "sweeps", [prov]); ctx.save_table(pd.DataFrame(flips), "flip_points", [prov])
