"""S3: virtual-population checks against declared published moments; BLOCKED where targets are unresolved (never PASS)."""
import pandas as pd

from iris.common.provenance import EvidenceClass
from iris.common.schemas import VIRTUAL_POPULATION
from iris.population.checks import dependence_diagnostics, run_checks
from iris.tools import experiment_lib as xl


def run(ctx):
    pcfg = xl.cfg_yaml(ctx, "configs/population/population_default.yaml")
    anchors = pcfg["phase_sensitivity_anchor"]
    targets = dict(tdd_mean=pcfg["tdd"]["mean_u"], tdd_sd=pcfg["tdd"]["sd_u"], cycle_mean=pcfg["cycle"]["mean_d"], cycle_sd=pcfg["cycle"]["sd_d"],
                   concordance=pcfg["concordance_with_population_direction"]["value"],
                   sens_ef=1 + anchors["early_follicular"]["value"], sens_ml=1 + anchors["midluteal"]["value"])
    allres = []
    for h in ctx.cfg["heterogeneity_levels"]:
        df, spec = xl.population_for(ctx, eta=ctx.cfg["eta_reference"], h=h, n=ctx.cfg["population"]["n"])
        res = run_checks(df, {**targets, 'concordance_applies': bool(abs(h - 1.0) < 1e-12)}); res.insert(0, "heterogeneity_multiplier", h)
        res["stress_components"] = "; ".join(spec.stress_components)
        allres.append(res)
        prov = xl.population_prov(ctx, spec)
        p = ctx.save_table(df, f"virtual_population_h{h}", [prov], schema=VIRTUAL_POPULATION)
        xl.publish_derived(ctx, p, f"virtual_population_h{h}")
        dd = dependence_diagnostics(df); ctx.log.info(f"dependence diagnostics h={h}: {dd}")
    out = pd.concat(allres, ignore_index=True)
    ctx.save_table(out, "population_checks", [xl.derived_prov(ctx, [xl.source_prov(ctx, "S1")], EvidenceClass.COMPUTED, "population_checks", "moment checks vs published anchors", "iris.population.checks")])
    if (out.status == "FAIL").any():
        ctx.log.warn("S3 FAIL: " + ", ".join(out.loc[out.status == "FAIL", "check"].unique()))
    if (out.status == "BLOCKED").any():
        ctx.blockers.append(dict(part="S3", reason="targets unresolved: " + ", ".join(out.loc[out.status == "BLOCKED", "check"].unique())))
