"""E4: scenario temperature histories, exposure summaries and (when kinetics are available) potency draws.

Layer-2 output: exposure summaries + potency_draws + provenance. Parametric scenarios are SIMULATED; scenarios needing
registered inputs (S5, S8) are recorded as blocked, never approximated. Potency draws are blocked (but exposure still
produced) when no extracted kinetics exist.
"""
import numpy as np
import pandas as pd

from iris.common.exceptions import ScientificBlocker
from iris.common.provenance import EvidenceClass, Provenance
from iris.common.schemas import THERMAL_EXPOSURE, POTENCY_DRAWS
from iris.thermal.exposure import exposure_summary, exposure_table, generate_parametric
from iris.thermal.lag import exponential_integrator
from iris.thermal.potency_draws import generate_potency_draws, scenario_key, full_key
from iris.tools import experiment_lib as xl


def run(ctx):
    sc = xl.cfg_yaml(ctx, "configs/fusion/scenarios.yaml")
    scen_ids = ctx.cfg["thermal"]["scenarios"]; durations = ctx.cfg["thermal"]["durations_d"]
    dt_min = float(ctx.cfg["thermal"]["dt_min"]); J = int(ctx.cfg["fusion"]["J"]); st_levels = [float(x) for x in ctx.cfg["thermal"]["transfer_sd_levels"]]
    ea = ctx.cfg["thermal"].get("mkt_ea_j_mol")           # None => MKT reported as NaN (compendial Ea not registered yet)
    try:
        tau_rng = xl.tau_range_min(ctx)
    except ScientificBlocker as e:
        tau_rng = None; ctx.blockers.append(dict(part="vial_lag", parameter=e.parameter, reason=e.reason)); ctx.log.warn(str(e))
    try:
        mset, kdiag, src = xl.model_set_for(ctx)
        ctx.save_table(kdiag, "kinetic_fit_diagnostics", [xl.derived_prov(ctx, src, EvidenceClass.COMPUTED, "kinetic_fits", "K1 posterior fits per study", "iris.thermal.kinetics.fitting")])
    except ScientificBlocker as e:
        mset, src = None, None; ctx.blockers.append(dict(part="potency_draws", parameter=e.parameter, reason=e.reason)); ctx.log.warn(str(e))
    summ, status, expo_frames, pot_frames = [], [], [], []
    base_prov = Provenance(EvidenceClass.SIMULATED, "parametric_scenarios", transformation="configs/fusion/scenarios.yaml",
                           generated_by="iris.thermal.exposure", run_id=ctx.run_id, synthetic=(ctx.mode.value == "test"),
                           parent_source_ids=(("TEST_ONLY:scenario_defs",) if ctx.mode.value == "test" else ()))
    for sid in scen_ids:
        cfg = sc["scenarios"][sid]
        for dur in durations:
            key = scenario_key(sid, dur)
            try:
                air, assumptions = generate_parametric(cfg, dur, dt_min, ctx.rng.generator("history", sid, f"#0"))
            except ScientificBlocker as e:
                status.append(dict(scenario=key, status="blocked", reason=e.needed)); ctx.blockers.append(dict(part=key, parameter=e.parameter, reason=e.reason))
                continue
            row = dict(scenario=key, status="ok", declared_assumptions=",".join(assumptions), evidence_class=cfg["evidence_class"])
            status.append(row)
            sm = exposure_summary(air, dt_min / 60.0, mkt_ea_j_mol=ea)
            sm.update(scenario=key, series="air", ea_for_mkt=ea if ea else np.nan); summ.append(sm)
            if tau_rng:
                tau = float(np.sqrt(tau_rng[0] * tau_rng[1]))      # geometric-mid tau for the stored exposure table
                vial = exponential_integrator(air, dt_min * 60, tau * 60)
                sv = exposure_summary(vial, dt_min / 60.0, mkt_ea_j_mol=ea); sv.update(scenario=key, series="vial", ea_for_mkt=ea if ea else np.nan); summ.append(sv)
                if dur == durations[0]:
                    expo_frames.append(exposure_table(key, ctx.cfg["thermal"].get("context_id", "C1"), "NA", "2026-01-01", dt_min, None, air, vial, tau,
                                                      "parametric", "ok", False, cfg["evidence_class"]))
                if mset is not None:
                    for st in st_levels:          # common random numbers across transfer levels (same delta stream, scaled)
                        pot_frames.append(generate_potency_draws({**cfg, "id": sid}, dur, mset, tau_rng, J, ctx.rng, dt_min=dt_min, transfer_sd=st))
    ctx.save_table(pd.DataFrame(status), "scenario_status", [base_prov])
    if summ:
        ctx.save_table(pd.DataFrame(summ), "exposure_summaries", [base_prov.derive(evidence_class=EvidenceClass.COMPUTED, source_id="exposure_summaries", transformation="hours/degree-hours/MKT", generated_by="iris.thermal.exposure")])
    if expo_frames:
        ctx.save_table(pd.concat(expo_frames, ignore_index=True), "thermal_exposure", [base_prov], schema=THERMAL_EXPOSURE)
    if pot_frames:
        pot = pd.concat(pot_frames, ignore_index=True)
        p = ctx.save_table(pot, "potency_draws", [xl.derived_prov(ctx, [base_prov] + (src or []), EvidenceClass.SIMULATED, "potency_draws", "exposure->lag->kinetics->potency (M draws)", "iris.thermal.potency_draws")], schema=None)
        xl.publish_derived(ctx, p, "potency_draws")
    if not pot_frames:
        ctx.log.warn("no potency draws produced (kinetics or lag input unresolved): downstream fusion will be blocked")
