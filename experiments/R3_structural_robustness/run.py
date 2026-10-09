"""R3: structural robustness: each kinetic study alone, pessimistic/optimistic envelopes, K0-only, K1-only. If conclusions flip, the flip is
reported plainly (no preferred result is selected)."""
import numpy as np
import pandas as pd

from iris.common.provenance import EvidenceClass
from iris.fusion.admissible_set import COMPONENTS, Theta
from iris.fusion.theta_eval import select_pool
from iris.thermal.potency_draws import full_key
from iris.tools import experiment_lib as xl


def run(ctx):
    cfg = ctx.cfg
    taus = sorted({float(c["threshold_units"]) for c in xl.cfg_yaml(ctx, "docs/prereg/conclusions.yaml")["conclusions"]})
    ev, aset = xl.evaluator_for(ctx, taus, int(cfg["n_eval"]))
    concl = xl.cfg_yaml(ctx, "docs/prereg/conclusions.yaml")["conclusions"]
    ref = {c: aset[c]["reference"] for c in COMPONENTS}; ref["s"] = cfg["scenario"]
    key = full_key(cfg["scenario"], cfg["fusion"]["duration_d"], float(cfg["fusion"]["transfer_sd"]))
    studies = sorted(ev.potency[(ev.potency.scenario_id == key) & (~ev.potency.is_null_model)]["kinetic_study"].unique())
    choices = ["ensemble", "K1_only", "K0", "pessimistic_envelope", "optimistic_envelope"]
    rows = []
    orig = ev.potency
    for ch in choices + [f"study:{s}" for s in studies]:
        ev.cache.clear() if False else None
        if ch.startswith("study:"):
            ev.potency = orig[(orig.kinetic_study == ch.split(":", 1)[1]) | (orig.scenario_id != key)]
            th = {**ref, "s": cfg["scenario"], "m": "ensemble"}
        else:
            ev.potency = orig; th = {**ref, "m": ch}
        try:
            m = ev.metrics(Theta(tuple(th[c] for c in COMPONENTS), "S"))
        except Exception as e:
            rows.append(dict(structure=ch, conclusion="*", holds=None, value=np.nan, note=f"blocked: {str(e)[:100]}")); continue
        for c in concl:
            v = m[f"{c['metric']}@{float(c['threshold_units']):g}"]
            rows.append(dict(structure=ch, conclusion=c["id"], value=float(v) if np.isfinite(v) else np.nan,
                             holds=bool(np.isfinite(v) and ((v > c["value"]) if c["comparator"] == ">" else (v < c["value"]))), note=""))
    ev.potency = orig
    df = pd.DataFrame(rows)
    flips = df.dropna(subset=["holds"]).groupby("conclusion")["holds"].agg(lambda x: bool(x.nunique() > 1)).rename("conclusion_flips_across_structures").reset_index()
    prov = xl.derived_prov(ctx, [xl.source_prov(ctx, "S1")], EvidenceClass.PROJECTED, "structural_robustness", "conclusions under alternative kinetic structures", "iris.fusion.theta_eval")
    ctx.save_table(df, "structural_results", [prov]); ctx.save_table(flips, "structural_flips", [prov])
    if flips["conclusion_flips_across_structures"].any():
        ctx.log.warn("conclusion(s) FLIP across kinetic structures: " + ", ".join(flips.loc[flips.conclusion_flips_across_structures, "conclusion"]) + " -- reported, not resolved")
