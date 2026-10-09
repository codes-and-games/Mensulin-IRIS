"""Literature-anchored virtual population (SIMULATED). 'virtual individuals', never patients/participants.

Everything stochastic draws from named generators (iris.common.rng). Completions that are not
evidence-derived (profile completion, non-normal families, gamma/xi levels, dependence) are recorded
in ``PopulationSpec.stress_components`` so downstream code classifies the run as Theta_S-only.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

from iris.common.exceptions import NumericalError, ScientificBlocker
from iris.common.parameters import Parameter, RunMode, Status
from iris.common.rng import RngTree
from iris.common.schemas import N_PHASES, VIRTUAL_POPULATION

from .dependence import BiologicalDependence, standardized_margin
from .requirement import build_requirement, swing_stats
from .sensitivity import build_sensitivity

HIGH_PHASE_POP, LOW_PHASE_POP = 4, 0  # midluteal vs early follicular (document 14.5)


@dataclass
class PopulationSpec:
    n: int
    tdd_mean_u: float
    tdd_sd_u: float
    cycle_mean_d: float
    cycle_sd_d: float
    cycle_lo_d: float
    cycle_hi_d: float
    luteal_mean_d: float
    luteal_sd_d: float
    anovulatory_prevalence: float | None
    m_p: np.ndarray                 # ln-scale phase mean profile of sensitivity (six phases)
    lambda_p: np.ndarray            # between-person amplitude loading (six phases), already scaled by h
    eps_sd: float
    gamma_amplitude: float          # ln-scale amplitude of the glucose-load phase pattern (peak midluteal)
    gamma_cv: float                 # between-person CV of gamma amplitude (0 => none)
    xi_sd: float
    eta: float
    family: str = "normal"
    family_opts: dict = field(default_factory=dict)
    dependence: BiologicalDependence = field(default_factory=BiologicalDependence.independent)
    heterogeneity_label: str = "mid"
    stress_components: list = field(default_factory=list)
    allow_circular_control: bool = False


def lognormal_params(mean: float, sd: float) -> tuple[float, float]:
    """(mu_ln, sigma_ln) for a lognormal with the stated mean and SD. Doc check: 37.3/12.2 -> 3.568, 0.319."""
    if mean <= 0 or sd <= 0:
        raise NumericalError("mean and sd must be positive")
    s2 = np.log1p((sd / mean) ** 2)
    return float(np.log(mean) - 0.5 * s2), float(np.sqrt(s2))


def truncnorm_match_moments(mean: float, sd: float, lo: float, hi: float) -> tuple[float, float]:
    """(mu, sigma) of the PRE-truncation normal such that the TRUNCATED distribution has the declared mean and SD."""
    from scipy.optimize import fsolve

    def resid(th):
        mu, sg = th[0], abs(th[1])
        a, b = (lo - mu) / sg, (hi - mu) / sg
        return [stats.truncnorm.mean(a, b, mu, sg) - mean, stats.truncnorm.std(a, b, mu, sg) - sd]

    sol, info, ier, msg = fsolve(resid, [mean, sd], full_output=True)
    if ier != 1 or np.max(np.abs(resid(sol))) > 1e-8:
        raise NumericalError(f"could not match truncated moments: {msg}")
    return float(sol[0]), float(abs(sol[1]))


GAMMA_SHAPE = np.array([-0.5, -0.25, 0.0, 0.25, 1.0, 0.5])  # fixed shape: peak midluteal. Direction only (document), amplitude is a declared level.


def gamma_profile(n: int, amplitude: float, cv: float, u_gamma: np.ndarray) -> np.ndarray:
    amp_i = np.maximum(amplitude * (1.0 + cv * u_gamma), 0.0)
    g = np.exp(amp_i[:, None] * GAMMA_SHAPE[None, :])
    return g / g.mean(axis=1, keepdims=True)


def generate(spec: PopulationSpec, rng_tree: RngTree) -> pd.DataFrame:
    n = int(spec.n)
    if spec.anovulatory_prevalence is None:
        raise ScientificBlocker("anovulatory_prevalence", "[TO EXTRACT] unresolved",
                                "extract prevalence (biology review) or declare an explicit stress value (incl. 0.0)")
    mu_ln, sg_ln = lognormal_params(spec.tdd_mean_u, spec.tdd_sd_u)
    lat = spec.dependence.draw_latents(rng_tree.generator("population", "latents"), n)
    tdd = np.exp(mu_ln + sg_ln * lat[:, 0])
    c_mu, c_sg = truncnorm_match_moments(spec.cycle_mean_d, spec.cycle_sd_d, spec.cycle_lo_d, spec.cycle_hi_d)
    a, b = (spec.cycle_lo_d - c_mu) / c_sg, (spec.cycle_hi_d - c_mu) / c_sg
    cyc = stats.truncnorm.rvs(a, b, loc=c_mu, scale=c_sg, size=n, random_state=rng_tree.generator("population", "cycle_len"))
    lut = stats.truncnorm.rvs(-3, 3, loc=spec.luteal_mean_d, scale=spec.luteal_sd_d, size=n,
                              random_state=rng_tree.generator("population", "luteal"))
    ovul = np.clip(cyc - lut, 1.0, None)
    anov = rng_tree.generator("population", "anovulatory").uniform(size=n) < spec.anovulatory_prevalence
    z = standardized_margin(spec.family, spec.family_opts)(lat[:, 1])
    s = build_sensitivity(z, spec.m_p, spec.lambda_p, spec.eps_sd, rng_tree.generator("population", "eps"), anov)
    gam = gamma_profile(n, spec.gamma_amplitude, spec.gamma_cv, lat[:, 2])
    rho = build_requirement(s, gam, spec.eta, spec.xi_sd, rng_tree.generator("population", "xi"),
                            allow_circular_control=spec.allow_circular_control)
    r_u = tdd[:, None] * rho
    sw_u, sw_s, _ = swing_stats(rho, tdd, s, HIGH_PHASE_POP, LOW_PHASE_POP)
    rank = stats.rankdata(sw_u, method="average") / n
    out = {"vp_id": np.arange(n), "heterogeneity_scenario": spec.heterogeneity_label, "eta": float(spec.eta),
           "tdd_u": tdd, "cycle_len": cyc, "ovulation_day": ovul, "anovulatory": anov}
    for p in range(N_PHASES):
        k = p + 1
        out[f"S_p{k}"], out[f"gamma_p{k}"], out[f"rho_p{k}"], out[f"R_p{k}_u"] = s[:, p], gam[:, p], rho[:, p], r_u[:, p]
        out[f"isf_p{k}_mgdl_per_u"] = np.full(n, np.nan)   # filled only in glucose-equivalent analyses (ISF model + K)
    out["swing_unit"], out["swing_sens"], out["swing_rank"] = sw_u, sw_s, rank
    df = pd.DataFrame(out)
    VIRTUAL_POPULATION.validate(df)
    return df


def phase_matrix(df: pd.DataFrame, prefix: str) -> np.ndarray:
    suffix = "_u" if prefix == "R_p" else ""
    return np.column_stack([df[f"{prefix}{k}{suffix}"].to_numpy() for k in range(1, N_PHASES + 1)])


def build_spec_from_config(cfg: dict, mode: RunMode, *, eta: float, h_multiplier: float, family: str = "normal",
                           family_opts: dict | None = None, dependence: BiologicalDependence | None = None,
                           n: int | None = None, completion: dict | None = None, label: str = "mid") -> PopulationSpec:
    """Translate configs/population/population_default.yaml into a PopulationSpec.

    Unresolved parameters raise ScientificBlocker unless the caller names an explicit stress completion
    (which is recorded in ``stress_components``). No value is guessed.
    """
    completion = completion or {}
    stress: list[str] = []

    def P(name, d, unit=""):
        return Parameter(name, d.get("value", d.get("mean_u", d.get("mean_d"))), unit, Status(d["status"]) if d.get("status") in Status.__members__ else Status.UNRESOLVED,
                         d.get("source_id", ""), note=d.get("note", ""))

    tdd, cyc, lut = cfg["tdd"], cfg["cycle"], cfg["luteal_length"]
    for key, d in (("tdd", tdd), ("cycle", cyc), ("luteal", lut)):
        Parameter(key, 1.0, "", Status(d["status"])).get(mode)  # status gate (PENDING_VERIFY needs provisional)
    anchors = cfg["phase_sensitivity_anchor"]
    phases = cfg["phases"]
    ef, ml = anchors["early_follicular"], anchors["midluteal"]
    for d in (ef, ml):
        Parameter("phase_anchor", d["value"], "", Status(d["status"])).get(mode)
    # --- phase mean profile m_p
    missing = [p for p in phases if anchors[p]["value"] is None]
    if missing:
        if completion.get("profile_completion") != "two_anchor_cosine":
            raise ScientificBlocker("phase_sensitivity_anchor", f"unresolved phases {missing}",
                                    "extract six-phase profile from the anchor study supplement, or declare the stress completion 'two_anchor_cosine'")
        stress.append("profile_completion:two_anchor_cosine")
        m_p = _two_anchor_cosine_profile(ef["value"], ml["value"])
    else:
        m_p = np.log1p(np.array([anchors[p]["value"] for p in phases]))
    # --- between-person loading lambda_p
    sd_cfg = cfg["between_person_posterior_sd"]
    if sd_cfg["value"] is not None:
        lam = np.asarray(sd_cfg["value"], float) * h_multiplier
    else:
        if completion.get("concordance_sd") != "sd_from_concordance_normal":
            raise ScientificBlocker("between_person_posterior_sd", "[TO EXTRACT] unresolved",
                                    "extract the reported posterior, or declare the reference/stress completion 'sd_from_concordance_normal'")
        conc = cfg["concordance_with_population_direction"]
        Parameter("concordance", conc["value"], "", Status(conc["status"])).get(mode)
        sigma_rel = 1.0 / float(stats.norm.ppf(conc["value"]))   # contrast_i = m_p (1 + sigma_rel z)
        lam = m_p * sigma_rel * h_multiplier
        stress.append("concordance_sd(reference assumption)")
    # --- gamma, xi
    g_amp = completion.get("gamma_amplitude")
    xi_sd = completion.get("xi_sd")
    if cfg["glucose_load_phase_profile"]["value"] is None:
        if g_amp is None:
            raise ScientificBlocker("glucose_load_phase_profile", "[TO EXTRACT] unresolved", "declare stress 'gamma_amplitude' or extract carbohydrate phase tables")
        stress.append(f"gamma_amplitude={g_amp}")
    if cfg["residual_xi_sd"]["value"] is None:
        if xi_sd is None:
            raise ScientificBlocker("residual_xi_sd", "unresolved: calibrate to published TDD phase variance", "declare stress 'xi_sd' or calibrate")
        stress.append(f"xi_sd={xi_sd}")
    if family != "normal":
        stress.append(f"family={family}")
    dep = dependence or BiologicalDependence.independent()
    if dep.status != "EVIDENCE":
        stress.append(f"R_B={dep.label}({dep.status})")
    return PopulationSpec(
        n=int(n or cfg["n"]), tdd_mean_u=tdd["mean_u"], tdd_sd_u=tdd["sd_u"], cycle_mean_d=cyc["mean_d"], cycle_sd_d=cyc["sd_d"],
        cycle_lo_d=cyc["lo_d"], cycle_hi_d=cyc["hi_d"], luteal_mean_d=lut["mean_d"], luteal_sd_d=lut["sd_d"],
        anovulatory_prevalence=completion.get("anovulatory_prevalence", cfg["anovulatory_prevalence"]["value"]),
        m_p=m_p, lambda_p=lam, eps_sd=float(completion.get("eps_sd", 0.0)), gamma_amplitude=float(g_amp or 0.0),
        gamma_cv=float(completion.get("gamma_cv", 0.0)), xi_sd=float(xi_sd or 0.0), eta=eta, family=family,
        family_opts=family_opts or {}, dependence=dep, heterogeneity_label=label, stress_components=stress)


def _two_anchor_cosine_profile(ef: float, ml: float) -> np.ndarray:
    """STRESS completion: ln S_p = a*cos(2 pi (x_p - x0)), phases at equally spaced stand-in positions
    (the true day windows are [TO EXTRACT]); (a, x0) solved so that, AFTER normalising to cycle mean 1,
    S_early_follicular = 1 + ef and S_midluteal = 1 + ml (the two published anchors)."""
    from scipy.optimize import least_squares

    x = (np.arange(N_PHASES) + 0.5) / N_PHASES

    def norm_s(a, x0):
        v = np.exp(a * np.cos(2 * np.pi * (x - x0)))
        return v / v.mean()

    def resid(th):
        s = norm_s(*th)
        return [s[0] - (1 + ef), s[4] - (1 + ml)]

    best = None
    for x0_init in np.linspace(-0.5, 0.5, 9):
        sol = least_squares(resid, [0.05, x[0] + x0_init * 0.1])
        if best is None or sol.cost < best.cost:
            best = sol
    if best.cost > 1e-14:
        raise NumericalError("two-anchor cosine completion could not reproduce the published anchors")
    a, x0 = best.x
    return a * np.cos(2 * np.pi * (x - x0))
