"""L2: degradation-literature extraction -> K1 fits -> LOSO evaluation -> kinetic model set. Reads literature/degradation_literature.csv (production: verified rows only).
Empty => BLOCKED. Test mode uses the TEST_ONLY kinetics fixture. Unlike products are never pooled; non-identifiable studies are reported as such."""
import pandas as pd

from iris.common.parameters import RunMode
from iris.common.provenance import EvidenceClass
from iris.thermal.kinetics.fitting import loso_k1
from iris.thermal.literature import load_literature
from iris.tools import experiment_lib as xl


def run(ctx):
    if ctx.mode is RunMode.TEST:
        df = load_literature(xl.repo(ctx) / "tests/data/synthetic_kinetics.csv", RunMode.TEST)
    else:
        df = load_literature(xl.repo(ctx) / "literature/degradation_literature.csv", ctx.mode)
    ms, diag, src = xl.model_set_for(ctx)
    base = xl.derived_prov(ctx, src, EvidenceClass.COMPUTED, "kinetic_fits", "per-study K1 posterior fits", "iris.thermal.kinetics.fitting")
    ctx.save_table(diag, "fit_diagnostics", [base])
    obs = df.rename(columns={"study_id": "study"})
    loso = loso_k1(obs, ctx.rng.child("L2_loso"))
    ctx.save_table(loso, "loso_predictions", [base])
    ctx.save_table(loso.groupby("held_out").agg(mae=("abs_err", "mean"), coverage95=("covered", "mean"), n=("observed", "count")).reset_index(), "loso_summary", [base])
    ctx.save_table(pd.DataFrame([dict(study=s.study, model=s.model_id, weight=w, n_draws=s.n_draws) for s, w in zip(ms.specs, ms.weights())]), "ensemble_weights", [base])
    if not ms.between_study_variance_estimable:
        ctx.log.warn("fewer than 5 comparable studies: between-study variance NOT estimable; the model set is an analyst-defined plausible set, not a quantified distribution")
