"""Extended Kalman filter for the T4 model. Hand-written and transparent (document: small state, testable).

Process noise Q: diagonal; lnS gets ``q``, E gets ``qE``, glucose gets ``q_g`` (model error), others ``q_small``.
Observation noise R: scalar ``r`` (CGM). Initial state x0, covariance P0 are explicit inputs.
Missing CGM (NaN): prediction only; no spurious update.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .glucose_insulin_model import IDX, N_STATE, ModelConstants, jacobian, observation_matrix, transition


@dataclass(frozen=True)
class NoiseSpec:
    q_lns: float
    q_e: float
    q_g: float
    q_small: float
    r: float

    def Q(self) -> np.ndarray:
        q = np.full(N_STATE, self.q_small)
        q[IDX["lnS"]], q[IDX["E"]], q[IDX["G"]] = self.q_lns, self.q_e, self.q_g
        return np.diag(q)


@dataclass
class FilterResult:
    x_pred: np.ndarray      # (T, n) prior at each step
    P_pred: np.ndarray
    x_filt: np.ndarray      # (T, n) posterior
    P_filt: np.ndarray
    F: np.ndarray           # (T, n, n) Jacobians used for the transition INTO step t
    innovations: np.ndarray  # (T,) NaN where missing
    innov_var: np.ndarray
    loglik: float


def run_ekf(cgm: np.ndarray, u: np.ndarray, carb: np.ndarray, k: ModelConstants, noise: NoiseSpec,
            x0: np.ndarray, P0: np.ndarray) -> FilterResult:
    T = len(cgm)
    H, Q = observation_matrix(), noise.Q()
    xp, Pp = np.empty((T, N_STATE)), np.empty((T, N_STATE, N_STATE))
    xf, Pf = np.empty((T, N_STATE)), np.empty((T, N_STATE, N_STATE))
    Fs = np.empty((T, N_STATE, N_STATE))
    innov, ivar = np.full(T, np.nan), np.full(T, np.nan)
    x, P, ll = x0.copy(), P0.copy(), 0.0
    for t in range(T):
        if t == 0:
            F, xpred, Ppred = np.eye(N_STATE), x, P
        else:
            F = jacobian(xf[t - 1], k)
            xpred = transition(xf[t - 1], u[t - 1], carb[t - 1], k)
            xpred[:4] = np.maximum(xpred[:4], 0.0)                     # non-negativity of compartments
            Ppred = F @ Pf[t - 1] @ F.T + Q
        Fs[t], xp[t], Pp[t] = F, xpred, Ppred
        if np.isfinite(cgm[t]):
            y = cgm[t] - (H @ xpred)[0]
            S_ = float((H @ Ppred @ H.T)[0, 0] + noise.r)
            K = (Ppred @ H.T) / S_
            xf[t] = xpred + (K[:, 0] * y)
            Pf[t] = (np.eye(N_STATE) - K @ H) @ Ppred
            Pf[t] = 0.5 * (Pf[t] + Pf[t].T)
            innov[t], ivar[t] = y, S_
            ll += -0.5 * (np.log(2 * np.pi * S_) + y * y / S_)
        else:
            xf[t], Pf[t] = xpred, Ppred
    return FilterResult(xp, Pp, xf, Pf, Fs, innov, ivar, float(ll))
