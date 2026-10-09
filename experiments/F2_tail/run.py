"""F2: tail analysis at N = 100,000 (PROJECTED): direct tail probabilities with MC SE and distribution-free product-tail bounds.
Tails are computed directly; they are never inferred from means."""
import numpy as np
import pandas as pd

from iris.common.provenance import EvidenceClass
from iris.fusion import endpoints as ep
from iris.fusion import metrics as mt
from iris.fusion.mc_engine import population_arrays
from iris.thermal.potency_draws import full_key
from iris.tools import experiment_lib as xl


def run(ctx):
    cfg = ctx.cfg
    n_tail = int(cfg["population"]["n_tail"]); h = float(cfg["population"]["h"])
    pop, spec = xl.population_for(ctx, eta=float(cfg["population"]["eta"]), h=h, n=n_tail, label=f"h{h}_tail")
    arr = population_arrays(pop)
    pot, ppot = xl.load_potency(ctx)
    rows = []
    for sid in cfg["thermal"]["scenarios"]:
        key = full_key(sid, cfg["fusion"]["duration_d"], float(cfg["fusion"]["transfer_sd"]))
        sub = pot[pot.scenario_id == key].sort_values("epistemic_draw_j")
        if sub.empty:
            ctx.blockers.append(dict(part=key, reason="no stored potency draws")); continue
        pool = 1.0 - sub["potency"].to_numpy()
        for j, ell in enumerate(pool):
            for t in cfg["tail_thresholds_units"]:
                for case, du in (("A", arr["R"][:, 4] * ell), ("B", arr["R"][:, 4] - arr["tdd"] * (1 - ell))):
                    p, se = mt.exceedance(du, t)
                    rows.append(dict(scenario=key, epistemic_draw_j=j, dosing_case=case, threshold=float(t), prob=p, mc_se=se, n=n_tail))
        env = ep.product_tail_envelope(arr, pool, 4, cfg["tail_thresholds_units"], n=20000, rng=ctx.rng.generator("F2_env", key)); env["scenario"] = key
        ctx.save_table(env, f"product_tail_envelope_{sid}", [xl.population_prov(ctx, spec).derive(evidence_class=EvidenceClass.COMPUTED, source_id=f"bounds:{sid}", transformation="Makarov bounds on empirical marginals", generated_by="iris.fusion.bounds")])
    df = pd.DataFrame(rows)
    prov = xl.population_prov(ctx, spec).derive(evidence_class=EvidenceClass.PROJECTED, source_id="tail_exceedance", transformation="direct tail probabilities N=%d" % n_tail, generated_by="experiments.F2_tail", extra_parents=tuple(x.source_id for x in ppot[:1]))
    ctx.save_table(df, "tail_exceedance", [prov])
    if len(df):
        # MC-SE convergence diagnostic across N (sub-sampling the stored population)
        conv = []
        for n in (1000, 5000, 20000, n_tail):
            sub = arr["R"][:n, 4]; ell = float(np.median(1 - pot["potency"]))
            p, se = mt.exceedance(sub * ell, cfg["tail_thresholds_units"][1]); conv.append(dict(n=n, prob=p, mc_se=se))
        ctx.save_table(pd.DataFrame(conv), "mc_convergence", [prov])
