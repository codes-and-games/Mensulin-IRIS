"""F1: central two-level Monte Carlo (PROJECTED). Consumes stored virtual_population + potency_draws; never recomputes kinetics.
Controls C1 (P=1 => zero Case-A shortfall) and C2 (S=rho=1 => no phase differences) are executed and recorded; a failed
control marks the run FAILED_CONTROL (the results table is still written so the failure is preserved)."""
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", message="All-NaN slice")   # HP undefined where both tails are zero: kept as NaN, flagged by den_zero_share

from iris.common.exceptions import ScientificBlocker
from iris.common.provenance import EvidenceClass
from iris.common.schemas import FUSION_OUT
from iris.fusion import controls
from iris.fusion import endpoints as ep
from iris.fusion.mc_engine import FusionConfig, population_arrays, run_fusion, summarise_epistemic
from iris.thermal.potency_draws import full_key
from iris.tools import experiment_lib as xl


def run(ctx):
    cfg = ctx.cfg
    h = float(cfg["population"]["h"])
    pop, ppop = xl.load_population(ctx, h)
    pot, ppot = xl.load_potency(ctx)
    arr = population_arrays(pop)
    thr = xl.cfg_yaml(ctx, "configs/fusion/thresholds.yaml")
    J = int(cfg["fusion"]["J"]); st = float(cfg["fusion"]["transfer_sd"]); dur = cfg["fusion"]["duration_d"]
    parents = ppop[:1] + ppot[:1]
    all_out, ctrl_rows, ep_rows, env_rows = [], [], [], []
    for sid in cfg["thermal"]["scenarios"]:
        key = full_key(sid, dur, st)
        if (pot["scenario_id"] == key).sum() == 0:
            ctx.blockers.append(dict(part=key, reason="no stored potency draws (scenario blocked upstream)")); continue
        fc = xl.fusion_cfg_from(ctx, key, J=J, mode=cfg["fusion"].get("mode", "shared"), r_pb=float(cfg["fusion"].get("r_pb", 0.0)))
        out = run_fusion(pop, pot, fc, ctx.rng)
        all_out.append(out)
        pool = 1.0 - pot[pot.scenario_id == key].sort_values("epistemic_draw_j")["potency"].to_numpy()
        # --- controls
        c1 = run_fusion(pop, pot.assign(potency=np.where(pot.scenario_id == key, 1.0, pot.potency)), FusionConfig(**{**fc.__dict__, "J": 3, "include_concentration": False}), ctx.rng, phases=("high_pop",))
        c1_ok = bool((c1[c1.metric.isin(["exceed_units", "exceed_pct_tdd", "mean_positive_part_u"]) & (c1.dosing_case == "A")]["value"] == 0.0).all())
        S1, R1 = controls.control_c2_no_cycle(arr["S"], arr["rho"]); c2_ok = bool(np.allclose(R1[:, 4], R1[:, 0]) and np.allclose(S1[:, 4], S1[:, 0]))
        ctrl_rows += [dict(scenario=key, control="C1_no_loss_gives_zero_shortfall", passed=c1_ok), dict(scenario=key, control="C2_no_cycle_removes_phase_difference", passed=c2_ok)]
        # --- primary endpoints
        rng = ctx.rng.generator("F1_endpoints", key)
        v = ep.p1_variance_decomposition(arr, pool, 4, rng); v.update(scenario=key, endpoint="P1_variance_decomposition"); ep_rows.append(v)
        hp = ep.p2_heterogeneity_penalty(arr, pool, 4, thr["units"], J=J); hp["scenario"] = key; ep_rows.append(None) if False else None
        hp_s = hp.groupby("threshold").agg(hp_median=("hp", lambda x: np.nanmedian(np.where(np.isinf(x), np.nan, x))), hp_inf_share=("hp", lambda x: float(np.isinf(x).mean())),
                                          p_het=("p_het", "median"), p_mean=("p_mean", "median"), den_zero_share=("denominator_zero", "mean")).reset_index(); hp_s["scenario"] = key
        env = ep.product_tail_envelope(arr, pool, 4, thr["units"], rng=rng); env["scenario"] = key; env_rows.append(env)
        ep_rows.append(dict(scenario=key, endpoint="P2_heterogeneity_penalty_table", table=hp_s.to_dict("records")))
        ph = xl.phi_ratio(arr); ph.update(scenario=key, endpoint="phi_and_rho_ratio"); ep_rows.append(ph)
    if not all_out:
        raise ScientificBlocker("potency_draws", "no scenario had stored potency draws", "run E4 with extracted kinetics")
    out = pd.concat(all_out, ignore_index=True)
    prov = xl.derived_prov(ctx, parents, EvidenceClass.PROJECTED, "fusion_out", "two-level Monte Carlo over stored population and potency draws", "iris.fusion.mc_engine")
    ctx.save_table(out, "fusion_out", [prov], schema=FUSION_OUT)
    ctx.save_table(summarise_epistemic(out), "fusion_summary", [prov])
    ctrl = pd.DataFrame(ctrl_rows); ctx.save_table(ctrl, "controls", [prov])
    ctx.save_table(pd.DataFrame([{k: (str(v) if isinstance(v, list) else v) for k, v in r.items()} for r in ep_rows if r]), "primary_endpoints", [prov])
    if env_rows:
        ctx.save_table(pd.concat(env_rows, ignore_index=True), "product_tail_envelope", [prov])
    if not ctrl["passed"].all():
        ctx.log.warn("FAILED_CONTROL: " + ", ".join(ctrl.loc[~ctrl.passed, "control"].astype(str)))
