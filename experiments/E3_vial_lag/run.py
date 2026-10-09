"""E3: verify the vial-lag implementation (SIMULATED). Validates the thermal code, NOT insulin behaviour."""
import json

import numpy as np
import pandas as pd

from iris.common.provenance import EvidenceClass, Provenance
from iris.thermal import lag


def run(ctx):
    c = ctx.cfg["verification"]            # VERIFICATION_ONLY physical values, not scientific inputs
    prov = Provenance(EvidenceClass.SIMULATED, "E3_verification_cases", transformation="lumped vs analytic vs finite-volume",
                      generated_by="iris.thermal.lag", run_id=ctx.run_id)
    rows, report = [], {}
    tau = lag.cylinder_tau_s(c["radius_m"], c["rho"], c["cp"], c["h"])
    bi = lag.biot_number(c["h"], np.pi * c["radius_m"] ** 2, 2 * np.pi * c["radius_m"], c["k"])
    report.update(tau_s=tau, biot=bi, lumped_valid=lag.lumped_valid(bi))
    dt, n = c["dt_s"], c["n_steps"]
    t = np.arange(n) * dt
    # 1. step response
    air = np.full(n, c["t_air_c"]); step = lag.exponential_integrator(air, dt, tau, tv0=c["t_v0_c"], output="edge")
    e_step = float(np.max(np.abs(step - lag.analytic_step_response(t, c["t_air_c"], c["t_v0_c"], tau))))
    rows.append(dict(check="step_response_vs_analytic", max_abs_error_c=e_step, tolerance=1e-9, passed=e_step < 1e-9))
    # 2. heat spike (rectangular pulse) vs piecewise analytic
    spike = np.full(n, c["t_air_c"]); spike[n // 3: n // 3 + n // 10] = c["spike_c"]
    sp = lag.exponential_integrator(spike, dt, tau, tv0=c["t_air_c"], output="edge")
    ref = np.empty(n); T = c["t_air_c"]
    for i in range(n):
        T = spike[i - 1] + (T - spike[i - 1]) * np.exp(-dt / tau) if i else T
        ref[i] = T
    rows.append(dict(check="heat_spike_vs_recursion", max_abs_error_c=float(np.max(np.abs(sp - ref))), tolerance=1e-9, passed=bool(np.max(np.abs(sp - ref)) < 1e-9)))
    # 3. timestep refinement (exact for piecewise-constant input): coarse mean == mean of fine means
    fine = np.repeat(spike, 4)
    m1 = lag.exponential_integrator(spike, dt, tau, tv0=c["t_air_c"]); m2 = lag.exponential_integrator(fine, dt / 4, tau, tv0=c["t_air_c"]).reshape(-1, 4).mean(axis=1)
    rows.append(dict(check="timestep_refinement", max_abs_error_c=float(np.max(np.abs(m1 - m2))), tolerance=1e-9, passed=bool(np.max(np.abs(m1 - m2)) < 1e-9)))
    # 4. tau -> 0 and constant ambient
    z = lag.exponential_integrator(spike, dt, 1e-9); rows.append(dict(check="tau_to_zero", max_abs_error_c=float(np.max(np.abs(z - spike))), tolerance=1e-6, passed=bool(np.max(np.abs(z - spike)) < 1e-6)))
    cst = lag.exponential_integrator(np.full(n, 30.0), dt, tau, tv0=30.0); rows.append(dict(check="constant_ambient", max_abs_error_c=float(np.max(np.abs(cst - 30.0))), tolerance=1e-12, passed=bool(np.max(np.abs(cst - 30.0)) < 1e-12)))
    # 5. finite-volume vs lumped (valid regime) and Biot check in a deliberately invalid regime
    fv = lag.finite_volume_cylinder(air, dt, radius_m=c["radius_m"], rho_kg_m3=c["rho"], cp_j_kgk=c["cp"], k_w_mk=c["k"], h_w_m2k=c["h"], tv0=c["t_v0_c"])
    d_fv = float(np.max(np.abs(fv - step)))
    rows.append(dict(check="finite_volume_vs_lumped(Bi<0.1)", max_abs_error_c=d_fv, tolerance=c["fv_tolerance_c"], passed=bool(lag.lumped_valid(bi) and d_fv < c["fv_tolerance_c"])))
    h_big = c["h_invalid"]; bi_big = lag.biot_number(h_big, np.pi * c["radius_m"] ** 2, 2 * np.pi * c["radius_m"], c["k"])
    fv_big = lag.finite_volume_cylinder(air, dt, radius_m=c["radius_m"], rho_kg_m3=c["rho"], cp_j_kgk=c["cp"], k_w_mk=c["k"], h_w_m2k=h_big, tv0=c["t_v0_c"])
    lump_big = lag.exponential_integrator(air, dt, lag.cylinder_tau_s(c["radius_m"], c["rho"], c["cp"], h_big), tv0=c["t_v0_c"], output="edge")
    rows.append(dict(check="biot_flags_invalid_lumped_regime", max_abs_error_c=float(np.max(np.abs(fv_big - lump_big))), tolerance=float("nan"),
                     passed=bool(not lag.lumped_valid(bi_big))))
    df = pd.DataFrame(rows)
    df["evidence_class"] = "SIMULATED"
    ctx.save_table(df, "lag_verification_table", [prov])
    report["checks"] = rows; report["all_passed"] = bool(df["passed"].all()); report["evidence_class"] = "SIMULATED"
    report["scope"] = "verifies the thermal-lag numerics only; says nothing about insulin behaviour"
    (ctx.tables / "lag_verification.json").write_text(json.dumps(report, indent=2, default=float))
    if not report["all_passed"]:
        ctx.log.warn("E3 verification FAILED: " + ", ".join(df.loc[~df.passed, "check"]))
