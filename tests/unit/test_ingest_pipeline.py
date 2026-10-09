"""Ingest pipeline on TEST-ONLY synthetic raw files (written to tmp; never in data/raw)."""
import json
import numpy as np
import pandas as pd
import pytest

from iris.common.exceptions import ScientificBlocker
from iris.common.io import dump_yaml, read_table
from iris.ingest.audit import audit_directory
from iris.ingest.mapping import make_template, validate_mapping
from iris.ingest.pipeline import combine_person_day, ingest_dataset
from iris.tools.validate_person_day import qc_report

REG = "source_id,class,title,citation_or_url,version,access_date,licence,sha256,used_for,verified_by\nT_DS,PUBLIC_DATASET,test ds,doi:test,v1,,,,test,\n"


def _raw(root, kind="rate"):
    d = root / "data/raw/t_ds"; d.mkdir(parents=True)
    rng = np.random.default_rng(0)
    for k in range(3):
        t = pd.date_range("2026-03-01", periods=288 * 10, freq="5min")
        df = pd.DataFrame({"time": t.strftime("%Y-%m-%d %H:%M:%S"), "glucose": rng.normal(140, 20, len(t)).round(0),
                           "carb_input": np.where(rng.random(len(t)) < 0.01, 40.0, np.nan)})
        if kind == "rate":
            df["basal_rate"] = 1.0; df["bolus_volume"] = np.where(rng.random(len(t)) < 0.01, 4.0, 0.0)
        else:
            df["insulin"] = 0.1
        df.to_csv(d / f"p{k}.csv", index=False)
    (root / "data").mkdir(exist_ok=True)
    (root / "data/sources_registry.csv").write_text(REG)
    return d


def _mapping(root, kind="rate"):
    cols = {"timestamp": "time", "glucose": "glucose", "carb": "carb_input"}
    units = {"glucose": "mg/dL", "carb": "g"}
    if kind == "rate":
        cols |= {"basal": "basal_rate", "bolus": "bolus_volume"}; units |= {"basal": "u_per_h", "bolus": "u"}
    else:
        cols["insulin_total"] = "insulin"; units["insulin_total"] = "u_per_step"
    m = {"dataset": "t_ds", "source_id": "T_DS", "audit_status": "AUDITED", "audit_file": "x.json", "raw_dir": "data/raw/t_ds",
         "file_glob": "*.csv", "tz": "UTC", "grid_minutes": 5, "person_id": {"from": "filename"}, "columns": cols, "units": units,
         "min_cgm_coverage": 0.7, "min_insulin_coverage": 0.9, "min_days_per_person": 7}
    p = root / "configs/mappings/t_ds.yaml"; dump_yaml(m, p)
    return p


@pytest.mark.parametrize("kind", ["rate", "total"])
def test_ingest_end_to_end_units(tmp_path, kind):
    _raw(tmp_path, kind); mp = _mapping(tmp_path, kind)
    rep = ingest_dataset(tmp_path, mp, "provisional")
    pdy, prov = read_table(tmp_path / "data/processed/t_ds/person_day.parquet")
    assert rep["persons"] == 3 and (~pdy.exclude_flag).sum() == 30
    # rate 1 U/h*24h = 24 U basal + ~bolus ; total: 0.1 U * 288 = 28.8 U  (units handled exactly, no guessing)
    inc = pdy[~pdy.exclude_flag]
    if kind == "rate":
        assert np.allclose(inc.basal_u, 24.0) and (inc.tdd_u >= 24.0).all()
    else:
        assert np.allclose(inc.tdd_u, 28.8) and inc.basal_u.isna().all()
    assert not rep["has_cycle_labels"] and pdy.cycle_pos.isna().all()          # no cycle labels invented
    assert prov[0].source_id.startswith("person_day:") and "T_DS" in prov[0].parent_source_ids
    assert qc_report(pdy)["hard_failures"] == []


def test_incomplete_insulin_never_guessed(tmp_path):
    d = _raw(tmp_path, "total"); mp = _mapping(tmp_path, "total")
    f = d / "p0.csv"; df = pd.read_csv(f); df.loc[:400, "insulin"] = np.nan; df.to_csv(f, index=False)   # >1 day with no insulin record
    ingest_dataset(tmp_path, mp, "provisional")
    pdy, _ = read_table(tmp_path / "data/processed/t_ds/person_day.parquet")
    bad = pdy[(pdy.person_id == "p0") & (pdy.pwd_flags == "insulin_incomplete")]
    assert len(bad) >= 1 and bad.tdd_u.isna().all()


def test_mapping_gates(tmp_path):
    _raw(tmp_path); mp = _mapping(tmp_path)
    assert validate_mapping({"dataset": "x"}) != []
    from iris.common.io import load_yaml
    m = load_yaml(mp)
    m["units"].pop("basal"); assert any("units.basal" in e for e in validate_mapping(m))
    m = load_yaml(mp); m["columns"]["insulin_total"] = "i"; assert any("double counting" in e for e in validate_mapping(m))
    m = load_yaml(mp); m["columns"]["cycle_day"] = "c"; assert any("together" in e for e in validate_mapping(m))
    m = load_yaml(mp); m["audit_status"] = "DRAFT"; dump_yaml(m, mp)
    with pytest.raises(ScientificBlocker):
        ingest_dataset(tmp_path, mp, "provisional")


def test_production_requires_verified_source_and_manifest(tmp_path):
    _raw(tmp_path); mp = _mapping(tmp_path)
    with pytest.raises(Exception):                                   # registered but unverified -> refused in production
        ingest_dataset(tmp_path, mp, "production")


def test_template_is_draft_and_ranks_from_audit(tmp_path):
    d = _raw(tmp_path)
    t = make_template(audit_directory(d), "t_ds", "T_DS", "data/raw/t_ds")
    assert t["audit_status"] == "DRAFT" and t["columns"] == {} and t["units"] == {}
    assert t["candidates"]["glucose"][0]["column"] == "glucose"
    assert validate_mapping(t) != []                                  # a draft can never be ingested


def test_combine_namespaces_ids_and_mode_gate(tmp_path):
    _raw(tmp_path); mp = _mapping(tmp_path)
    ingest_dataset(tmp_path, mp, "provisional")
    dst = combine_person_day(tmp_path, mode="provisional")
    df, _ = read_table(dst)
    assert df.person_id.str.startswith("t_ds:").all()
    with pytest.raises(ScientificBlocker):
        combine_person_day(tmp_path, mode="production")
