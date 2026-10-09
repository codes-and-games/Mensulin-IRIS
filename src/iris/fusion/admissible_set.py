"""The admissible parameter set  theta = (f, h, eta, ISF_model, s, m, st, r_PB, R_B, d, q)  (document 16A.8).

Theta_E (evidence-constrained) and Theta_S (stress-test) are DISTINCT objects. Components with no
evidence-supported levels are held at their declared reference level in Theta_E and listed in
``conditioned_on`` so every Theta_E conclusion is reported as conditional on those references.
``pool()`` is deliberately absent: the two sets are never merged.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from iris.common.exceptions import IrisError, NumericalError
from iris.common.io import load_yaml

COMPONENTS = ("f", "h", "eta", "isf", "s", "m", "st", "r_PB", "R_B", "d", "q")
CONTINUOUS = ("h", "eta", "st", "r_PB")


@dataclass(frozen=True)
class Theta:
    values: tuple          # aligned with COMPONENTS
    analysis_set: str      # 'E' or 'S'

    def as_dict(self) -> dict:
        return dict(zip(COMPONENTS, self.values))


@dataclass
class AdmissibleSet:
    spec: dict
    search: dict = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "AdmissibleSet":
        raw = load_yaml(path)
        comps = raw["components"]
        missing = [c for c in COMPONENTS if c not in comps]
        if missing:
            raise IrisError(f"admissible_set.yaml missing components {missing}")
        return cls(comps, {k: v for k, v in raw.items() if k != "components"})

    # ---- level sets ----
    def levels(self, which: str) -> dict:
        out = {}
        for c in COMPONENTS:
            d = self.spec[c]
            if c == "q":
                out[c] = [which]
            elif which == "E":
                lv = list(d.get("evidence_levels") or [])
                out[c] = lv if lv else [d["reference"]]
            elif which == "S":
                lv = [d["reference"]] + list(d.get("evidence_levels") or []) + list(d.get("stress_levels") or [])
                out[c] = list(dict.fromkeys(lv))
            else:
                raise NumericalError("analysis set must be 'E' or 'S'")
        return out

    def conditioned_on_E(self) -> list[str]:
        """Components with no evidence-supported level: held at reference in Theta_E (conclusions are conditional on them)."""
        return [c for c in COMPONENTS if c != "q" and not (self.spec[c].get("evidence_levels") or [])]

    def size(self, which: str) -> int:
        return int(np.prod([len(v) for v in self.levels(which).values()]))

    def factorial(self, which: str, max_points: int | None, rng: np.random.Generator) -> tuple[list[Theta], dict]:
        lv = self.levels(which)
        total = self.size(which)
        grid = itertools.product(*[lv[c] for c in COMPONENTS])
        if max_points is None or total <= max_points:
            pts = [Theta(tuple(g), which) for g in grid]
        else:
            idx = set(rng.choice(total, size=max_points, replace=False).tolist())
            pts = [Theta(tuple(g), which) for i, g in enumerate(grid) if i in idx]
        return pts, {"analysis_set": which, "n_total": total, "n_evaluated": len(pts), "subsampled": len(pts) < total}

    def latin_hypercube(self, which: str, n: int, rng: np.random.Generator) -> list[Theta]:
        """LHS over CONTINUOUS components (interval = [min, max] of numeric levels); categorical components are
        drawn uniformly at random. Coverage must be recorded separately for E and S by the caller."""
        lv = self.levels(which)
        u = (np.argsort(rng.random((n, len(COMPONENTS))), axis=0) + rng.random((n, len(COMPONENTS)))) / n
        pts = []
        for i in range(n):
            vals = []
            for k, c in enumerate(COMPONENTS):
                opts = lv[c]
                if c in CONTINUOUS and len(opts) > 1:
                    lo, hi = float(min(opts)), float(max(opts))
                    vals.append(lo + u[i, k] * (hi - lo))
                else:
                    vals.append(opts[min(int(u[i, k] * len(opts)), len(opts) - 1)])
            pts.append(Theta(tuple(vals), which))
        return pts

    def bounds_for_search(self, which: str) -> tuple[list, list]:
        """Per component: ('cont', lo, hi) or ('cat', levels)."""
        lv = self.levels(which)
        return [(c, ("cont", float(min(lv[c])), float(max(lv[c]))) if (c in CONTINUOUS and len(lv[c]) > 1)
                 else ("cat", lv[c])) for c in COMPONENTS]

    def is_in_E(self, theta: Theta) -> bool:
        lv = self.levels("E")
        return all((theta.as_dict()[c] in lv[c]) for c in COMPONENTS if c != "q")


def assert_single_set(thetas: list[Theta]) -> str:
    """Raise if Theta_E and Theta_S points are mixed in one list (they are never silently pooled)."""
    sets = {t.analysis_set for t in thetas}
    if len(sets) != 1:
        raise IrisError(f"mixed analysis sets {sorted(sets)}: Theta_E and Theta_S must be reported separately")
    return sets.pop()


# ---------------------------------------------------------------- classification of a conclusion
@dataclass
class ConclusionResult:
    conclusion_id: str
    analysis_set: str
    classification: str                 # computationally_robust | conditional | unsupported
    n_points: int
    n_hold: int
    n_undefined: int
    conditioned_on: list
    controlling_component: str | None
    flip_levels: dict
    adversary: dict
    note: str = ""


def classify_conclusion(cid: str, which: str, evals: pd.DataFrame, adversary: dict | None, conditioned_on: list[str]) -> ConclusionResult:
    """``evals``: one row per evaluated theta with columns COMPONENTS + 'margin' (>0 holds; NaN undefined) + 'blocked'.

    robust      : every evaluated point holds AND the adversarial search found no counterexample within budget
    conditional : holds on a strict subset (or a counterexample exists); controlling component and flip levels reported
    unsupported : evaluation was blocked by missing evidence, or no point is defined
    """
    adversary = adversary or {}
    if len(evals) and evals["blocked"].all():
        reasons = sorted(set(map(str, evals["blocked_reason"]))) if "blocked_reason" in evals else []
        return ConclusionResult(cid, which, "unsupported", len(evals), 0, 0, conditioned_on, None, {}, adversary,
                                note="; ".join(reasons[:3]))
    ok = evals[~evals["blocked"]]
    margin = ok["margin"].to_numpy(float)
    n_undef = int(np.isnan(margin).sum())
    hold = np.nan_to_num(margin, nan=-np.inf) > 0
    n_hold = int(hold.sum())
    cex_found = bool(adversary.get("counterexample_found", False))
    if len(ok) == 0 or n_undef == len(ok):
        cls = "unsupported"
    elif n_hold == len(ok) and not cex_found:
        cls = "computationally_robust"
    else:
        cls = "conditional"
    controlling, flips = None, {}
    if cls == "conditional" and (~hold).any() and hold.any():
        # controlling component = largest between-level share of the variance of the hold indicator (eta^2);
        # confounds in small subsamples are thereby penalised relative to a true separator.
        h = pd.Series(hold.astype(float), index=ok.index)
        total = float(((h - h.mean()) ** 2).sum())
        best = -1.0
        for c in COMPONENTS:
            if c == "q":
                continue
            grp = h.groupby(ok[c].astype(str))
            between = float((grp.mean().sub(h.mean()) ** 2 * grp.size()).sum())
            eta2 = between / total
            if eta2 > best + 1e-12:
                best, controlling = eta2, c
                flips = {str(k): float(v) for k, v in grp.mean().items() if v < 1.0}
    return ConclusionResult(cid, which, cls, len(ok), n_hold, n_undef, conditioned_on if which == "E" else [],
                            controlling, flips, adversary)
