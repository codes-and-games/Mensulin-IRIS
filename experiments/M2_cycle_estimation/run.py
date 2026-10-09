"""M2: cycle estimation with a mixed-effects harmonic model and a placebo-cycle permutation control. REQUIRES real cycle labels; datasets without them cannot
support any cycle claim (BLOCKED). Estimator validation only: no menstrual-cycle biology is inferred from unlabelled data."""
import numpy as np
import pandas as pd

from iris.common.exceptions import ScientificBlocker
from iris.common.provenance import EvidenceClass
from iris.estimator.hierarchical import fit_harmonic_mixed
from iris.estimator.targets import t1_relative_tdd
from iris.features.person_day import finalize_person_day
from iris.tools import experiment_lib as xl


def run(ctx):
    raw, prov = xl.load_person_day(ctx, with_cycle_labels=True)
    pdf = finalize_person_day(raw.drop(columns=[c for c in ["isf_clinician"] if c in raw]))
    pdf["y"] = t1_relative_tdd(pdf)
    d = pdf.dropna(subset=["y", "cycle_pos"])
    if d.empty:
        raise ScientificBlocker("cycle_labels", "dataset has no cycle labels", "use a dataset with cycle information (or none: no cycle claim is made)")
    res, amp = fit_harmonic_mixed(d, "y", "person_id", "cycle_pos", K=1)
    rng = ctx.rng.generator("M2_placebo")
    placebo = []
    for _ in range(int(ctx.cfg["n_placebo"])):
        dd = d.copy()
        shift = {p: rng.uniform(0, 1) for p in dd["person_id"].unique()}
        dd["cycle_pos"] = (dd["cycle_pos"] + dd["person_id"].map(shift)) % 1.0      # placebo: random per-person cycle offsets
        placebo.append(fit_harmonic_mixed(dd, "y", "person_id", "cycle_pos", K=1)[1]["A1"])
    pval = float((np.sum(np.array(placebo) >= amp["A1"]) + 1) / (len(placebo) + 1))
    out = pd.DataFrame([dict(amplitude=amp["A1"], placebo_mean=float(np.mean(placebo)), placebo_p95=float(np.percentile(placebo, 95)), perm_p_value=pval, n_persons=d.person_id.nunique())])
    ctx.save_table(out, "cycle_amplitude", [xl.derived_prov(ctx, prov[:1], EvidenceClass.COMPUTED, "cycle_amplitude", "mixed harmonic + placebo-cycle control", "iris.estimator.hierarchical")])
