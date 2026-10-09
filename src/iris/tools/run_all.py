"""python -m iris.tools.run_all --mode {test,provisional,production} [--smoke] [--only ID,ID] [--out results/status_<mode>.md]
Runs every experiment in dependency order, never stops on BLOCKED, and writes a status table. A COMPLETED code run is NOT a
scientific validation: the table separates `pipeline_status` from `evidence_status` (see docs/runbook/05_production_runbook.md)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from iris.common.runs import RunExistsError
from iris.tools.run_experiment import ROOT, run_experiment

# dependency order (upstream first). Verified against experiments/*/run.py inputs (load_derived / load_person_day / load_events).
ORDER = ["L3_biological_evidence", "L5_thermal_context", "L2_degradation", "L1_novelty", "E3_vial_lag", "E1_climate_agreement",
         "E2_reconstruction_context", "S2_thermal_kinetics", "E4_exposure_generation", "S3_virtual_population",
         "F1_central", "F2_tail", "F3_compounding", "F4_ablation", "F6_dependence_transport", "F5_admissible_set",
         "R1_sensitivity", "R2_definition_robustness", "R3_structural_robustness",
         "S1_estimator_ground_truth", "M4_leakage", "M1_baseline", "M6_circadian_recovery", "M2_cycle_estimation", "M3_generalisation",
         "L4_isf_tdd", "M5_empirical_isf_tdd"]
#: experiments whose outputs are verification of code on synthetic truth, never evidence about the world
VERIFICATION_ONLY = {"E3_vial_lag", "S1_estimator_ground_truth", "S2_thermal_kinetics", "M4_leakage"}


def evidence_status(exp: str, mode: str, status: str, smoke: bool) -> str:
    if status != "completed":
        return "none (blocked/failed)"
    if mode == "test" or smoke:
        return "none (TEST/smoke: plumbing only)"
    if exp in VERIFICATION_ONLY:
        return "verification of code/controls (not evidence about the world)"
    return "PROVISIONAL" if mode == "provisional" else "PRODUCTION (still requires the validation checklist)"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["test", "provisional", "production"])
    ap.add_argument("--smoke", action="store_true"); ap.add_argument("--only", default=""); ap.add_argument("--out")
    a = ap.parse_args(argv)
    want = [e for e in a.only.split(",") if e] or ORDER
    rows = []
    for e in want:
        try:
            ctx = run_experiment(e, a.mode, smoke=a.smoke)
            meta = json.loads((ctx.dir / "provenance.json").read_text())["run"]
            st, why = meta["status"], (meta.get("blocker", {}) or {}).get("needed", "") or "; ".join(b["reason"][:80] for b in meta.get("partial_blockers", []))
            rows.append((e, st, evidence_status(e, a.mode, st, a.smoke), ctx.run_id, why))
        except RunExistsError:
            rows.append((e, "exists", "unchanged: a completed run with this exact config exists today", "-", "if INPUT DATA changed since, delete that run folder under results/runs/ and re-run (run ids hash the config, not the data)"))
        except Exception as exc:                       # noqa: BLE001 - report and continue
            rows.append((e, "failed", "none (blocked/failed)", "-", repr(exc)[:160]))
    out = Path(a.out) if a.out else ROOT / f"results/status_{a.mode}{'_smoke' if a.smoke else ''}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# Run status ({a.mode}{', smoke' if a.smoke else ''})", "", "| experiment | pipeline_status | evidence_status | run_id | what unblocks it / note |", "| --- | --- | --- | --- | --- |"]
    lines += [f"| {e} | {s} | {ev} | {rid} | {why} |" for e, s, ev, rid, why in rows]
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines)); print(f"\nwritten {out}")
    return 0 if all(r[1] in ("completed", "blocked", "exists") for r in rows) else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
