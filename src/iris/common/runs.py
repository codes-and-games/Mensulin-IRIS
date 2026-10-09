"""Immutable run directories:  results/runs/<run_id>/{config.yaml, provenance.json, log.txt, tables/, figures/}.

run_id = UTC date + short git hash + config hash. Runs are never overwritten: re-creating an existing
run_id raises unless ``restore=True`` AND the stored config hash matches (exact reproducible restore).
"""
from __future__ import annotations

import datetime as _dt
import json
import platform
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from .exceptions import IrisError, ProvenanceError
from .hashing import config_hash, sha256_file
from .io import dump_yaml, write_table
from .logging import RunLogger
from .parameters import RunMode
from .provenance import Provenance, assert_production_safe, write_provenance
from .rng import RngTree


class RunExistsError(IrisError):
    pass


def git_short_hash(cwd: str | Path = ".") -> str:
    """Short commit hash; if the working tree has uncommitted changes, '+<hash of the diff>' is appended so a run
    made from modified code can never collide with (or be mistaken for) a run from the clean commit."""
    try:
        out = subprocess.run(["git", "rev-parse", "--short=7", "HEAD"], cwd=cwd, capture_output=True, text=True, timeout=10)
        h = out.stdout.strip()
        if out.returncode != 0 or not h:
            return "nogit"
        # modified AND untracked files under code/config dirs (git diff alone misses new untracked files)
        ls = subprocess.run(["git", "ls-files", "-m", "-o", "--exclude-standard", "--", "src", "configs", "experiments", "docs/prereg"],
                            cwd=cwd, capture_output=True, text=True, timeout=30).stdout.split()
        if ls:
            import hashlib
            hh = hashlib.sha256()
            for f in sorted(ls):
                fp = Path(cwd) / f
                hh.update(f.encode()); hh.update(fp.read_bytes() if fp.is_file() else b"<deleted>")
            return f"{h}+{hh.hexdigest()[:6]}"
        return h
    except Exception:  # pragma: no cover
        return "nogit"


def software_versions() -> dict:
    import scipy, pandas, yaml
    v = {"python": sys.version.split()[0], "numpy": np.__version__, "scipy": scipy.__version__,
         "pandas": pd.__version__, "platform": platform.platform()}
    try:
        import pyarrow; v["pyarrow"] = pyarrow.__version__
    except ImportError:  # pragma: no cover
        pass
    return v


def make_run_id(cfg: dict, cwd: str | Path = ".", date: _dt.date | None = None) -> str:
    d = (date or _dt.datetime.now(_dt.timezone.utc).date()).strftime("%Y%m%d")
    return f"{d}_{git_short_hash(cwd)}_{config_hash(cfg)}"


@dataclass
class RunContext:
    run_id: str
    experiment: str
    cfg: dict
    root: Path
    mode: RunMode
    rng: RngTree
    log: RunLogger
    provenance: list = field(default_factory=list)
    input_files: dict = field(default_factory=dict)
    started: str = ""
    outputs: dict = field(default_factory=dict)
    blockers: list = field(default_factory=list)   # partial scientific blockers (dependent parts only)

    @property
    def dir(self) -> Path: return self.root / self.run_id
    @property
    def tables(self) -> Path: return self.dir / "tables"
    @property
    def figures(self) -> Path: return self.dir / "figures"

    def add_input(self, path: str | Path) -> str:
        h = sha256_file(path); self.input_files[str(path)] = h; return h

    def save_table(self, df: pd.DataFrame, name: str, prov: list[Provenance], schema=None, evidence_class: str | None = None) -> Path:
        """Write a parquet table + provenance sidecar into the run; counts evidence classes."""
        if self.mode is RunMode.PRODUCTION:
            assert_production_safe(prov)
        p = self.tables / f"{name}.parquet"
        write_table(df, p, prov, schema)
        for pr in prov:
            self.log.count_evidence(pr.evidence_class.value)
        self.provenance.extend(prov)
        self.outputs[name] = str(p.relative_to(self.dir))
        return p

    def finalize(self, status: str = "completed", extra: dict | None = None) -> None:
        end = _dt.datetime.now(_dt.timezone.utc).isoformat()
        meta = {"run_id": self.run_id, "experiment": self.experiment, "status": status, "started_utc": self.started,
                "ended_utc": end, "seed_global": self.rng.seed_global, "git_hash": git_short_hash(self.root.parent.parent if self.root.name == "runs" else "."),
                "config_hash": config_hash(self.cfg), "run_mode": self.mode.value, "input_sha256": self.input_files,
                "software": software_versions(), "warnings": self.log.warnings, "exclusions": self.log.exclusions,
                "evidence_class_counts": dict(self.log.evidence_counts), "outputs": self.outputs,
                "partial_blockers": self.blockers}
        if self.mode is not RunMode.PRODUCTION:
            meta["stamp"] = f"{self.mode.value.upper()} RUN: not a production scientific result"
        if extra:
            meta.update(extra)
        write_provenance(self.dir / "provenance.json", self.provenance, extra=meta)
        self.log.info(f"run {status}")
        self.log.close()


def start_run(experiment: str, cfg: dict, root: str | Path = "results/runs", *, mode: RunMode | str = RunMode.PROVISIONAL,
              restore: bool = False, cwd: str | Path = ".", date: _dt.date | None = None) -> RunContext:
    mode = RunMode(mode)
    cfg = dict(cfg)
    run_id = make_run_id({**cfg, "experiment": experiment, "run_mode": mode.value}, cwd, date)
    root = Path(root)
    d = root / run_id
    if d.exists() and not restore:
        # A BLOCKED/FAILED run is not a result: it produced no tables worth keeping and would otherwise stop the same experiment
        # from being re-run the same day once the missing input has been supplied (run ids hash the config, not the inputs).
        prov = d / "provenance.json"
        if prov.exists() and json.loads(prov.read_text()).get("run", {}).get("status") in ("blocked", "failed"):
            import shutil
            shutil.rmtree(d)
    if d.exists():
        if not restore:
            raise RunExistsError(f"run {run_id} already exists; runs are immutable (use restore=True to verify an exact restore)")
        old = json.loads((d / "provenance.json").read_text()).get("run", {}) if (d / "provenance.json").exists() else {}
        if old.get("config_hash") != config_hash(cfg):
            raise ProvenanceError("restore requested but stored config hash differs")
    (d / "tables").mkdir(parents=True, exist_ok=True)
    (d / "figures").mkdir(exist_ok=True)
    dump_yaml({**cfg, "experiment": experiment, "run_mode": mode.value}, d / "config.yaml")
    log = RunLogger(d / "log.txt")
    started = _dt.datetime.now(_dt.timezone.utc).isoformat()
    log.info(f"start run {run_id} experiment={experiment} mode={mode.value}")
    seed = int(cfg.get("seed", cfg.get("seed_global", 0)))
    return RunContext(run_id, experiment, cfg, root, mode, RngTree(seed), log, started=started)
