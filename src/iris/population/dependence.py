"""Within-biology dependence object R_B and non-normal stress-test families.

Latent standardized Gaussian vector u = (u_tdd, u_sens, u_gamma) ~ N(0, R_B).
  ln TDD  <- u_tdd           (lognormal margin)
  z       <- Q_f(Phi(u_sens)) (unit-variance, zero-mean margin of family f; Gaussian copula)
  gamma-amplitude heterogeneity <- u_gamma
R_B entries are evidence-constrained only if a source identifies them; otherwise they belong to
the stress-test set and are labelled so. Nothing here supplies a convenient default correlation
other than the identity (independence), which is itself a declared reference assumption.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats

from iris.common.exceptions import NumericalError

LATENTS = ("tdd", "sens", "gamma")


@dataclass(frozen=True)
class BiologicalDependence:
    corr: np.ndarray            # 3x3 over LATENTS
    status: str = "REFERENCE_INDEPENDENCE"   # or STRESS_TEST / EVIDENCE
    label: str = "independent"

    def __post_init__(self):
        c = np.asarray(self.corr, float)
        if c.shape != (3, 3) or not np.allclose(c, c.T) or not np.allclose(np.diag(c), 1.0):
            raise NumericalError("R_B must be a symmetric 3x3 correlation matrix with unit diagonal")
        if np.linalg.eigvalsh(c).min() < 1e-9:
            raise NumericalError("R_B must be positive definite")
        object.__setattr__(self, "corr", c)

    @classmethod
    def independent(cls) -> "BiologicalDependence":
        return cls(np.eye(3))

    @classmethod
    def from_pairs(cls, pairs: dict, status: str, label: str) -> "BiologicalDependence":
        c = np.eye(3)
        for (a, b), r in pairs.items():
            i, j = LATENTS.index(a), LATENTS.index(b)
            c[i, j] = c[j, i] = r
        return cls(c, status, label)

    def draw_latents(self, rng: np.random.Generator, n: int) -> np.ndarray:
        L = np.linalg.cholesky(self.corr)
        return rng.standard_normal((n, 3)) @ L.T


def standardized_margin(family: str, opts: dict | None = None):
    """Return a function mapping standard-normal u -> zero-mean, unit-variance z for family f.

    families: 'normal', 'student_t_<nu>' (nu>2), 'skewnormal_<alpha>', 'mixture_<pi>' (two-component
    normal mixture; minority shifted by ``opts['mixture_shift_sd']`` and re-standardised so mean=0, sd=1).
    All non-normal families are STRESS-TEST completions of unidentified tails.
    """
    opts = opts or {}
    if family == "normal":
        return lambda u: np.asarray(u, float)
    kind, _, par = family.partition("_")
    if family.startswith("student_t_"):
        nu = float(family.split("_")[-1])
        if nu <= 2:
            raise NumericalError("Student-t needs nu > 2 for unit variance")
        sd = np.sqrt(nu / (nu - 2.0))
        return lambda u: stats.t.ppf(stats.norm.cdf(u), nu) / sd
    if family.startswith("skewnormal_"):
        a = float(family.split("_")[-1])
        mean, var = stats.skewnorm.mean(a), stats.skewnorm.var(a)
        return lambda u: (stats.skewnorm.ppf(np.clip(stats.norm.cdf(u), 1e-12, 1 - 1e-12), a) - mean) / np.sqrt(var)
    if family.startswith("mixture_"):
        pi = float(family.split("_")[-1])
        if "mixture_shift_sd" not in opts:
            from iris.common.exceptions import ScientificBlocker
            raise ScientificBlocker("mixture_shift_sd", "mixture minority shift not declared in config",
                                    "declare analyst stress level in configs/fusion/admissible_set.yaml")
        delta, w = float(opts["mixture_shift_sd"]), pi
        mu = w * delta
        var = 1.0 + w * (1 - w) * delta ** 2      # unit-variance components, shifted minority
        grid = np.linspace(-12, 12 + delta, 40001)
        cdf = (1 - w) * stats.norm.cdf(grid) + w * stats.norm.cdf(grid - delta)
        def q(u):
            p = np.clip(stats.norm.cdf(u), 1e-12, 1 - 1e-12)
            return (np.interp(p, cdf, grid) - mu) / np.sqrt(var)
        return q
    raise NumericalError(f"unknown family '{family}'")
