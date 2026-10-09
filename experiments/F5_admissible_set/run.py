"""F5: conclusion-set classification C_set(Theta) for PRE-REGISTERED conclusions: full/sub-sampled factorial grid + Latin hypercube
(+ adversarial search with a fixed budget) separately over Theta_E and Theta_S. Theta_E and Theta_S are never pooled.
Unfrozen conclusions are refused outside test mode (post-hoc conclusions). 'computationally_robust' is a statement about the declared
search design and budget, NOT proof."""
import numpy as np
import pandas as pd

from iris.common.exceptions import ScientificBlocker
from iris.common.parameters import RunMode
from iris.common.provenance import EvidenceClass
from iris.fusion.admissible_set import AdmissibleSet, classify_conclusion
from iris.fusion.adversary import adversarial_search
from iris.fusion.theta_eval import evaluate_points
from iris.tools import experiment_lib as xl


def run(ctx):
    cfg = ctx.cfg
    concl = xl.cfg_yaml(ctx, "docs/prereg/conclusions.yaml")["conclusions"]
    if ctx.mode is not RunMode.TEST:
        unfrozen = [c["id"] for c in concl if not c.get("frozen")]
        if unfrozen:
            raise ScientificBlocker("preregistered_conclusions", f"not frozen: {unfrozen}",
                                    "owner must review, date and freeze docs/prereg/conclusions.yaml before any fusion output is inspected")
    aset = AdmissibleSet.from_yaml(xl.repo(ctx) / "configs/fusion/admissible_set.yaml")
    taus = sorted({float(c["threshold_units"]) for c in concl})
    ev, _ = xl.evaluator_for(ctx, taus, int(cfg["n_eval"]))
    rng = ctx.rng.generator("F5_design")
    sets = {"E": aset.conditioned_on_E(), "S": []}
    class_rows, point_frames, adv_rows, cov_rows = [], [], [], []
    for c in concl:
        for which in ("E", "S"):
            pts, cov = aset.factorial(which, int(cfg["max_grid_points"][which]), rng)
            lhs = aset.latin_hypercube(which, int(cfg["lhs_points"]), rng)
            cov_rows.append(dict(conclusion=c["id"], **cov, lhs_points=len(lhs), conditioned_on=",".join(sets[which])))
            evals = evaluate_points(ev, pts + lhs, c["metric"], float(c["threshold_units"]), c["comparator"], float(c["value"]))
            evals["conclusion"], evals["analysis_set"] = c["id"], which
            point_frames.append(evals)
            mf = ev.margin_fn(c["metric"], float(c["threshold_units"]), c["comparator"], float(c["value"]))
            adv = adversarial_search(mf, aset, which, ctx.rng.child("F5", c["id"]), budget=int(cfg["adversary_budget"]), popsize=int(cfg.get("adversary_popsize", 8)))
            adv_rows.append(dict(conclusion=c["id"], **{k: (str(v) if isinstance(v, dict) else v) for k, v in adv.items()}))
            res = classify_conclusion(c["id"], which, evals, adv, sets[which])
            class_rows.append(dict(conclusion=c["id"], analysis_set=which, classification=res.classification, n_points=res.n_points, n_hold=res.n_hold,
                                   n_undefined=res.n_undefined, conditioned_on=",".join(res.conditioned_on), controlling_component=res.controlling_component,
                                   flip_levels=str(res.flip_levels), adversary_budget=adv["budget"], counterexample_found=adv["counterexample_found"],
                                   best_margin=adv["best_margin"], note=res.note))
    parents = [xl.source_prov(ctx, "S1")]
    prov = xl.derived_prov(ctx, parents, EvidenceClass.PROJECTED, "conclusion_set", "factorial+LHS+adversarial evaluation over Theta_E and Theta_S (never pooled)", "iris.fusion.admissible_set")
    ctx.save_table(pd.DataFrame(class_rows), "conclusion_classes", [prov])
    ctx.save_table(pd.concat(point_frames, ignore_index=True).astype({c: str for c in ["f", "h", "eta", "isf", "s", "m", "st", "r_PB", "R_B", "d", "q"]}), "theta_evaluations", [prov])
    ctx.save_table(pd.DataFrame(adv_rows), "adversarial_search", [prov])
    ctx.save_table(pd.DataFrame(cov_rows), "design_coverage", [prov])
