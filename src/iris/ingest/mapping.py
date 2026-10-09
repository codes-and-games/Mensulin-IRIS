"""Column-mapping contract (configs/mappings/<dataset>.yaml) and the mapping-template generator.

Principle: a mapping is *evidence-backed*. ``make_template`` proposes candidates from an audit JSON using only column
names/units found in the audit (never from filenames or memory); a human sets ``audit_status: AUDITED`` after checking
each role against the dataset's data dictionary. ``validate_mapping`` is the single gate used by the ingest pipeline.

Roles
  required : timestamp, glucose  (glucose unit mg/dL or mmol/L)
  insulin  : EITHER (basal and/or bolus)  OR  insulin_total  (one column holding all insulin per step, e.g. BrisT1D)
  optional : carb, isf_clinician, cycle_day, cycle_len
Basal units: u_per_h (a rate), u_per_step (amount delivered in the step), u_per_day (a daily total column).
"""
from __future__ import annotations

import re
from pathlib import Path

from iris.common.exceptions import ScientificBlocker
from iris.common.io import load_yaml

ROLES = ("timestamp", "glucose", "basal", "bolus", "insulin_total", "carb", "isf_clinician", "cycle_day", "cycle_len")
GLUCOSE_UNITS = {"mg/dl", "mmol/l"}
BASAL_UNITS = {"u_per_h", "u_per_step"}
INSULIN_STEP_UNITS = {"u_per_step"}

# keyword hints used ONLY to rank candidates in a DRAFT template; they are never accepted automatically.
HINTS = {
    "timestamp": ("time", "date", "timestamp", "datetime"),
    "glucose": ("glucose", "cgm", "bg", "sgv", "glu"),
    "basal": ("basal",),
    "bolus": ("bolus",),
    "insulin_total": ("insulin",),
    "carb": ("carb", "cho", "meal"),
    "isf_clinician": ("isf", "sensitivity", "correction"),
    "cycle_day": ("cycle_day", "cycleday", "menstrual_day"),
    "cycle_len": ("cycle_len", "cyclelength", "cycle_length"),
}


def validate_mapping(m: dict, *, require_audited: bool = True) -> list[str]:
    """Return a list of problems (empty = valid)."""
    errs: list[str] = []
    for k in ("dataset", "source_id", "raw_dir", "grid_minutes", "tz", "columns", "units", "person_id"):
        if k not in m or m[k] in (None, "", {}):
            errs.append(f"missing key: {k}")
    if errs:
        return errs
    if require_audited and (m.get("audit_status") != "AUDITED" or not m.get("audit_file")):
        errs.append("audit_status must be AUDITED and audit_file set (a human confirmed every role against the audit/data dictionary)")
    cols, units = m["columns"], m["units"]
    for r in cols:
        if r not in ROLES:
            errs.append(f"unknown role {r!r}; allowed: {ROLES}")
    if "timestamp" not in cols or "glucose" not in cols:
        errs.append("roles 'timestamp' and 'glucose' are required")
    if "glucose" in cols and str(units.get("glucose", "")).lower().replace(" ", "") not in GLUCOSE_UNITS:
        errs.append(f"units.glucose must be one of {sorted(GLUCOSE_UNITS)}")
    has_split = "basal" in cols or "bolus" in cols
    if has_split and "insulin_total" in cols:
        errs.append("use either basal/bolus OR insulin_total, not both (double counting)")
    if not has_split and "insulin_total" not in cols:
        errs.append("no insulin role mapped: TDD cannot be computed (map basal/bolus or insulin_total)")
    if "basal" in cols and units.get("basal") not in BASAL_UNITS:
        errs.append(f"units.basal must be one of {sorted(BASAL_UNITS)} (a rate vs an amount must be stated, never assumed)")
    for r in ("bolus", "insulin_total"):
        if r in cols and units.get(r) not in INSULIN_STEP_UNITS | {"u"}:
            errs.append(f"units.{r} must be 'u' (amount per record) or 'u_per_step'")
    if "carb" in cols and units.get("carb") != "g":
        errs.append("units.carb must be 'g'")
    if int(m["grid_minutes"]) <= 0 or 1440 % int(m["grid_minutes"]):
        errs.append("grid_minutes must divide 1440")
    pid = m["person_id"]
    if pid.get("from") not in ("filename", "column", "constant"):
        errs.append("person_id.from must be filename|column|constant")
    if pid.get("from") == "column" and not pid.get("column"):
        errs.append("person_id.column required when from: column")
    if ("cycle_day" in cols) != ("cycle_len" in cols):
        errs.append("cycle_day and cycle_len must be mapped together (labels are never inferred)")
    if "cycle_day" in cols and not m.get("cycle_label_provenance"):
        errs.append("cycle labels mapped but cycle_label_provenance (how the dataset defines them) is empty")
    return errs


def load_mapping(path: str | Path, *, require_audited: bool = True) -> dict:
    p = Path(path)
    if not p.exists():
        raise ScientificBlocker("column_mapping", f"no mapping at {p}", "run make_mapping_template on the audit, review it, set audit_status: AUDITED")
    m = load_yaml(p)
    errs = validate_mapping(m, require_audited=require_audited)
    if errs:
        raise ScientificBlocker("column_mapping", f"{p.name}: " + "; ".join(errs), "fix the mapping (see docs/data/04_ingestion_and_mapping.md)")
    return m


def _rank(role: str, col: str) -> int:
    c = col.lower()
    return sum(1 for h in HINTS[role] if re.search(h, c))


def make_template(audit: dict, dataset: str, source_id: str, raw_dir: str) -> dict:
    """DRAFT mapping from an audit report. Every guess is listed under ``candidates`` for human decision."""
    files = [f for f in audit.get("files", []) if "columns" in f]
    cols: dict[str, dict] = {}
    for f in files:
        for c, info in f["columns"].items():
            d = cols.setdefault(c, {"n_files": 0, "dtype": info["dtype"], "min": info.get("min"), "max": info.get("max"),
                                    "timestamp_like": info.get("timestamp_like", False), "missing_frac_max": 0.0})
            d["n_files"] += 1
            d["missing_frac_max"] = max(d["missing_frac_max"], info["missing_frac"])
    candidates = {}
    for role in HINTS:
        ranked = sorted(((_rank(role, c), c) for c in cols), reverse=True)
        candidates[role] = [{"column": c, "score": s, **{k: cols[c][k] for k in ("dtype", "min", "max", "timestamp_like", "n_files")}}
                            for s, c in ranked if s > 0][:5]
    return {
        "dataset": dataset, "source_id": source_id, "audit_status": "DRAFT", "audit_file": "",
        "raw_dir": raw_dir, "file_glob": "**/*.csv", "tz": "",           # tz MUST be set from the data paper/dictionary
        "grid_minutes": 5,
        "person_id": {"from": "filename", "column": None},
        "columns": {},                                                   # role -> column name; fill after review
        "units": {},                                                     # role -> unit; fill after review (never assumed)
        "min_cgm_coverage": 0.7, "min_insulin_coverage": 0.9, "min_days_per_person": 7,
        "basal_ffill_minutes": 0, "device_type": "",
        "REVIEW_REQUIRED": ("Fill columns/units/tz from the data dictionary, check each against `candidates`, "
                            "then set audit_status: AUDITED and audit_file. Delete this key and `candidates` when done."),
        "candidates": candidates,
        "n_files_audited": len(files),
    }
