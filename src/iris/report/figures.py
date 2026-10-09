"""Figures are code outputs, drawn from stored run tables only (no scientific model is recomputed here).
Each PNG gets a JSON sidecar {caption, evidence class, run_id, source ids, uncertainty} and an on-image footer."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from iris.common.io import read_sidecar_meta
from . import captions as cp
from .tables import load_run_table


def _finish(fig, run_dir: Path, name: str, title: str, desc: str, prov, uncertainty: str, experiment: str, publication: bool = False) -> Path:
    meta = json.loads((run_dir / "provenance.json").read_text())["run"]
    fp = cp.from_records(prov, run_dir.name, meta["run_mode"], uncertainty, experiment)
    cap = cp.make_caption(title, desc, fp, publication)         # raises if provenance missing / wording violates claims lint
    footer = f"{', '.join(fp.evidence_classes)} | {fp.run_id} | {meta['run_mode'].upper()}"
    fig.text(0.01, 0.005, footer, fontsize=6, color="gray")
    out = run_dir / "figures" / f"{name}.png"
    out.parent.mkdir(exist_ok=True)
    fig.savefig(out, dpi=140, bbox_inches="tight"); plt.close(fig)
    out.with_suffix(".json").write_text(json.dumps(dict(caption=cap, evidence_classes=fp.evidence_classes, run_id=fp.run_id, source_ids=fp.source_ids,
                                                         uncertainty=fp.uncertainty, run_mode=fp.run_mode), indent=2))
    return out


def exceedance_curves(run_dir, scenario_filter=None, phase="high_pop", case="A") -> Path:
    run_dir = Path(run_dir)
    s, prov, _ = load_run_table(run_dir, "fusion_summary")
    d = s[(s.metric == "exceed_units") & (s.phase == phase) & (s.dosing_case == case)]
    fig, ax = plt.subplots(figsize=(6, 4))
    for sc, g in d.groupby("scenario_id"):
        if scenario_filter and sc not in scenario_filter:
            continue
        g = g.sort_values("threshold")
        ax.plot(g.threshold, g["median"], marker="o", label=sc); ax.fill_between(g.threshold, g["lo"], g["hi"], alpha=0.2)
    ax.set_xlabel("threshold tau (U)"); ax.set_ylabel("Pr(unit shortfall > tau) [model-projected]"); ax.legend(fontsize=6)
    return _finish(fig, run_dir, "exceedance_curves", "Exceedance probability of modelled unit shortfall",
                   f"Median across epistemic draws with 95% interval; phase {phase}, dosing case {case}. The model projects these values under the declared assumptions.",
                   prov, "epistemic 2.5-97.5% interval across potency draws; Monte Carlo SE tabulated in fusion_summary", run_dir.name.split("_")[-1])


def conclusion_map(run_dir) -> Path:
    run_dir = Path(run_dir)
    c, prov, _ = load_run_table(run_dir, "conclusion_classes")
    fig, ax = plt.subplots(figsize=(7, 0.6 * len(c) + 1.5))
    colour = {"computationally_robust": "#2e7d32", "conditional": "#f9a825", "unsupported": "#c62828"}
    for i, r in enumerate(c.itertuples()):
        ax.barh(i, r.n_hold / max(r.n_points, 1), color=colour.get(r.classification, "gray"))
        ax.text(0.01, i, f"{r.conclusion} [{r.analysis_set}] {r.classification}; cex={r.counterexample_found}; budget={r.adversary_budget}", va="center", fontsize=6)
    ax.set_yticks([]); ax.set_xlabel("fraction of evaluated points where the conclusion holds"); ax.set_xlim(0, 1)
    return _finish(fig, run_dir, "conclusion_map", "Conclusion-set classification over Theta_E and Theta_S (reported separately)",
                   "Computational robustness is conditional on the declared search design and budget, not proof.", prov, "grid/LHS coverage and adversarial budget in design_coverage", "F5")


def sweep_plot(run_dir) -> Path:
    run_dir = Path(run_dir)
    s, prov, _ = load_run_table(run_dir, "sweeps")
    axes = [a for a in ("r_PB", "st") if a in set(s.axis)]
    fig, ax = plt.subplots(1, len(axes), figsize=(5 * len(axes), 3.5), squeeze=False)
    for k, a in enumerate(axes):
        for cid, g in s[s.axis == a].groupby("conclusion"):
            g = g.copy(); g["x"] = g.axis_value.astype(float); g = g.sort_values("x")
            ax[0][k].plot(g.x, g.margin, marker="o", label=cid)
        ax[0][k].axhline(0, color="k", lw=0.5); ax[0][k].set_xlabel(a); ax[0][k].set_ylabel("conclusion margin (>0 holds)"); ax[0][k].legend(fontsize=6)
    return _finish(fig, run_dir, "dependence_sweeps", "Conclusion margin versus exposure-biology dependence and transfer discrepancy",
                   "Sign changes mark flip points; a flip near zero dependence indicates conditionality on independence.", prov, "single reference theta; Monte Carlo SE not shown", "F6")


def tornado_plot(run_dir) -> Path:
    run_dir = Path(run_dir)
    t, prov, _ = load_run_table(run_dir, "tornado")
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.barh(t.parameter, t.swing); ax.set_xlabel("swing in Pr(shortfall > tau) over the declared range")
    return _finish(fig, run_dir, "tornado", "One-at-a-time sensitivity of the modelled tail probability",
                   "Computed from the stored evaluations; ranges are the declared stress/evidence ranges.", prov, "one-at-a-time; no interaction effects", "R1")


def recovery_plot(run_dir) -> Path:
    run_dir = Path(run_dir)
    s, prov, _ = load_run_table(run_dir, "recovery_summary")
    d = s[s.label == "correct_model"]
    fig, ax = plt.subplots(figsize=(5, 3.5))
    for lc, g in d.groupby("Lc"):
        ax.plot(g.A, g.detect_rate, marker="o", label=f"Lc={lc}")
    ax.set_xlabel("injected amplitude A"); ax.set_ylabel("detection rate"); ax.legend(fontsize=6)
    return _finish(fig, run_dir, "recovery_detection", "Estimator detection rate versus injected amplitude",
                   "Detection at A = 0 is the false-detection rate; results are in simulation only.", prov, "finite replicates per cell; see recovery_trials", "S1")


FIGURE_FUNCS = {"fusion_summary": exceedance_curves, "conclusion_classes": conclusion_map, "sweeps": sweep_plot, "tornado": tornado_plot, "recovery_summary": recovery_plot}
