"""Reproducible, independent random streams.

Every stochastic function in IRIS receives a ``numpy.random.Generator``.
Streams are derived by NAME from one global seed through ``SeedSequence`` spawn keys,
so adding draws to one component, or adding a new component, never perturbs the
stream of any other component (unlike sequential ``spawn()``, which is order-dependent).
"""
from __future__ import annotations

import hashlib

import numpy as np


def _name_key(name: str) -> int:
    """Stable 32-bit key for a stream name (independent of Python hash randomisation)."""
    return int.from_bytes(hashlib.sha256(name.encode("utf-8")).digest()[:4], "big")


class RngTree:
    """Named hierarchy of independent generators derived from ``seed_global``."""

    def __init__(self, seed_global: int, path: tuple[int, ...] = ()):
        if not isinstance(seed_global, (int, np.integer)) or seed_global < 0:
            raise ValueError("seed_global must be a non-negative integer")
        self.seed_global = int(seed_global)
        self._path = tuple(path)

    def child(self, *names: str) -> "RngTree":
        return RngTree(self.seed_global, self._path + tuple(_name_key(n) for n in names))

    def seed_sequence(self) -> np.random.SeedSequence:
        return np.random.SeedSequence(entropy=self.seed_global, spawn_key=self._path)

    def generator(self, *names: str) -> np.random.Generator:
        """Return a fresh Generator for ``names``; same names => identical stream."""
        node = self.child(*names) if names else self
        return np.random.Generator(np.random.PCG64(node.seed_sequence()))

    def indexed(self, name: str, index: int) -> np.random.Generator:
        """Generator for the ``index``-th member of a family (e.g. epistemic draw j)."""
        return self.generator(name, f"#{int(index)}")
