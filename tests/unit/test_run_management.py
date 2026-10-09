import datetime as dt
import json
import pytest

from iris.common.exceptions import ProvenanceError, ScientificBlocker, TestOnlyDataError
from iris.common.parameters import Parameter, RunMode, Status
from iris.common.provenance import EvidenceClass, Provenance
from iris.common.runs import RunExistsError, make_run_id, start_run
import pandas as pd


def test_parameter_gating():
    p = Parameter("x", 1.0, "u", Status.PENDING_VERIFY)
    assert p.get(RunMode.PROVISIONAL) == 1.0
    with pytest.raises(ScientificBlocker):
        p.get(RunMode.PRODUCTION)
    u = Parameter("y", None, "u", Status.UNRESOLVED, note="extract")
    for m in RunMode:
        with pytest.raises(ScientificBlocker):
            u.get(m)
    assert Parameter("z", 2.0, "u", Status.RESOLVED).get(RunMode.PRODUCTION) == 2.0


def test_run_id_format_and_immutability(tmp_path):
    cfg = {"seed": 1, "a": 2}
    rid = make_run_id(cfg, tmp_path, dt.date(2026, 10, 5))
    d, g, h = rid.split("_")
    assert d == "20261005" and len(h) == 8
    ctx = start_run("EXP", cfg, tmp_path, mode="test", cwd=tmp_path, date=dt.date(2026, 10, 5))
    assert (ctx.dir / "config.yaml").exists() and (ctx.dir / "tables").is_dir() and (ctx.dir / "figures").is_dir()
    ctx.finalize()
    meta = json.loads((ctx.dir / "provenance.json").read_text())["run"]
    assert meta["seed_global"] == 1 and "input_sha256" in meta and meta["stamp"].startswith("TEST")
    with pytest.raises(RunExistsError):
        start_run("EXP", cfg, tmp_path, mode="test", cwd=tmp_path, date=dt.date(2026, 10, 5))
    start_run("EXP", cfg, tmp_path, mode="test", cwd=tmp_path, date=dt.date(2026, 10, 5), restore=True).log.close()
    other = start_run("EXP", {**cfg, "a": 3}, tmp_path, mode="test", cwd=tmp_path, date=dt.date(2026, 10, 5)); other.log.close()
    assert other.run_id != ctx.run_id


def test_production_run_refuses_synthetic_lineage(tmp_path):
    ctx = start_run("EXP", {"seed": 2}, tmp_path, mode="production", cwd=tmp_path)
    prov = Provenance(EvidenceClass.SIMULATED, "TEST_ONLY:x", synthetic=True)
    with pytest.raises(TestOnlyDataError):
        ctx.save_table(pd.DataFrame({"a": [1]}), "t", [prov])
    ctx.log.close()


def test_blocked_run_can_be_rerun_but_completed_run_cannot(tmp_path):
    import datetime as dt
    from iris.common.runs import start_run
    cfg = {"a": 1}
    d = dt.date(2026, 10, 5)
    c1 = start_run("EXP", cfg, tmp_path, mode="test", cwd=tmp_path, date=d); c1.finalize("blocked")
    c2 = start_run("EXP", cfg, tmp_path, mode="test", cwd=tmp_path, date=d); c2.finalize("completed")      # allowed: previous was blocked
    with pytest.raises(RunExistsError):
        start_run("EXP", cfg, tmp_path, mode="test", cwd=tmp_path, date=d)                                   # completed runs stay immutable
