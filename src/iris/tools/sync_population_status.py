"""python -m iris.tools.sync_population_status [--root .] [--dry-run]

Bridge between human verification and the production gate. ``source_verification apply-params`` records sign-off in
``literature/biological_evidence.csv``; the gate reads each parameter's ``status`` in ``configs/population/population_default.yaml``.
This tool sets ``status: RESOLVED`` in the YAML **only** for parameters whose CSV row is RESOLVED, and only when the YAML value equals the
verified CSV value (a mismatch is reported and nothing is changed by default). A deliberate, documented source correction can be applied only with
``--approve-mismatch GROUP --decision-note PATH``; the numbered note must list the exact verified values under ``## Approved sync values``. It never
invents a value, never touches a row that is not RESOLVED, and keeps comments and layout."""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
CSV = "literature/biological_evidence.csv"
YML = "configs/population/population_default.yaml"
SCALAR = {"tdd": {"mean_u": "tdd_mean_u", "sd_u": "tdd_sd_u"}, "cycle": {"mean_d": "cycle_length_mean_d", "sd_d": "cycle_length_sd_d"},
          "luteal_length": {"mean_d": "luteal_length_mean_d", "sd_d": "luteal_length_sd_d"}}
SINGLE = {"concordance_with_population_direction": "share_consistent_with_population_trend"}
PHASES = ["early_follicular", "late_follicular", "periovulatory", "early_luteal", "midluteal", "late_luteal"]
LINE = re.compile(r"^(?P<ind>\s*)(?P<key>[A-Za-z_]+):\s*\{(?P<body>.*)\}(?P<tail>\s*(#.*)?)$")


def _f(x):
    return float(x) if str(x).strip() not in ("", "None") else None


def _fmt(d: dict) -> str:
    def v(x):
        return "[" + ", ".join(f"{i:g}" for i in x) + "]" if isinstance(x, list) else (f"{x:g}" if isinstance(x, float) else str(x))
    return "{" + ", ".join(f"{k}: {v(x)}" for k, x in d.items()) + "}"


def _decision_approves_values(text: str, values: dict[str, float]) -> bool:
    """Require a numbered decision note to explicitly name each approved value.

    This deliberately does not infer approval from a narrative paragraph. The
    note must contain a machine-checkable section so an overwrite is deliberate
    and reviewable.
    """
    if not re.search(r"(?mi)^#\s+D-\d+\b", text):
        return False
    section = re.search(r"(?ms)^## Approved sync values\s*\n(.*?)(?=^## |\Z)", text)
    if section is None:
        return False
    body = section.group(1)
    for name, value in values.items():
        pattern = rf"(?m)^\s*-\s*{re.escape(name)}\s*:\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)\s*$"
        matches = list(re.finditer(pattern, body))
        if len(matches) != 1:
            return False
        if abs(float(matches[0].group(1)) - float(value)) > 1e-9:
            return False
    return True


def sync(
    root: Path,
    dry: bool = False,
    approve_mismatch: set[str] | None = None,
    decision_note: Path | None = None,
) -> tuple[list[str], list[str]]:
    """Synchronise verified literature values to the population configuration.

    A mismatching, already populated scalar may be replaced only with an
    explicit ``approve_mismatch`` selection and a numbered decision note that
    lists the exact verified values under ``## Approved sync values``.
    Ordinary syncs remain fail-closed.
    """
    approve_mismatch = approve_mismatch or set()
    decision_text = ""
    decision_label = ""
    if approve_mismatch:
        if decision_note is None:
            raise ValueError("--approve-mismatch requires --decision-note")
        note_path = decision_note if decision_note.is_absolute() else root / decision_note
        note_path = note_path.resolve()
        try:
            note_path.relative_to(root.resolve())
        except ValueError as exc:
            raise ValueError("decision note must be inside the repository root") from exc
        if not note_path.is_file():
            raise ValueError(f"decision note not found: {note_path}")
        decision_text = note_path.read_text(encoding="utf-8")
        decision_label = str(note_path.relative_to(root.resolve())).replace("\\", "/")
    unknown = approve_mismatch - set(SCALAR)
    if unknown:
        raise ValueError("unsupported mismatch group(s): " + ", ".join(sorted(unknown)))

    with open(root / CSV, newline="", encoding="utf-8-sig") as fh:
        bio = {r["parameter"]: r for r in csv.DictReader(fh)}
    ok = lambda n: n in bio and bio[n]["status"] == "RESOLVED" and bio[n]["page_table_ref"].strip() and bio[n]["verified_by"].strip()
    lines = (root / YML).read_text(encoding="utf-8").splitlines()
    changes, problems = [], []
    for i, ln in enumerate(lines):
        m = LINE.match(ln)
        if not m:
            continue
        key = m["key"]; d = yaml.safe_load("{" + m["body"] + "}")
        new = None
        if key in SCALAR and m["ind"] == "":
            need = SCALAR[key]
            if not all(ok(n) for n in need.values()) or d.get("status") == "RESOLVED":
                continue
            bad = [f"{k}: config {d.get(k)} vs verified {bio[n]['value']}" for k, n in need.items() if d.get(k) is None or abs(float(d[k]) - float(bio[n]["value"])) > 1e-9]
            if bad:
                if key not in approve_mismatch:
                    problems.append(f"{key}: NOT synced, {'; '.join(bad)} (resolve via the 'paper disagrees' procedure)"); continue
                approved_values = {n: float(bio[n]["value"]) for n in need.values()}
                if not _decision_approves_values(decision_text, approved_values):
                    names = ", ".join(f"{name}: {value:g}" for name, value in approved_values.items())
                    problems.append(f"{key}: NOT synced; decision note must contain a numbered D-# heading and '## Approved sync values' with exact lines for {names}"); continue
                # The evidence rows above must already be RESOLVED with source
                # locations and verifier names. Copy only those verified values.
                d = {**d, **{config_field: approved_values[param] for config_field, param in need.items()}}
                if isinstance(d.get("note"), str) and any(tag in d["note"] for tag in ("[VERIFY]", "[TO EXTRACT]")):
                    d.pop("note")
                new = {**d, "status": "RESOLVED"}
                changes.append(f"{key}: -> RESOLVED (approved mismatch per {decision_label})")
            else:
                new = {**d, "status": "RESOLVED"}
                changes.append(f"{key}: -> RESOLVED")
        elif key in SINGLE and m["ind"] == "":
            n = SINGLE[key]
            if not ok(n) or d.get("status") == "RESOLVED":
                continue
            if abs(float(d["value"]) - float(bio[n]["value"])) > 1e-9:
                problems.append(f"{key}: NOT synced, config {d['value']} vs verified {bio[n]['value']}"); continue
            new = {**d, "status": "RESOLVED"}
        elif key in PHASES and m["ind"] != "":
            n = f"sensitivity_contrast_{key}"
            if not ok(n) or d.get("status") == "RESOLVED":
                continue
            val = _f(bio[n]["value"]); lo, hi = _f(bio[n]["ci_low"]), _f(bio[n]["ci_high"])
            if d.get("value") is not None:
                same = abs(float(d["value"]) - val) < 1e-9 and (not d.get("ci") or (abs(d["ci"][0] - lo) < 1e-9 and abs(d["ci"][1] - hi) < 1e-9))
                if not same:
                    problems.append(f"{key}: NOT synced, config {d['value']} {d.get('ci')} vs verified {val} [{lo}, {hi}]"); continue
                new = {**d, "status": "RESOLVED"}
            else:                                                       # UNRESOLVED in config: copy the verified value
                new = {"value": val, **({"ci": [lo, hi]} if lo is not None and hi is not None else {}), "status": "RESOLVED", "source_id": bio[n]["source_id"]}
        if new is not None:
            lines[i] = f"{m['ind']}{key}:{' ' * max(1, 18 - len(key) - 1)}{_fmt(new)}{m['tail']}".rstrip() if m["ind"] else f"{key}: {_fmt(new)}{m['tail']}".rstrip()
            if not any(item.startswith(f"{key}: ") for item in changes):
                changes.append(f"{key}: -> RESOLVED")
    if changes and not dry:
        (root / YML).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return changes, problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(ROOT)); ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--approve-mismatch", action="append", default=[], choices=sorted(SCALAR), metavar="GROUP",
                    help="explicitly allow a verified value to replace a conflicting scalar config value; requires --decision-note")
    ap.add_argument("--decision-note", type=Path, help="numbered decision note containing an exact '## Approved sync values' section")
    a = ap.parse_args(argv)
    try:
        ch, pr = sync(Path(a.root), a.dry_run, set(a.approve_mismatch), a.decision_note)
    except ValueError as exc:
        ap.error(str(exc))
    for c in ch:
        print(("would set " if a.dry_run else "set ") + c)
    for p in pr:
        print("NOT SYNCED:", p)
    print(f"{len(ch)} parameter(s) {'would be ' if a.dry_run else ''}synced; {len(pr)} problem(s)")
    return 1 if pr else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
