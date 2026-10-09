"""Vial thermal lag (lumped capacitance) and its verification solvers.

Model:  dTv/dt = (Tair - Tv) / tau,   tau = m*cp / (U*A)            [IRIS doc 12.8]
Exact step for piecewise-constant air temperature (doc 13.2):
        Tv[n+1] = Ta[n] + (Tv[n] - Ta[n]) * exp(-dt / tau)

This module models thermal inertia only. It does NOT model insulin behaviour.
"""
from __future__ import annotations

import numpy as np
from scipy.linalg import solve_banded
from scipy.signal import lfilter

from iris.common.exceptions import NumericalError

BIOT_LUMPED_LIMIT = 0.1


def tau_lumped_s(m_cp_j_per_k: float, u_w_m2k: float, area_m2: float) -> float:
    """tau = m*cp / (U*A) in seconds."""
    if m_cp_j_per_k <= 0 or u_w_m2k <= 0 or area_m2 <= 0:
        raise NumericalError("m*cp, U and A must be positive")
    return m_cp_j_per_k / (u_w_m2k * area_m2)


def biot_number(u_w_m2k: float, volume_m3: float, area_m2: float, k_w_mk: float) -> float:
    """Bi = U * L / k with L = V / A (characteristic length)."""
    if min(u_w_m2k, volume_m3, area_m2, k_w_mk) <= 0:
        raise NumericalError("U, V, A and k must be positive")
    return u_w_m2k * (volume_m3 / area_m2) / k_w_mk


def lumped_valid(bi: float) -> bool:
    return bi < BIOT_LUMPED_LIMIT


def analytic_step_response(t_s, t_air_final: float, tv0: float, tau_s: float):
    """Tv(t) after a step in air temperature from the vial's initial temperature tv0."""
    t = np.asarray(t_s, dtype=float)
    if tau_s < 0:
        raise NumericalError("tau must be >= 0")
    if tau_s == 0:
        return np.full_like(t, t_air_final)
    return t_air_final + (tv0 - t_air_final) * np.exp(-t / tau_s)


def exponential_integrator(t_air, dt_s: float, tau_s, tv0=None, output: str = "mean"):
    """Exact-exponential vial temperature for piecewise-constant air temperature.

    ``t_air``: shape (T,) or (D, T) (D parallel draws); sample n holds over [t_n, t_n + dt).
    ``tau_s``: scalar or shape (D,). ``tv0``: initial vial temperature (default: first air value).

    output='edge' : Tv at the START of each interval (point values of the exact solution; used to
                    verify against the analytic step response and the finite-volume solver).
    output='mean' : exact MEAN vial temperature over each interval (default; this is what the hazard
                    integral uses). Tbar_n = Ta_n + (Tv_n - Ta_n) * (tau/dt) * (1 - exp(-dt/tau)),
                    which tends to Ta_n as tau -> 0 (no spurious one-step lag) and to Tv_n as tau -> inf.
    tau == 0 returns the air series exactly (tau -> 0 limit).
    """
    if output not in ("mean", "edge"):
        raise NumericalError("output must be 'mean' or 'edge'")
    x = np.atleast_2d(np.asarray(t_air, dtype=float))
    if not np.isfinite(x).all():
        raise NumericalError("non-finite air temperature")
    d, n = x.shape
    tau = np.broadcast_to(np.asarray(tau_s, dtype=float), (d,)).copy()
    if (tau < 0).any() or dt_s <= 0:
        raise NumericalError("tau must be >= 0 and dt > 0")
    v0 = x[:, 0] if tv0 is None else np.broadcast_to(np.asarray(tv0, dtype=float), (d,))
    out = np.empty_like(x)
    for i in range(d):
        if tau[i] == 0.0:
            out[i] = x[i]
            continue
        a = float(np.exp(-dt_s / tau[i]))
        # y[n] = a*y[n-1] + (1-a)*x[n-1], y[0] = v0  (transposed direct form II, zi = [v0])
        edge = lfilter([0.0, 1.0 - a], [1.0, -a], x[i], zi=[v0[i]])[0]
        if output == "edge":
            out[i] = edge
        else:
            g = (tau[i] / dt_s) * (1.0 - a)
            out[i] = x[i] + (edge - x[i]) * g
    return out if np.ndim(t_air) == 2 else out[0]


def finite_volume_cylinder(t_air, dt_s: float, *, radius_m: float, rho_kg_m3: float, cp_j_kgk: float,
                           k_w_mk: float, h_w_m2k: float, tv0: float | None = None, n_cells: int = 60):
    """Independent radial-conduction solution in a cylinder with a convective boundary.

    Implicit (backward Euler) finite-volume scheme. Returns the VOLUME-AVERAGED liquid
    temperature at each sample, for comparison with the lumped model whose time constant is
    tau = rho*cp*R / (2*h) (cylinder side wall, V/A = R/2). SIMULATED verification only.
    """
    x = np.asarray(t_air, dtype=float)
    if min(radius_m, rho_kg_m3, cp_j_kgk, k_w_mk, h_w_m2k, dt_s) <= 0:
        raise NumericalError("all physical parameters must be positive")
    n = int(n_cells)
    dr = radius_m / n
    r_face = np.linspace(0.0, radius_m, n + 1)
    r_cell = 0.5 * (r_face[:-1] + r_face[1:])
    vol = np.pi * (r_face[1:] ** 2 - r_face[:-1] ** 2)  # per unit length
    cap = rho_kg_m3 * cp_j_kgk * vol
    g = np.zeros(n + 1)  # conductances between cells (face i between cell i-1 and i)
    g[1:n] = 2.0 * np.pi * r_face[1:n] * k_w_mk / dr
    g_wall = 2.0 * np.pi * radius_m * h_w_m2k * 1.0  # convective conductance to air (per unit length)
    # Include the half-cell conduction resistance to the wall in series with convection.
    g_out = 1.0 / (1.0 / g_wall + (dr / 2.0) / (2.0 * np.pi * radius_m * k_w_mk))
    ab = np.zeros((3, n))
    diag = cap / dt_s + g[:-1] + g[1:]
    diag[-1] = cap[-1] / dt_s + g[-2] + g_out
    diag[0] = cap[0] / dt_s + g[1]
    ab[1] = diag
    ab[0, 1:] = -g[1:n]
    ab[2, :-1] = -g[1:n]
    T = np.full(n, x[0] if tv0 is None else tv0, dtype=float)
    out = np.empty(len(x))
    w = vol / vol.sum()
    out[0] = float(w @ T)
    for j in range(len(x) - 1):
        rhs = cap / dt_s * T
        rhs[-1] += g_out * x[j]
        T = solve_banded((1, 1), ab, rhs)
        out[j + 1] = float(w @ T)
    return out


def cylinder_tau_s(radius_m: float, rho_kg_m3: float, cp_j_kgk: float, h_w_m2k: float) -> float:
    """Lumped tau for the cylinder-side-wall model: rho*cp*R/(2h)."""
    return rho_kg_m3 * cp_j_kgk * radius_m / (2.0 * h_w_m2k)


def sample_tau_log_uniform(rng: np.random.Generator, tau_min_range: tuple[float, float], size: int):
    """tau (minutes) drawn log-uniformly from a context range (doc 12.8 / 13.4)."""
    lo, hi = tau_min_range
    if not (0 < lo <= hi):
        raise NumericalError("tau range must satisfy 0 < lo <= hi")
    return np.exp(rng.uniform(np.log(lo), np.log(hi), size=size))
