"""S3 checks: does the virtual population reproduce declared published moments (document 14.6)?

Each check returns PASS / FAIL / BLOCKED. A target that is unresolved yields BLOCKED, never PASS.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .generator import phase_matrix


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str            # PASS | FAIL | BLOCKED
    observed: float | None
    target: float | None
    tolerance: str
    note: str = ""

    def as_row(self) -> dict:
        return dict(check=self.name, status=self.status, observed=self.observed, target=self.target,
                    tolerance=self.tolerance, note=self.note)


def _cmp(name, obs, tgt, tol_abs=None, tol_rel=None, note="", applicable=True):
    if not applicable:
        return CheckResult(name, "NOT_APPLICABLE", float(obs), tgt, "-", note or "target defined only at the reference setting")
    if tgt is None:
        return CheckResult(name, "BLOCKED", obs, None, "target unresolved", note)
    ok = (abs(obs - tgt) <= tol_abs) if tol_abs is not None else (abs(obs - tgt) <= tol_rel * abs(tgt))
    tol = f"abs {tol_abs}" if tol_abs is not None else f"rel {tol_rel:.0%}"
    return CheckResult(name, "PASS" if ok else "FAIL", float(obs), float(tgt), tol, note)


def run_checks(df: pd.DataFrame, targets: dict, tdd_tol_rel=0.02, cycle_tol_d=0.1, concord_tol=0.02) -> pd.DataFrame:
    """``targets`` keys: tdd_mean, tdd_sd, cycle_mean, cycle_sd, concordance, sens_ef, sens_ml (None => BLOCKED)."""
    S = phase_matrix(df, "S_p")
    res = [
        _cmp("tdd_mean", df.tdd_u.mean(), targets.get("tdd_mean"), tol_rel=tdd_tol_rel),
        _cmp("tdd_sd", df.tdd_u.std(ddof=1), targets.get("tdd_sd"), tol_rel=tdd_tol_rel),
        _cmp("cycle_mean", df.cycle_len.mean(), targets.get("cycle_mean"), tol_abs=cycle_tol_d),
        _cmp("cycle_sd", df.cycle_len.std(ddof=1), targets.get("cycle_sd"), tol_abs=cycle_tol_d),
        _cmp("sens_early_follicular_mean", S[:, 0].mean(), targets.get("sens_ef"), tol_abs=0.01,
             note="published population contrast; compare against its credible interval separately"),
        _cmp("sens_midluteal_mean", S[:, 4].mean(), targets.get("sens_ml"), tol_abs=0.01),
        _cmp("concordance_with_population_direction", float((S[:, 0] > S[:, 4]).mean()), targets.get("concordance"),
             tol_abs=concord_tol, note="reference-assumption calibrated; not evidence of tails",
             applicable=bool(targets.get("concordance_applies", True))),
        CheckResult("cycle_mean_of_S_equals_1", "PASS" if np.allclose(S.mean(axis=1), 1.0) else "FAIL",
                    float(S.mean(axis=1).mean()), 1.0, "abs 1e-9"),
        CheckResult("cycle_mean_of_rho_equals_1",
                    "PASS" if np.allclose(phase_matrix(df, "rho_p").mean(axis=1), 1.0) else "FAIL", None, 1.0, "abs 1e-9"),
    ]
    return pd.DataFrame([r.as_row() for r in res])


def sensitivity_requirement_correlation(df: pd.DataFrame) -> float:
    """Diagnostic: corr(ln S, ln rho) pooled over phases (published value unresolved => reported, not tested)."""
    S, R = phase_matrix(df, "S_p"), phase_matrix(df, "rho_p")
    return float(np.corrcoef(np.log(S).ravel(), np.log(R).ravel())[0, 1])


def dependence_diagnostics(df: pd.DataFrame) -> dict:
    """Corr(TDD, sigma_cycle), Corr(TDD, S_contrast), Corr(TDD, gamma_contrast), Corr(S, gamma), Corr(TDD, rho)."""
    S, G, Rho = (phase_matrix(df, p) for p in ("S_p", "gamma_p", "rho_p"))
    tdd = np.log(df.tdd_u.to_numpy())
    s_contrast = np.log(S.max(1) / S.min(1))
    g_contrast = np.log(G.max(1) / G.min(1))
    sigma_cycle = np.log(df.swing_unit.to_numpy())
    c = lambda a, b: float(np.corrcoef(a, b)[0, 1]) if np.std(a) > 0 and np.std(b) > 0 else float("nan")
    return {"corr_tdd_sigma_cycle": c(tdd, sigma_cycle), "corr_tdd_S_contrast": c(tdd, s_contrast),
            "corr_tdd_gamma_contrast": c(tdd, g_contrast), "corr_S_gamma": c(s_contrast, g_contrast),
            "corr_tdd_rho": c(tdd, np.log(Rho).std(axis=1))}
