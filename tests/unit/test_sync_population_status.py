import shutil
from pathlib import Path

from iris.tools import sync_population_status as sp

REPO = Path(__file__).resolve().parents[2]


def _copy(tmp):
    for rel in (sp.CSV, sp.YML):
        (tmp / rel).parent.mkdir(parents=True, exist_ok=True); shutil.copy(REPO / rel, tmp / rel)


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
