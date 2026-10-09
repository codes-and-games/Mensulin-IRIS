"""Climate-source access (registered files only) and E1 cross-source agreement metrics.

``load_registered_series`` refuses any file that is not in the manifest with a verified source (production) —
NO SOURCE, NO NUMBER. Agreement metrics are pure functions tested on synthetic arrays.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from iris.common.exceptions import NumericalError
from iris.common.parameters import RunMode
from iris.common.registry import SourceRegistry


def load_registered_series(path: str | Path, registry: SourceRegistry, mode: RunMode, root: str | Path = ".") -> pd.DataFrame:
    p = Path(path)
    if mode is RunMode.TEST:
        return pd.read_csv(p)
    registry.require_file(p, root)       # raises unless in manifest + hash OK + source row verified
    return pd.read_csv(p) if p.suffix == ".csv" else pd.read_parquet(p)


def align_sources(a: pd.Series, b: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    """Inner-join on the (UTC) index; refuses silently misaligned conventions (no overlap)."""
    j = pd.concat([a.rename("a"), b.rename("b")], axis=1, join="inner").dropna()
    if j.empty:
        raise NumericalError("no overlapping timestamps: check units, timezone convention and period")
    return j["a"].to_numpy(float), j["b"].to_numpy(float)


def agreement_metrics(a: np.ndarray, b: np.ndarray) -> dict:
    d = a - b
    return {"n": int(len(a)), "mean_diff": float(d.mean()), "rmse": float(np.sqrt(np.mean(d ** 2))),
            "corr": float(np.corrcoef(a, b)[0, 1]) if np.std(a) > 0 and np.std(b) > 0 else float("nan"),
            "sd_diff": float(d.std(ddof=1)) if len(d) > 1 else float("nan")}


def cross_source_sigma(series: dict[str, pd.Series], sigma_val: float | None) -> dict:
    """Cross-source SD at each time (variance across sources) and sigma_data = sqrt(sigma_cross^2 + sigma_val^2).
    ``sigma_val`` (published validation uncertainty vs ground truth) is a REQUIRED registered input: None => blocked."""
    from iris.common.exceptions import ScientificBlocker
    if sigma_val is None:
        raise ScientificBlocker("sigma_val", "published validation uncertainty not extracted (source S36)", "extract from validation studies")
    df = pd.concat(series, axis=1, join="inner").dropna()
    if df.shape[1] < 2 or df.empty:
        raise NumericalError("need >= 2 overlapping sources")
    cross = float(np.sqrt(df.var(axis=1, ddof=1).mean()))
    return {"sigma_cross": cross, "sigma_val": float(sigma_val), "sigma_data": float(np.hypot(cross, sigma_val)), "n_sources": int(df.shape[1])}
