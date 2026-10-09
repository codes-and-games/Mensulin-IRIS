"""Cycle-time representations (document 9.1-9.2): day, normalised position, two-anchor position, backward
position, harmonic encoding, and phase labels from EXPLICIT day windows (the windows are [TO EXTRACT]; no defaults)."""
from __future__ import annotations

import numpy as np

from iris.common.exceptions import NumericalError, ScientificBlocker


def normalised_position(day, cycle_len):
    d, L = np.asarray(day, float), np.asarray(cycle_len, float)
    if np.any(d < 1) or np.any(L < 1) or np.any(d > L):
        raise NumericalError("need 1 <= day <= cycle_len")
    return (d - 1.0) / L


def two_anchor_position(day, cycle_len, ovulation_day):
    """Piecewise: follicular u = (d-1)/(O-1); luteal v = (d-O)/(L-O+1). Returns (segment, position in [0,1])."""
    d, L, O = (np.asarray(v, float) for v in (day, cycle_len, ovulation_day))
    if np.any(O <= 1) or np.any(O > L):
        raise NumericalError("ovulation day must satisfy 1 < O <= L")
    foll = d < O
    pos = np.where(foll, (d - 1.0) / (O - 1.0), (d - O) / (L - O + 1.0))
    return np.where(foll, "follicular", "luteal"), pos


def backward_position(day, cycle_len):
    return np.asarray(cycle_len, float) - np.asarray(day, float)


def harmonic_features(x, K: int = 2):
    """[cos(k phi), sin(k phi)]_{k=1..K}, phi = 2 pi x. Continuous across cycle boundaries."""
    phi = 2 * np.pi * np.asarray(x, float)
    cols = []
    for k in range(1, K + 1):
        cols += [np.cos(k * phi), np.sin(k * phi)]
    return np.column_stack(cols)


def phase_from_windows(day, cycle_len, ovulation_day, windows: dict | None):
    """Assign six-phase labels from extracted day windows (relative to anchors). ``windows=None`` => blocked."""
    if windows is None:
        raise ScientificBlocker("phase_day_windows", "[TO EXTRACT] exact day windows of the anchor study",
                                "extract windows and the ovulation-estimation method from the anchor study methods")
    raise NotImplementedError("window schema depends on the extracted definition; implement once windows are registered")
