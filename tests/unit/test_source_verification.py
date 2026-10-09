import csv
from iris.tools import source_verification as sv

REG = "source_id,class,title,citation_or_url,version,access_date,licence,sha256,used_for,verified_by\r\nS1,PUBLISHED,t,x,,,,,u,\r\nS15,PUBLIC_DATASET,d,y,,,,,u,\r\n"
BIO = "parameter,value,ci_low,ci_high,unit,source_id,page_table_ref,population,extracted_by,verified_by,status\r\ntdd_mean_u,37.3,,,U/day,S1,[to locate],p,document_appendix,,PENDING_VERIFY\r\nnew_p,,,,d,S1,,[TO EXTRACT],,,UNRESOLVED\r\n"


def _setup(tmp_path):
    (tmp_path / "data").mkdir(); (tmp_path / "literature").mkdir(); (tmp_path / "configs").mkdir(); (tmp_path / "src").mkdir()
    (tmp_path / "data/sources_registry.csv").write_text(REG); (tmp_path / "literature/biological_evidence.csv").write_text(BIO)


def _fill(path, **kw):
    rows = list(csv.DictReader(open(path)))
    rows[0].update(kw)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def test_incomplete_source_rows_are_never_applied(tmp_path):
    _setup(tmp_path); sh = tmp_path / "w.csv"; sv.sources_worksheet(tmp_path, sh)
    _fill(sh, status="VERIFIED", verified_by="A")        # missing date, licence, location ...
    n, probs = sv.apply_sources(tmp_path, sh)
    assert n == 0 and any("access_date" in p for p in probs)
    assert all(r["verified_by"] == "" for r in csv.DictReader(open(tmp_path / "data/sources_registry.csv")))


def test_complete_source_row_updates_registry_and_logs(tmp_path):
    _setup(tmp_path); sh = tmp_path / "w.csv"; sv.sources_worksheet(tmp_path, sh)
    _fill(sh, status="VERIFIED", verified_by="Reviewer", access_date="2026-10-08", licence_or_access="journal copyright; cited only",
          doi_or_url_confirmed="doi:10.x/y", claim_location="Table 1", evidence_type="direct")
    n, probs = sv.apply_sources(tmp_path, sh)
    assert n == 1 and not probs
    reg = list(csv.DictReader(open(tmp_path / "data/sources_registry.csv")))
    assert reg[0]["verified_by"] == "Reviewer" and reg[0]["access_date"] == "2026-10-08" and reg[1]["verified_by"] == ""
    assert (tmp_path / "docs/literature/verification_log.csv").exists()


def test_parameters_need_second_reader_and_mismatch_is_not_applied(tmp_path):
    _setup(tmp_path); sh = tmp_path / "p.csv"; sv.params_worksheet(tmp_path, sh)
    _fill(sh, matches="yes", page_table_ref="Table 1", verified_by="document_appendix")
    n, probs = sv.apply_params(tmp_path, sh)
    assert n == 0 and any("second reader" in p for p in probs)
    _fill(sh, matches="no", page_table_ref="Table 1", verified_by="R")
    n, probs = sv.apply_params(tmp_path, sh)
    assert n == 0 and any("does not match" in p for p in probs)
    _fill(sh, matches="yes", page_table_ref="Table 1", verified_by="R")
    n, probs = sv.apply_params(tmp_path, sh)
    assert n == 1
    assert "RESOLVED" in (tmp_path / "literature/biological_evidence.csv").read_text()


def test_dataset_digest_is_copied_only_when_well_formed(tmp_path):
    _setup(tmp_path); sh = tmp_path / "w.csv"; sv.sources_worksheet(tmp_path, sh)
    rows = list(csv.DictReader(open(sh)))
    rows[1].update(status="VERIFIED", verified_by="R", access_date="2026-10-08", licence_or_access="CC BY 4.0 (quoted from page)",
                   doi_or_url_confirmed="doi:10.17632/x", version="v1", dataset_sha256="abc")
    with open(sh, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    n, probs = sv.apply_sources(tmp_path, sh)
    assert n == 0 and any("dataset_sha256" in p for p in probs)                    # malformed digest is rejected
    rows[1]["dataset_sha256"] = "a" * 64
    with open(sh, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    n, probs = sv.apply_sources(tmp_path, sh)
    assert n == 1 and not probs
    assert list(csv.DictReader(open(tmp_path / "data/sources_registry.csv")))[1]["sha256"] == "a" * 64
