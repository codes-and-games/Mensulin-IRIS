"""Mapping-driven ingest: raw files -> harmonised 5-min event grid -> person-day table, with provenance and QC.

Rules (documents 8, 17): no guessing; flag, never silently delete; units and timezone must be declared by the mapping;
TDD exists only when insulin is recorded for >= ``min_insulin_coverage`` of the day's grid steps; cycle fields exist only
when the mapping declares dataset-provided labels. Outputs are COMPUTED and carry the run mode they were produced in.
"""
from __future__ import annotations

import fnmatch
from pathlib import Path

import numpy as np
import pandas as pd

from iris.common.exceptions import ScientificBlocker
from iris.common.provenance import EvidenceClass
from iris.common.registry import SourceRegistry
from iris.ingest.audit import _read
from iris.ingest.harmonise import flag_glucose, glucose_to_mgdl, to_utc_with_local
from iris.ingest.mapping import load_mapping
from iris.features.person_day import apply_inclusion, finalize_person_day

EVENT_COLUMNS = ["dataset", "person_id", "ts_local", "date_local", "glucose_mgdl", "glucose_flag", "basal_u", "bolus_u",
                 "insulin_u", "carb_g"]


def _files(root: Path, m: dict) -> list[Path]:
    base = root / m["raw_dir"]
    if not base.exists():
        raise ScientificBlocker("raw_data", f"{base} does not exist", "download the dataset into data/raw/<dataset>/ (see docs/data guides)")
    fs = sorted(p for p in base.glob(m.get("file_glob", "**/*.csv")) if p.is_file())
    if not fs:
        raise ScientificBlocker("raw_data", f"no files match {m.get('file_glob')} under {base}", "check file_glob in the mapping")
    return fs


def _person(path: Path, df: pd.DataFrame, m: dict) -> pd.Series:
    p = m["person_id"]
    if p["from"] == "filename":
        return pd.Series(path.stem, index=df.index)
    if p["from"] == "constant":
        return pd.Series(str(p.get("value", "P1")), index=df.index)
    return df[p["column"]].astype(str)


def _to_grid(df: pd.DataFrame, m: dict, dataset: str, person: pd.Series, log: list[str]) -> pd.DataFrame:
    cols, units, g = m["columns"], m["units"], int(m["grid_minutes"])
    t = to_utc_with_local(df[cols["timestamp"]], m["tz"])
    bad = int(t["dst_ambiguous_flag"].sum())
    if bad:
        log.append(f"{bad} rows dropped: DST-ambiguous/nonexistent local times")
    keep = ~t["dst_ambiguous_flag"].to_numpy()
    wall = t.loc[keep, "ts_local"].dt.tz_localize(None)            # local wall-clock time (circadian analyses need it)
    bin_ = wall.dt.floor(f"{g}min")
    frame = pd.DataFrame({"person_id": person[keep].to_numpy(), "bin": bin_.to_numpy()})
    gl = glucose_to_mgdl(pd.to_numeric(df.loc[keep, cols["glucose"]], errors="coerce"), units["glucose"]).to_numpy()
    frame["glucose_mgdl"] = gl
    if "basal" in cols:
        v = pd.to_numeric(df.loc[keep, cols["basal"]], errors="coerce").to_numpy()
        frame["basal_raw"] = v
    if "bolus" in cols:
        frame["bolus_u"] = pd.to_numeric(df.loc[keep, cols["bolus"]], errors="coerce").to_numpy()
    if "insulin_total" in cols:
        frame["insulin_total_u"] = pd.to_numeric(df.loc[keep, cols["insulin_total"]], errors="coerce").to_numpy()
    if "carb" in cols:
        frame["carb_g"] = pd.to_numeric(df.loc[keep, cols["carb"]], errors="coerce").to_numpy()
    for r in ("isf_clinician", "cycle_day", "cycle_len"):
        if r in cols:
            frame[r] = pd.to_numeric(df.loc[keep, cols[r]], errors="coerce").to_numpy()
    agg = {"glucose_mgdl": "mean"}
    for c in ("basal_raw",):
        if c in frame:
            agg[c] = "mean" if units["basal"] == "u_per_h" else (lambda s: s.sum(min_count=1))
    for c in ("bolus_u", "insulin_total_u", "carb_g"):
        if c in frame:
            agg[c] = lambda s: s.sum(min_count=1)
    for c in ("isf_clinician", "cycle_day", "cycle_len"):
        if c in frame:
            agg[c] = "median"
    out = frame.groupby(["person_id", "bin"]).agg(agg).reset_index()
    dup = int(frame.duplicated(["person_id", "bin"]).sum())
    if dup:
        log.append(f"{dup} rows share a {g}-min bin with another row: glucose averaged, doses/carbs summed")
    if "basal_raw" in out:
        if units["basal"] == "u_per_h":
            out = out.sort_values(["person_id", "bin"])
            lim = int(m.get("basal_ffill_minutes", 0) // g)
            if lim:
                out["basal_raw"] = out.groupby("person_id")["basal_raw"].ffill(limit=lim)
            out["basal_u"] = out["basal_raw"] * g / 60.0
        else:
            out["basal_u"] = out["basal_raw"]
        out = out.drop(columns="basal_raw")
    # regular grid per person between first and last bin (gaps stay NaN)
    parts = []
    for pid, d in out.groupby("person_id"):
        idx = pd.date_range(d["bin"].min().floor("D"), d["bin"].max().floor("D") + pd.Timedelta(days=1) - pd.Timedelta(minutes=g), freq=f"{g}min")
        d = d.set_index("bin").reindex(idx)
        d.index.name = "ts_local"
        d["person_id"] = pid
        parts.append(d.reset_index())
    ev = pd.concat(parts, ignore_index=True)
    ev["dataset"] = dataset
    ev["date_local"] = ev["ts_local"].dt.strftime("%Y-%m-%d")
    ev["glucose_flag"] = np.where(ev["glucose_mgdl"].isna(), "gap_missing", flag_glucose(ev["glucose_mgdl"].fillna(100.0)).to_numpy())
    for c in ("basal_u", "bolus_u", "carb_g"):
        if c not in ev:
            ev[c] = np.nan
    parts_present = [c for c in ("basal_u", "bolus_u") if c in cols or c.replace("_u", "") in cols]
    if "insulin_total_u" in ev:
        ev["insulin_u"] = ev["insulin_total_u"]
    else:
        ev["insulin_u"] = ev[["basal_u", "bolus_u"]].sum(axis=1, min_count=2) if len(parts_present) == 2 else ev[parts_present[0]] if parts_present else np.nan
    return ev


def build_person_day(ev: pd.DataFrame, m: dict) -> pd.DataFrame:
    g = int(m["grid_minutes"]); per_day = 1440 // g
    day = ev.groupby(["person_id", "date_local"])
    out = pd.DataFrame(index=day.size().index)
    gl = ev["glucose_mgdl"]
    out["cgm_coverage"] = day["glucose_mgdl"].count() / per_day
    out["mean_glucose_mgdl"] = day["glucose_mgdl"].mean()
    ev = ev.assign(_tir=gl.between(70, 180), _tbr=gl < 70, _tar=gl > 180)
    for k in ("tir", "tbr", "tar"):
        n = ev.groupby(["person_id", "date_local"])["glucose_mgdl"].count().replace(0, np.nan)
        out[f"{k}_pct"] = ev.groupby(["person_id", "date_local"])[f"_{k}"].sum() / n * 100.0
    for c in ("basal_u", "bolus_u", "carb_g"):
        out[c] = day[c].sum(min_count=1)
    ins_cov = day["insulin_u"].count() / per_day
    out["tdd_u"] = day["insulin_u"].sum(min_count=1)
    flags = pd.Series("", index=out.index)
    incomplete = ins_cov < float(m.get("min_insulin_coverage", 0.9))
    out.loc[incomplete, ["tdd_u", "basal_u", "bolus_u"]] = np.nan
    flags[incomplete] = "insulin_incomplete"
    out["carb_entries"] = day["carb_g"].count()
    out.loc[out["carb_g"].isna(), "carb_entries"] = np.nan
    out["pwd_flags"] = flags.replace("", np.nan)
    out = out.reset_index()
    out["dataset"], out["tz"], out["device_type"] = m["dataset"], m["tz"], (m.get("device_type") or None)
    out["person_id"] = out["person_id"].astype(str)
    if "cycle_day" in ev:
        cd = day["cycle_day"].median().reset_index(drop=True); cl = day["cycle_len"].median().reset_index(drop=True)
        out["cycle_day"], out["cycle_len"] = cd.round(), cl.round()
        out["cycle_pos"] = (out["cycle_day"] - 1) / out["cycle_len"]          # only from dataset-provided labels; phase stays NULL
    if "isf_clinician" in ev:
        out["isf_clinician"] = day["isf_clinician"].median().reset_index(drop=True)
    out = apply_inclusion(out.assign(exclude_flag=False, exclude_reason=None), float(m.get("min_cgm_coverage", 0.7)),
                          int(m.get("min_days_per_person", 7)))
    return out


def ingest_dataset(root: str | Path, mapping_path: str | Path, mode: str = "provisional") -> dict:
    """Run the ingest. Returns a summary dict (also written next to the outputs as ingest_report.json)."""
    import json
    from iris.common.io import write_table
    root = Path(root)
    m = load_mapping(mapping_path)
    reg = SourceRegistry.load(root / "data/sources_registry.csv", root / "data/manifest.csv")
    row = reg.require(m["source_id"], allow_unverified=(mode != "production"))
    log: list[str] = []
    evs = []
    for p in _files(root, m):
        if mode == "production":
            reg.require_file(p, root)                                  # manifest + hash gate (docs/data guides: `register_raw`)
        df = _read(p)
        missing = [c for c in m["columns"].values() if c not in df.columns]
        if missing:
            raise ScientificBlocker("column_mapping", f"{p.name}: mapped columns missing {missing}", "mapping must come from the audit of THIS dataset version")
        evs.append(_to_grid(df, m, m["dataset"], _person(p, df, m), log))
    ev = pd.concat(evs, ignore_index=True)
    ev["person_id"] = ev["person_id"].astype(str)
    pdy = build_person_day(ev, m)
    # schema validation (isf_clinician is an allowed extra carried alongside for L4/M5)
    extra = pdy[["isf_clinician"]] if "isf_clinician" in pdy else None
    core = finalize_person_day(pdy.drop(columns=["isf_clinician"]) if extra is not None else pdy)
    if extra is not None:
        core["isf_clinician"] = extra["isf_clinician"].to_numpy()
    out_dir = root / "data/processed" / m["dataset"]
    base_prov = row.to_provenance(transformation=f"ingest via {Path(mapping_path).name}", run_id="")
    pv = base_prov.derive(evidence_class=EvidenceClass.COMPUTED, source_id=f"person_day:{m['dataset']}",
                          transformation=f"harmonise to {m['grid_minutes']}-min grid, aggregate to person-days",
                          generated_by="iris.ingest.pipeline")
    ev_out = ev[EVENT_COLUMNS]
    h1 = write_table(ev_out, out_dir / "events_grid.parquet", [pv], extra={"run_mode": mode, "mapping": str(mapping_path)})
    h2 = write_table(core, out_dir / "person_day.parquet", [pv], extra={"run_mode": mode, "mapping": str(mapping_path)})
    rep = {"dataset": m["dataset"], "mode": mode, "persons": int(core["person_id"].nunique()), "person_days": int(len(core)),
           "included_person_days": int((~core["exclude_flag"]).sum()), "log": log,
           "has_cycle_labels": bool(core["cycle_pos"].notna().any()), "has_isf": bool("isf_clinician" in core and core["isf_clinician"].notna().any()),
           "sha256_person_day": h2, "sha256_events": h1}
    (out_dir / "ingest_report.json").write_text(json.dumps(rep, indent=2))
    return rep


def combine_person_day(root: str | Path, datasets: list[str] | None = None, mode: str = "provisional") -> Path:
    """Concatenate per-dataset person-day tables into data/processed/person_day.parquet (person ids namespaced by dataset)."""
    from iris.common.io import read_table, read_sidecar_meta, write_table
    root = Path(root)
    dirs = [root / "data/processed" / d for d in datasets] if datasets else sorted(p for p in (root / "data/processed").iterdir() if (p / "person_day.parquet").exists())
    frames, provs = [], []
    order = {"test": 0, "provisional": 1, "production": 2}
    for d in dirs:
        df, pv = read_table(d / "person_day.parquet")
        made = read_sidecar_meta(d / "person_day.parquet").get("run_mode", "unknown")
        if order.get(made, -1) < order[mode]:
            raise ScientificBlocker(d.name, f"ingested in '{made}' mode; cannot enter a '{mode}' combined table", "re-run ingest in the stricter mode")
        df = df.assign(person_id=df["dataset"] + ":" + df["person_id"])
        frames.append(df); provs += pv
    if not frames:
        raise ScientificBlocker("person_day", "no per-dataset person_day tables found", "run ingest_dataset first")
    allcols = list(dict.fromkeys(c for f in frames for c in f.columns))
    comb = pd.concat([f.reindex(columns=allcols) for f in frames], ignore_index=True)
    dst = root / "data/processed/person_day.parquet"
    write_table(comb, dst, provs, extra={"run_mode": mode, "datasets": [d.name for d in dirs]})
    return dst
