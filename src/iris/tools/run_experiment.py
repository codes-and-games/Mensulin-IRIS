"""Run an experiment by ID:  python -m iris.tools.run_experiment F1_central [--mode provisional|production|test].

Each experiments/<ID>/ directory contains README.md, config.yaml, run.py (exposing ``run(ctx)``),
expected_outputs.md. A ScientificBlocker raised by a dependent computation is recorded in the run (status
'blocked') and reported; it is never converted into a default value.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

from iris.common.exceptions import ScientificBlocker
from iris.common.io import load_yaml
from iris.common.parameters import RunMode
from iris.common.runs import start_run

ROOT = Path(__file__).resolve().parents[3]


def find_experiment(exp_id: str, root: Path = ROOT) -> Path:
    cands = sorted((root / "experiments").glob(f"{exp_id}*"))
    cands = [c for c in cands if (c / "run.py").exists()]
    if not cands:
        raise FileNotFoundError(f"no experiment matching {exp_id!r}")
    return cands[0]


def deep_merge(a: dict, b: dict) -> dict:
    out = dict(a)
    for k, v in b.items():
        out[k] = deep_merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def run_experiment(exp_id: str, mode: str = "provisional", root: Path = ROOT, cfg_override: dict | None = None,
                   runs_root: Path | None = None, smoke: bool = False):
    """``smoke=True`` merges the experiment's ``smoke:`` block (reduced sizes for plumbing checks). Smoke runs are
    recorded as such in the config (and hence the run_id) and are never production results."""
    exp_dir = find_experiment(exp_id, root)
    base = load_yaml(root / "configs/base.yaml")
    ecfg = load_yaml(exp_dir / "config.yaml")
    smoke_cfg = ecfg.pop("smoke", {})
    cfg = deep_merge({**base, **ecfg}, smoke_cfg if smoke else {})
    cfg = deep_merge(cfg, cfg_override or {})
    cfg["smoke"] = bool(smoke)
    cfg["_repo_root"] = str(root)
    ctx = start_run(exp_dir.name, {k: v for k, v in cfg.items() if not k.startswith("_")},
                    runs_root or (root / base["paths"]["runs"]), mode=mode, cwd=root)
    ctx.cfg["_repo_root"] = str(root)
    spec = importlib.util.spec_from_file_location(f"iris_exp_{exp_dir.name}", exp_dir / "run.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    try:
        mod.run(ctx)
        ctx.finalize("completed")
    except ScientificBlocker as exc:
        ctx.log.warn(str(exc))
        ctx.finalize("blocked", {"blocker": {"parameter": exc.parameter, "reason": exc.reason, "needed": exc.needed}})
        print(f"[{exp_dir.name}] BLOCKED: {exc}")
        return ctx
    except Exception as exc:
        ctx.log.warn(f"failure: {exc!r}")
        ctx.finalize("failed", {"error": repr(exc)})
        raise
    print(f"[{exp_dir.name}] completed run_id={ctx.run_id}")
    return ctx


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("experiment")
    ap.add_argument("--mode", default=None, choices=["production", "provisional", "test"])
    ap.add_argument("--smoke", action="store_true", help="reduced sizes (plumbing check; not a scientific result)")
    args = ap.parse_args(argv)
    base = load_yaml(ROOT / "configs/base.yaml")
    ctx = run_experiment(args.experiment, args.mode or base.get("run_mode", "provisional"), smoke=args.smoke)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
