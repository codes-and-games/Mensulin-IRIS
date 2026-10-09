"""Source/parameter verification workflow (documents 12/16: NO SOURCE, NO NUMBER; human sign-off).

  python -m iris.tools.source_verification sources-worksheet [--out docs/literature/source_verification_worksheet.csv]
  python -m iris.tools.source_verification apply-sources   <filled_worksheet.csv> [--root .]
  python -m iris.tools.source_verification params-worksheet [--out docs/literature/parameter_verification_worksheet.csv]
  python -m iris.tools.source_verification apply-params    <filled_worksheet.csv> [--root .] [--allow-single-reader]

The tool NEVER fills evidence, licences, dates or sign-offs itself. ``apply-*`` copies only rows whose human-entered fields are
complete and consistent, appends an audit line to docs/literature/verification_log.csv and leaves everything else untouched.
Columns prefixed ``prepared_`` hold evidence pre-collected for the reviewer to CHECK; they are never copied into the registry."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC_COLS = ["source_id", "class", "title", "citation_or_url_current", "used_in_files", "prepared_evidence", "prepared_open_questions",
            "doi_or_url_confirmed", "version", "access_date", "licence_or_access", "claim_location", "evidence_note", "evidence_type",
            "ambiguity_note", "dataset_sha256", "status", "verified_by", "verified_on"]
PAR_COLS = ["parameter", "source_id", "value_in_iris", "unit", "status_now", "extracted_by", "prepared_evidence", "value_in_paper",
            "page_table_ref", "matches", "corrected_value_if_no", "reviewer_note", "verified_by", "verified_on"]
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LOG_FIELDS = ["applied_on", "kind", "id", "action", "verified_by", "claim_location", "note"]


def _read(p: Path) -> list[dict]:
    with open(p, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def _write(p: Path, rows: list[dict], fields: list[str]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields); w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def _log(root: Path, rows: list[dict]) -> None:
    p = root / "docs/literature/verification_log.csv"
    new = not p.exists()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=LOG_FIELDS)
        if new:
            w.writeheader()
        for r in rows:
            w.writerow({"applied_on": dt.date.today().isoformat(), **r})


def used_in(root: Path, sid: str) -> str:
    hits = []
    pat = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(sid)}(?![A-Za-z0-9_])")
    for d in ("configs", "literature", "src"):
        for f in sorted((root / d).rglob("*")):
            if f.is_file() and f.suffix in (".yaml", ".csv", ".py") and "__pycache__" not in f.parts:
                try:
                    if pat.search(f.read_text(errors="ignore")):
                        hits.append(str(f.relative_to(root)).replace("\\", "/"))
                except OSError:
                    pass
    return "; ".join(hits[:8])


def sources_worksheet(root: Path, out: Path, prepared: dict[str, dict] | None = None) -> int:
    prepared = prepared or {}
    rows = []
    for r in _read(root / "data/sources_registry.csv"):
        sid = r["source_id"]
        p = prepared.get(sid, {})
        rows.append({"source_id": sid, "class": r["class"], "title": r["title"], "citation_or_url_current": r["citation_or_url"],
                     "used_in_files": used_in(root, sid), "prepared_evidence": p.get("evidence", ""), "prepared_open_questions": p.get("open", ""),
                     "evidence_type": "", "status": "OPEN"})
    _write(out, rows, SRC_COLS)
    return len(rows)


def _check_source_row(r: dict, cls: str) -> list[str]:
    e = []
    if r["status"].strip().upper() != "VERIFIED":
        return ["status is not VERIFIED"]
    if not r["verified_by"].strip():
        e.append("verified_by empty")
    if not ISO.match(r["access_date"].strip()):
        e.append("access_date must be YYYY-MM-DD (the day YOU accessed the primary source)")
    if not r["licence_or_access"].strip():
        e.append("licence_or_access empty (quote the licence/terms line, or 'copyright journal; cited, not redistributed')")
    if not r["doi_or_url_confirmed"].strip():
        e.append("doi_or_url_confirmed empty")
    if cls == "PUBLISHED":
        if not r["claim_location"].strip():
            e.append("claim_location empty (page/table/figure/section)")
        if r["evidence_type"].strip().lower() not in ("direct", "derived"):
            e.append("evidence_type must be 'direct' or 'derived'")
    if cls == "PUBLIC_DATASET" and not r["version"].strip():
        e.append("version empty (dataset version/DOI version)")
    d = r.get("dataset_sha256", "").strip()
    if d and not re.fullmatch(r"[0-9a-fA-F]{64}", d):
        e.append("dataset_sha256 must be the 64-hex digest printed by register_raw")
    return e


def apply_sources(root: Path, sheet: Path) -> tuple[int, list[str]]:
    reg_p = root / "data/sources_registry.csv"
    with open(reg_p, newline="", encoding="utf-8-sig") as fh:
        rd = csv.DictReader(fh); fields = rd.fieldnames; reg = list(rd)
    by = {r["source_id"]: r for r in reg}
    done, problems, logrows = 0, [], []
    for r in _read(sheet):
        sid = r["source_id"].strip()
        if r["status"].strip().upper() in ("", "OPEN"):
            continue
        if sid not in by:
            problems.append(f"{sid}: not in registry"); continue
        errs = _check_source_row(r, by[sid]["class"])
        if errs:
            problems.append(f"{sid}: " + "; ".join(errs)); continue
        row = by[sid]
        row["citation_or_url"] = r["doi_or_url_confirmed"].strip()
        row["access_date"], row["licence"] = r["access_date"].strip(), r["licence_or_access"].strip()
        if r["version"].strip():
            row["version"] = r["version"].strip()
        if r.get("dataset_sha256", "").strip():            # printed by `register_raw`; copied verbatim, never computed here
            row["sha256"] = r["dataset_sha256"].strip().lower()
        row["verified_by"] = r["verified_by"].strip()
        logrows.append({"kind": "source", "id": sid, "action": "VERIFIED", "verified_by": row["verified_by"],
                        "claim_location": r["claim_location"].strip(), "note": r["ambiguity_note"].strip()})
        done += 1
    if done:
        with open(reg_p, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields); w.writeheader(); w.writerows(reg)
        _log(root, logrows)
    return done, problems


def params_worksheet(root: Path, out: Path, prepared: dict[str, str] | None = None) -> int:
    prepared = prepared or {}
    rows = []
    for r in _read(root / "literature/biological_evidence.csv"):
        rows.append({"parameter": r["parameter"], "source_id": r["source_id"], "value_in_iris": r["value"], "unit": r["unit"],
                     "status_now": r["status"], "extracted_by": r["extracted_by"], "prepared_evidence": prepared.get(r["parameter"], "")})
    _write(out, rows, PAR_COLS)
    return len(rows)


def apply_params(root: Path, sheet: Path, allow_single_reader: bool = False) -> tuple[int, list[str]]:
    p = root / "literature/biological_evidence.csv"
    with open(p, newline="", encoding="utf-8-sig") as fh:
        rd = csv.DictReader(fh); fields = rd.fieldnames; rows = list(rd)
    by = {r["parameter"]: r for r in rows}
    done, problems, logrows = 0, [], []
    for s in _read(sheet):
        name = s["parameter"].strip()
        r = by.get(name)
        if r is None:
            problems.append(f"{name}: not in biological_evidence.csv"); continue
        if not s["verified_by"].strip() and not s["value_in_paper"].strip():
            continue
        loc = s["page_table_ref"].strip()
        if not loc:
            problems.append(f"{name}: page_table_ref empty"); continue
        if r["status"] == "UNRESOLVED":                       # first extraction
            if not s["value_in_paper"].strip() or not s["verified_by"].strip():
                problems.append(f"{name}: UNRESOLVED needs value_in_paper and the extractor's name in verified_by"); continue
            r["value"], r["page_table_ref"], r["extracted_by"], r["status"] = s["value_in_paper"].strip(), loc, s["verified_by"].strip(), "PENDING_VERIFY"
            logrows.append({"kind": "parameter", "id": name, "action": "EXTRACTED->PENDING_VERIFY", "verified_by": s["verified_by"], "claim_location": loc, "note": s["reviewer_note"]})
            done += 1
            continue
        m = s["matches"].strip().lower()
        if m not in ("yes", "no"):
            problems.append(f"{name}: matches must be yes/no"); continue
        if m == "no":
            problems.append(f"{name}: value does not match the paper -> NOT applied; resolve the discrepancy (see docs/runbook troubleshooting) and re-extract"); 
            logrows.append({"kind": "parameter", "id": name, "action": "MISMATCH_REPORTED", "verified_by": s["verified_by"], "claim_location": loc, "note": s["corrected_value_if_no"] or s["reviewer_note"]})
            continue
        if not s["verified_by"].strip():
            problems.append(f"{name}: verified_by empty"); continue
        if s["verified_by"].strip() == r["extracted_by"].strip() and not allow_single_reader:
            problems.append(f"{name}: verifier equals extractor (second reader required; use --allow-single-reader to record a documented limitation)"); continue
        r["page_table_ref"], r["verified_by"], r["status"] = loc, s["verified_by"].strip(), "RESOLVED"
        logrows.append({"kind": "parameter", "id": name, "action": "RESOLVED" + ("(single_reader)" if s["verified_by"].strip() == r["extracted_by"].strip() else ""),
                        "verified_by": s["verified_by"], "claim_location": loc, "note": s["reviewer_note"]})
        done += 1
    if done:
        with open(p, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields); w.writeheader(); w.writerows(rows)
    if logrows:
        _log(root, logrows)
    return done, problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for n in ("sources-worksheet", "params-worksheet"):
        s = sub.add_parser(n); s.add_argument("--out"); s.add_argument("--root", default=str(ROOT))
    for n in ("apply-sources", "apply-params"):
        s = sub.add_parser(n); s.add_argument("sheet"); s.add_argument("--root", default=str(ROOT))
        if n == "apply-params":
            s.add_argument("--allow-single-reader", action="store_true")
    a = ap.parse_args(argv)
    root = Path(a.root)
    if a.cmd == "sources-worksheet":
        print(sources_worksheet(root, Path(a.out) if a.out else root / "docs/literature/source_verification_worksheet.csv"), "rows written")
    elif a.cmd == "params-worksheet":
        print(params_worksheet(root, Path(a.out) if a.out else root / "docs/literature/parameter_verification_worksheet.csv"), "rows written")
    else:
        fn = apply_sources if a.cmd == "apply-sources" else (lambda r, s: apply_params(r, s, a.allow_single_reader))
        n, problems = fn(root, Path(a.sheet))
        print(f"applied {n} row(s)")
        for pr in problems:
            print("NOT APPLIED:", pr)
        return 1 if problems else 0
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
