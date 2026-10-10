import shutil
from pathlib import Path

from iris.tools import sync_population_status as sp

REPO = Path(__file__).resolve().parents[2]


def _copy(tmp):
    for rel in (sp.CSV, sp.YML):
        (tmp / rel).parent.mkdir(parents=True, exist_ok=True); shutil.copy(REPO / rel, tmp / rel)

    # Keep the baseline sync tests independent of changes made while doing real
    # source verification in the working repository. The dedicated mismatch
    # tests below explicitly replace these two fixture rows with verified data.
    import csv
    p = tmp / sp.CSV
    with open(p, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        fields, rows = reader.fieldnames, list(reader)
    baseline = {
        "luteal_length_mean_d": "14.0",
        "luteal_length_sd_d": "1.7",
    }
    for row in rows:
        if row["parameter"] in baseline:
            row.update({
                "value": baseline[row["parameter"]],
                "ci_low": "",
                "ci_high": "",
                "page_table_ref": "[to locate]",
                "population": "[VERIFY] in document",
                "extracted_by": "document_appendix",
                "verified_by": "",
                "status": "PENDING_VERIFY",
            })
    with open(p, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    # Tests must use the pre-sync population configuration even when the real
    # repository has already been synchronized. Reset only the temporary copy.
    yml = tmp / sp.YML
    lines = yml.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if line.startswith("luteal_length:"):
            lines[i] = 'luteal_length: {mean_d: 14.0, sd_d: 1.7, status: PENDING_VERIFY, source_id: S1, note: "[VERIFY]"}'
            break
    else:
        raise AssertionError("luteal_length fixture row not found in population config")
    yml.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _resolve(tmp, names, value_override=None):
    p = tmp / sp.CSV; txt = p.read_text(encoding="utf-8-sig").splitlines()
    out = []
    for ln in txt:
        cells = ln.split(",")
        if cells[0] in names:
            cells[5 + 5 - 5] = cells[5]                      # keep column layout
            ln = ln.replace("PENDING_VERIFY", "RESOLVED").replace("[to locate]", "Table 2 p.1")
            ln = ln.replace(",document_appendix,,", ",document_appendix,Rev,")
        out.append(ln)
    p.write_text("\n".join(out) + "\n", encoding="utf-8")


def test_nothing_changes_without_verification(tmp_path):
    _copy(tmp_path); before = (tmp_path / sp.YML).read_text()
    ch, pr = sp.sync(tmp_path)
    assert ch == [] and pr == [] and (tmp_path / sp.YML).read_text() == before


def test_verified_rows_resolve_matching_config_only(tmp_path):
    _copy(tmp_path); _resolve(tmp_path, {"tdd_mean_u", "tdd_sd_u"})
    ch, pr = sp.sync(tmp_path)
    txt = (tmp_path / sp.YML).read_text()
    assert ch == ["tdd: -> RESOLVED"] and not pr
    assert "tdd:" in txt and "status: RESOLVED" in txt.splitlines()[4] and "status: PENDING_VERIFY" in txt.splitlines()[5]   # cycle untouched


def test_value_mismatch_is_reported_not_synced(tmp_path):
    _copy(tmp_path); _resolve(tmp_path, {"tdd_mean_u", "tdd_sd_u"})
    p = tmp_path / sp.CSV; p.write_text(p.read_text(encoding="utf-8-sig").replace("tdd_mean_u,37.3", "tdd_mean_u,37.4"), encoding="utf-8")
    ch, pr = sp.sync(tmp_path)
    assert ch == [] and len(pr) == 1 and "37.4" in pr[0]


def _set_luteal_evidence_resolved(tmp):
    import csv
    p = tmp / sp.CSV
    with open(p, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        fields, rows = reader.fieldnames, list(reader)
    vals = {"luteal_length_mean_d": "12.5", "luteal_length_sd_d": "1.2"}
    for row in rows:
        if row["parameter"] in vals:
            row["value"] = vals[row["parameter"]]
            row["page_table_ref"] = "Supplementary Appendix, Table 3, p. 6"
            row["extracted_by"] = "Divyesh Idhate"
            row["verified_by"] = "Gurman Dhillon"
            row["status"] = "RESOLVED"
    with open(p, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields); writer.writeheader(); writer.writerows(rows)


def test_documented_luteal_mismatch_requires_exact_decision_values(tmp_path):
    _copy(tmp_path); _set_luteal_evidence_resolved(tmp_path)
    note = tmp_path / "docs/decisions/D-21-luteal-mismatch.md"
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text(
        "# D-21: Resolve luteal-length mismatch\n\n"
        "## Approved sync values\n"
        "- luteal_length_mean_d: 12.5\n"
        "- luteal_length_sd_d: 1.2\n", encoding="utf-8"
    )
    before = (tmp_path / sp.YML).read_text()
    ch, pr = sp.sync(tmp_path, dry=True, approve_mismatch={"luteal_length"}, decision_note=Path("docs/decisions/D-21-luteal-mismatch.md"))
    assert ch == ["luteal_length: -> RESOLVED (approved mismatch per docs/decisions/D-21-luteal-mismatch.md)"]
    assert not pr
    assert (tmp_path / sp.YML).read_text() == before  # dry-run is read-only

    ch, pr = sp.sync(tmp_path, approve_mismatch={"luteal_length"}, decision_note=Path("docs/decisions/D-21-luteal-mismatch.md"))
    txt = (tmp_path / sp.YML).read_text()
    assert not pr and ch
    assert "luteal_length: {mean_d: 12.5, sd_d: 1.2, status: RESOLVED, source_id: S1}" in txt
    assert "[VERIFY]" not in txt


def test_documented_mismatch_rejects_decision_note_with_wrong_value(tmp_path):
    _copy(tmp_path); _set_luteal_evidence_resolved(tmp_path)
    note = tmp_path / "docs/decisions/D-21-luteal-mismatch.md"
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text(
        "# D-21: Resolve luteal-length mismatch\n\n"
        "## Approved sync values\n"
        "- luteal_length_mean_d: 14.0\n"
        "- luteal_length_sd_d: 1.2\n", encoding="utf-8"
    )
    before = (tmp_path / sp.YML).read_text()
    ch, pr = sp.sync(tmp_path, dry=True, approve_mismatch={"luteal_length"}, decision_note=Path("docs/decisions/D-21-luteal-mismatch.md"))
    assert not ch and len(pr) == 1 and "exact lines" in pr[0]
    assert (tmp_path / sp.YML).read_text() == before
