"""Orchestration helpers shared by experiments/*/run.py (the only module that wires several layers together).

Mode semantics (run_mode):
  production  : only RESOLVED parameters, verified registry sources, verified literature rows; never TEST_ONLY.
  provisional : PENDING_VERIFY anchors and declared ASSUMPTION/STRESS completions allowed; every output stamped.
  test        : TEST_ONLY synthetic fixtures allowed; outputs are never publishable.
Anything unresolved raises ScientificBlocker: the experiment is recorded as 'blocked', never filled with defaults.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from iris.common.exceptions import ScientificBlocker, TestOnlyDataError
from iris.common.io import load_yaml, read_sidecar_meta, read_table, sidecar_path, write_table
from iris.common.parameters import Parameter, RunMode, Status
from iris.common.provenance import EvidenceClass, Provenance
from iris.common.registry import SourceRegistry
from iris.common.rng import RngTree
from iris.common.runs import RunContext
from iris.common.schemas import FUSION_OUT, POTENCY_DRAWS, VIRTUAL_POPULATION

TEST_COMPLETION_DEFAULT = {"profile_completion": "two_anchor_cosine", "concordance_sd": "sd_from_concordance_normal"}


def repo(ctx: RunContext) -> Path:
    return Path(ctx.cfg["_repo_root"])


def cfg_yaml(ctx: RunContext, rel: str) -> dict:
    return load_yaml(repo(ctx) / rel)


def registry(ctx: RunContext) -> SourceRegistry:
    r = repo(ctx)
    return SourceRegistry.load(r / ctx.cfg["paths"]["registry"], r / ctx.cfg["paths"]["manifest"])


def source_prov(ctx: RunContext, source_id: str, transformation: str = "") -> Provenance:
    """Provenance for an external source, gated by run mode."""
    if ctx.mode is RunMode.TEST or source_id.startswith("TEST_ONLY:"):
        if ctx.mode is not RunMode.TEST:
            raise TestOnlyDataError(f"{source_id} cannot enter a {ctx.mode.value} run")
        sid = source_id if source_id.startswith("TEST_ONLY:") else f"TEST_ONLY:{source_id}"
        return Provenance(EvidenceClass.PUBLISHED, sid, synthetic=True, transformation=transformation, run_id=ctx.run_id)
    row = registry(ctx).require(source_id, allow_unverified=(ctx.mode is RunMode.PROVISIONAL))
    return row.to_provenance(transformation=transformation, run_id=ctx.run_id)


def derived_prov(ctx: RunContext, parents: list[Provenance], cls: EvidenceClass, source_id: str, transformation: str, generated_by: str) -> Provenance:
    base = parents[0]
    p = base.derive(evidence_class=cls, source_id=source_id, transformation=transformation, generated_by=generated_by,
                    run_id=ctx.run_id, extra_parents=tuple(x.source_id for x in parents[1:]))
    return p


def stamp(ctx: RunContext) -> str:
    return {"production": "PRODUCTION", "provisional": "PROVISIONAL (inputs not fully verified)", "test": "TEST-ONLY (synthetic fixtures)"}[ctx.mode.value]


# --------------------------------------------------------------------------- thermal inputs
def tau_range_min(ctx: RunContext, key: str = "C1_still_indoor_air") -> tuple[float, float]:
    d = cfg_yaml(ctx, "configs/thermal/lag.yaml")["contexts"][key]
    st = Status(d["status"]) if d.get("status") in Status.__members__ else Status.UNRESOLVED
    v = d.get("tau_min_range")
    val = tuple(v) if v else None
    return Parameter(f"tau_range:{key}", val, "min", st, note="compute from registered handbook values (S35)").get(
        RunMode.TEST if ctx.mode is RunMode.TEST else ctx.mode)


def model_set_for(ctx: RunContext):
    """Kinetic model set from the literature table (or the TEST_ONLY fixture in test mode)."""
    from iris.thermal.literature import build_model_set, load_literature
    if ctx.mode is RunMode.TEST:
        df = load_literature(repo(ctx) / "tests/data/synthetic_kinetics.csv", RunMode.TEST)
        nulls = ["TEST_ONLY:N"]
    else:
        df = load_literature(repo(ctx) / "literature/degradation_literature.csv", ctx.mode)
        nulls = list(cfg_yaml(ctx, "configs/thermal/kinetics_k0.yaml").get("studies") or [])
    ms, diag = build_model_set(df, ctx.rng.child("kinetics"), nulls)
    src = [source_prov(ctx, s) for s in sorted(set(df["source_id"].astype(str)))]
    return ms, diag, src


# --------------------------------------------------------------------------- population inputs
def population_for(ctx: RunContext, *, eta: float, h: float, family: str = "normal", family_opts: dict | None = None,
                   dependence=None, n: int | None = None, label: str | None = None, completion: dict | None = None,
                   rng_name: str = "population"):
    from iris.population.generator import build_spec_from_config, generate
    pcfg = cfg_yaml(ctx, "configs/population/population_default.yaml")
    comp = completion if completion is not None else dict(ctx.cfg.get("population_completion", {}))
    spec = build_spec_from_config(pcfg, ctx.mode, eta=eta, h_multiplier=h, family=family, family_opts=family_opts,
                                  dependence=dependence, n=n or ctx.cfg.get("population", {}).get("n"), completion=comp,
                                  label=label or f"h{h}")
    df = generate(spec, ctx.rng.child(rng_name, f"h{h}", f"eta{eta}", family))
    return df, spec


def population_prov(ctx: RunContext, spec) -> Provenance:
    parent = source_prov(ctx, "S1", "anchor moments (TDD, cycle length, phase contrast)")
    return parent.derive(evidence_class=EvidenceClass.SIMULATED, source_id=f"virtual_population:{spec.heterogeneity_label}",
                         transformation="virtual population generator; stress components: " + "; ".join(spec.stress_components or ["none"]),
                         generated_by="iris.population.generator", run_id=ctx.run_id)


# --------------------------------------------------------------------------- derived hand-off between layers
def publish_derived(ctx: RunContext, run_table: Path, name: str) -> Path:
    """Copy a stored run table (+ provenance sidecar + run mode) to data/derived/ for downstream layers."""
    dst = repo(ctx) / ctx.cfg["paths"]["derived"] / f"{name}.parquet"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(run_table, dst)
    sc = sidecar_path(run_table)
    import json
    meta = json.loads(sc.read_text())
    meta.setdefault("run", {})["run_mode"] = ctx.mode.value
    meta["run"]["source_run_id"] = ctx.run_id
    sidecar_path(dst).write_text(json.dumps(meta, indent=2, sort_keys=True))
    return dst


def load_derived(ctx: RunContext, name: str, schema=None):
    """Load a derived table, verifying hash, provenance, and that the producing run's mode is compatible."""
    p = repo(ctx) / ctx.cfg["paths"]["derived"] / f"{name}.parquet"
    if not p.exists():
        raise ScientificBlocker(name, f"{p.name} not found in data/derived", f"run the upstream experiment that produces {name}")
    df, prov = read_table(p, schema)
    meta = read_sidecar_meta(p)
    produced_mode = meta.get("run_mode", "unknown")
    order = {"test": 0, "provisional": 1, "production": 2}
    if order.get(produced_mode, -1) < order[ctx.mode.value]:
        raise ScientificBlocker(name, f"derived table produced in '{produced_mode}' mode cannot feed a '{ctx.mode.value}' run",
                                "regenerate the upstream layer in the same (or stricter) mode")
    if ctx.mode is not RunMode.TEST and any(x.synthetic for x in prov):
        raise TestOnlyDataError(f"{name} carries TEST_ONLY lineage")
    return df, prov


def fusion_cfg_from(ctx: RunContext, scenario_key: str, *, J: int, mode: str = "shared", r_pb: float = 0.0, run_id: str | None = None,
                    cases=None, isf_model="K_over_tdd_times_S", include_glucose=True):
    from iris.fusion.mc_engine import FusionConfig
    thr = cfg_yaml(ctx, "configs/fusion/thresholds.yaml")
    fz = ctx.cfg.get("fusion", {})
    return FusionConfig(run_id=run_id or ctx.run_id, scenario_id=scenario_key, J=J, dosing_cases=tuple(cases or fz.get("dosing_cases", ["A", "B"])),
                        isf_model=isf_model, isf_const=tuple(float(k) for k in fz.get("isf_const", [1500, 1700, 1800])),
                        thr_units=tuple(thr["units"]), thr_pct_tdd=tuple(thr["pct_tdd"]), thr_glucose=tuple(thr["glucose_mgdl"]),
                        mode=mode, r_pb=r_pb, tci_top_fraction=float(thr.get("tci_top_fraction", 0.2)), include_glucose=include_glucose)


def scenario_ids(ctx: RunContext) -> list[str]:
    return [s for s in ctx.cfg.get("thermal", {}).get("scenarios", [])]


# --------------------------------------------------------------------------- fusion-side helpers
def load_population(ctx: RunContext, h: float):
    df, prov = load_derived(ctx, f"virtual_population_h{h}", VIRTUAL_POPULATION)
    return df, prov


def load_potency(ctx: RunContext):
    df, prov = load_derived(ctx, "potency_draws", None)
    from iris.common.schemas import validate_potency_draws
    validate_potency_draws(df)
    return df, prov


def parse_dependence(name: str, aset_spec: dict):
    from iris.population.dependence import BiologicalDependence
    s = float(aset_spec["R_B"].get("strength", 0.5))
    table = {"independent": None, "tdd_sigma_pos": {("tdd", "sens"): s}, "tdd_sigma_neg": {("tdd", "sens"): -s},
             "s_gamma_pos": {("sens", "gamma"): s}, "s_gamma_neg": {("sens", "gamma"): -s}}
    if name not in table:
        raise ScientificBlocker("R_B", f"unknown dependence level {name}")
    return BiologicalDependence.independent() if table[name] is None else BiologicalDependence.from_pairs(table[name], "STRESS_TEST", name)


def make_population_fn(ctx: RunContext, aset_spec: dict, n_eval: int):
    """theta dict -> virtual population for the evaluator (provisional/test completions come from the config)."""
    opts = {"mixture_shift_sd": aset_spec["f"].get("mixture_shift_sd")} if aset_spec["f"].get("mixture_shift_sd") is not None else {}

    def fn(th: dict):
        df, _ = population_for(ctx, eta=float(th["eta"]), h=round(float(th["h"]), 4), family=th["f"], family_opts=opts,
                               dependence=parse_dependence(th["R_B"], aset_spec), n=n_eval, label=f"h{th['h']}",
                               rng_name=f"popfn_{th['f']}_{th['R_B']}")
        return df
    return fn


def evaluator_for(ctx: RunContext, thresholds, n_eval: int):
    from iris.fusion.theta_eval import ThetaEvaluator
    aset = cfg_yaml(ctx, "configs/fusion/admissible_set.yaml")["components"]
    pot, _ = load_potency(ctx)
    return ThetaEvaluator(make_population_fn(ctx, aset, n_eval), pot, float(ctx.cfg["fusion"]["duration_d"]), tuple(thresholds),
                          ctx.rng.child("theta"), n_eval=n_eval), aset


def phi_ratio(arr: dict, high: int = 4, low: int = 0) -> dict:
    """phi = (R_high S_high)/(R_low S_low) = G_high/G_low (document 15.x); rho_ratio = rho_high / rho_low (population ratios of means)."""
    gh, gl = arr["R"][:, high] * arr["S"][:, high], arr["R"][:, low] * arr["S"][:, low]
    return {"phi": float(gh.mean() / gl.mean()), "phi_median_individual": float(np.median(gh / gl)),
            "rho_ratio": float(arr["rho"][:, high].mean() / arr["rho"][:, low].mean()),
            "R_ratio_weighted": float((arr["tdd"] * arr["rho"][:, high]).mean() / (arr["tdd"] * arr["rho"][:, low]).mean())}


def load_person_day(ctx: RunContext, with_cycle_labels: bool = True):
    """Person-day table: TEST_ONLY synthetic in test mode; otherwise a registered, provenance-carrying processed table or BLOCKED."""
    from iris.tools.synthetic import synthetic_person_day
    from iris.common.schemas import PERSON_DAY
    if ctx.mode is RunMode.TEST:
        df = synthetic_person_day(ctx.rng.generator("synthetic_person_day"), with_cycle_labels=with_cycle_labels,
                                  n_persons=int(ctx.cfg.get("synthetic", {}).get("n_persons", 24)))
        return df, [Provenance(EvidenceClass.SIMULATED, "TEST_ONLY:synthetic_person_day", synthetic=True, generated_by="iris.tools.synthetic", run_id=ctx.run_id)]
    p = repo(ctx) / "data/processed/person_day.parquet"
    if not p.exists():
        raise ScientificBlocker("person_day", "no processed person-day table", "obtain a registered public dataset, audit it (make audit), write configs/mappings/<dataset>.yaml, then ingest")
    df, prov = read_table(p)
    PERSON_DAY.validate(df[[c.name for c in PERSON_DAY.columns]])
    made = read_sidecar_meta(p).get("run_mode", "unknown")
    order = {"test": 0, "provisional": 1, "production": 2}
    if order.get(made, -1) < order[ctx.mode.value]:
        raise ScientificBlocker("person_day", f"person_day.parquet was ingested in '{made}' mode and cannot feed a '{ctx.mode.value}' run",
                                "re-ingest with --mode production after the dataset source is verified and its files are in data/manifest.csv")
    if any(x.synthetic for x in prov):
        raise TestOnlyDataError("person_day carries TEST_ONLY lineage")
    return df, prov


def load_events(ctx: RunContext, dataset: str):
    """5-min event grid for one ingested dataset (data/processed/<dataset>/events_grid.parquet): TEST_ONLY synthetic in test mode;
    otherwise a provenance-carrying table produced in the same or a stricter run mode, or BLOCKED."""
    from iris.tools.synthetic import synthetic_events_grid
    if ctx.mode is RunMode.TEST:
        c = ctx.cfg.get("synthetic", {})
        df = synthetic_events_grid(ctx.rng.generator("synthetic_events", dataset), n_persons=int(c.get("n_persons", 8)),
                                   n_days=int(c.get("n_days", 14)), circadian_amp=float(c.get("circadian_amp", 0.2)))
        return df, [Provenance(EvidenceClass.SIMULATED, "TEST_ONLY:synthetic_events", synthetic=True, generated_by="iris.tools.synthetic", run_id=ctx.run_id)]
    p = repo(ctx) / "data/processed" / dataset / "events_grid.parquet"
    if not p.exists():
        raise ScientificBlocker(f"events_grid:{dataset}", f"{p} not found", f"download {dataset}, audit, write the mapping, then `python -m iris.tools.ingest_dataset {dataset}`")
    df, prov = read_table(p)
    made = read_sidecar_meta(p).get("run_mode", "unknown")
    order = {"test": 0, "provisional": 1, "production": 2}
    if order.get(made, -1) < order[ctx.mode.value]:
        raise ScientificBlocker(f"events_grid:{dataset}", f"ingested in '{made}' mode; cannot feed a '{ctx.mode.value}' run", "re-ingest with --mode production after source verification and manifest registration")
    if any(x.synthetic for x in prov):
        raise TestOnlyDataError(f"events_grid:{dataset} carries TEST_ONLY lineage")
    want = ctx.cfg.get("grid_minutes")
    if want is not None and len(df):
        step = (df.sort_values(["person_id", "ts_local"]).groupby("person_id")["ts_local"].diff().dropna().dt.total_seconds() / 60.0)
        have = float(step.median()) if len(step) else float(want)
        if abs(have - float(want)) > 1e-9:       # a silent grid mismatch would mis-scale coverage and the EKF time step
            raise ScientificBlocker(f"events_grid:{dataset}", f"ingested grid is {have:g} min but this experiment is configured for grid_minutes={want}",
                                    "set grid_minutes in the experiment config to the ingested grid (record the change in docs/decisions/DECISION_LOG.md), or re-ingest with the intended grid")
    return df, prov
