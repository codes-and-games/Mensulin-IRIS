"""Hashing helpers: file hashes, canonical object hashes, config hashes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

_CHUNK = 1 << 20


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=_default)


def _default(o: Any):
    try:
        import numpy as np

        if isinstance(o, np.generic):
            return o.item()
        if isinstance(o, np.ndarray):
            return o.tolist()
    except ImportError:  # pragma: no cover
        pass
    if isinstance(o, Path):
        return str(o)
    if isinstance(o, (set, frozenset)):
        return sorted(o)
    raise TypeError(f"cannot canonically hash object of type {type(o)!r}")


def sha256_obj(obj: Any) -> str:
    """Hash any JSON-able (or numpy-containing) object canonically."""
    return hashlib.sha256(_canonical(obj).encode("utf-8")).hexdigest()


def config_hash(cfg: dict, length: int = 8) -> str:
    return sha256_obj(cfg)[:length]


def sha256_dataframe(df) -> str:
    """Order-sensitive content hash of a pandas DataFrame (values + column names)."""
    import pandas as pd

    h = hashlib.sha256()
    h.update(",".join(map(str, df.columns)).encode())
    h.update(pd.util.hash_pandas_object(df, index=True).values.tobytes())
    return h.hexdigest()
