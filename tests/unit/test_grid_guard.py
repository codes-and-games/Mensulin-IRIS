import numpy as np
import pandas as pd
import pytest

from iris.common.exceptions import ScientificBlocker
from iris.tools.inspect_grid import spacing


def test_spacing_reports_native_interval():
    t = pd.date_range("2026-01-01", periods=100, freq="15min")
    assert spacing(pd.Series(t))["median_min"] == 15.0


def test_load_events_rejects_grid_mismatch(tmp_path, monkeypatch):
    from iris.common.io import write_table
    from iris.common.parameters import RunMode
    from iris.common.provenance import EvidenceClass, Provenance
    from iris.tools import experiment_lib as xl

    ev = pd.DataFrame({"person_id": "p", "ts_local": pd.date_range("2026-01-01", periods=50, freq="15min"), "glucose_mgdl": 120.0})
    p = tmp_path / "data/processed/dsx/events_grid.parquet"
    write_table(ev, p, [Provenance(EvidenceClass.COMPUTED, "person_day:dsx", generated_by="t")], extra={"run_mode": "production"})

    class Ctx:
        mode = RunMode.PRODUCTION
        cfg = {
            "grid_minutes": 5,
            "_repo_root": str(tmp_path),
            "paths": {
                "manifest": "data/manifest.csv",
                "registry": "data/sources_registry.csv",
            },
        }

        def add_input(self, path):
            pass
    monkeypatch.setattr(xl, "repo", lambda ctx: tmp_path)
    with pytest.raises(ScientificBlocker, match="15 min"):
        xl.load_events(Ctx(), "dsx")
