"""Analyst-defined plausible kinetic model set (NOT a quantified model-set uncertainty unless
>= 5 comparable studies exist), with pessimistic / optimistic envelopes.

Each ``KineticSpec`` is one (study, model-form) member carrying posterior parameter draws.
Weights are a declared analyst choice (default: uniform across members; K0 weighted by the
number of studies reporting no loss) and are secondary to the envelopes (doc 11.5).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from iris.common.exceptions import NumericalError, ScientificBlocker

from .kinetics.base import KineticModel
from .kinetics.k0 import K0


@dataclass
class KineticSpec:
    study: str
    model_id: str
    #: build(draw_index, rate_scale) -> KineticModel with a multiplicative rate factor applied
    build: Callable[[int, float], KineticModel]
    n_draws: int
    weight: float = 1.0
    source_ids: tuple = ()

    @property
    def is_null(self) -> bool:
        return self.model_id == "K0"


def k0_spec(study: str, source_ids=()) -> KineticSpec:
    return KineticSpec(study, "K0", lambda i, s: K0(), 1, 1.0, tuple(source_ids))


@dataclass
class ModelSet:
    specs: list[KineticSpec]
    comparable_study_count: int = 0

    def __post_init__(self):
        if not self.specs:
            raise ScientificBlocker("kinetic_model_set", "no kinetic specifications supplied",
                                    "run L2 extraction/fitting for >= 1 comparable study")

    @property
    def between_study_variance_estimable(self) -> bool:
        return self.comparable_study_count >= 5

    def weights(self) -> np.ndarray:
        w = np.array([max(s.weight, 0.0) for s in self.specs], float)
        if w.sum() <= 0:
            raise NumericalError("kinetic model weights sum to zero")
        return w / w.sum()

    def sample_member(self, rng: np.random.Generator) -> int:
        return int(rng.choice(len(self.specs), p=self.weights()))

    def subset(self, study: str | None = None, model_id: str | None = None) -> "ModelSet":
        sel = [s for s in self.specs if (study is None or s.study == study) and (model_id is None or s.model_id == model_id)]
        return ModelSet(sel, self.comparable_study_count)

    def envelope(self, history_c: np.ndarray, dt_days: float, rng: np.random.Generator, n: int = 200):
        """(pessimistic, optimistic) member by median potency under a reference history."""
        med = []
        for s in self.specs:
            ps = [float(s.build(int(rng.integers(0, s.n_draws)), 1.0).potency(history_c, dt_days)[0]) for _ in range(n)]
            med.append(np.median(ps))
        return self.specs[int(np.argmin(med))], self.specs[int(np.argmax(med))]


def uniform_weights_with_null_by_count(specs: list[KineticSpec], n_null_studies: int) -> None:
    """Declared default: non-null members equal weight 1 each; K0 weight = number of null-finding studies."""
    for s in specs:
        s.weight = float(max(n_null_studies, 0)) if s.is_null else 1.0
