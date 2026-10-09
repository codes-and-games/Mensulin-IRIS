"""python -m iris.tools.sync_population_status [--root .] [--dry-run]

Bridge between human verification and the production gate. ``source_verification apply-params`` records sign-off in
``literature/biological_evidence.csv``; the gate reads each parameter's ``status`` in ``configs/population/population_default.yaml``.
This tool sets ``status: RESOLVED`` in the YAML **only** for parameters whose CSV row is RESOLVED, and only when the YAML value equals the
verified CSV value (a mismatch is reported and nothing is changed). For a parameter that was UNRESOLVED in the YAML it copies the verified
value/interval from the CSV. It never invents a value, never touches a row that is not RESOLVED, and keeps comments and layout."""
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


def sync(root: Path, dry: bool = False) -> tuple[list[str], list[str]]:
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
                problems.append(f"{key}: NOT synced, {'; '.join(bad)} (resolve via the 'paper disagrees' procedure)"); continue
            new = {**d, "status": "RESOLVED"}
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
            changes.append(f"{key}: -> RESOLVED")
    if changes and not dry:
        (root / YML).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return changes, problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(ROOT)); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    ch, pr = sync(Path(a.root), a.dry_run)
    for c in ch:
        print(("would set " if a.dry_run else "set ") + c)
    for p in pr:
        print("NOT SYNCED:", p)
    print(f"{len(ch)} parameter(s) {'would be ' if a.dry_run else ''}synced; {len(pr)} problem(s)")
    return 1 if pr else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
