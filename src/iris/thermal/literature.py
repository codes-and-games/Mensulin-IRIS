"""Degradation-literature table -> kinetic fits -> ModelSet.

literature/degradation_literature.csv columns:
  study_id, source_id, product, formulation, container, temp_c, time_days, potency, sd, assay,
  extracted_by, verified_by, page_table_ref
Only rows with ``verified_by`` can enter a production fit. Unlike products/formulations are NEVER pooled:
a fit is made per (study_id, product, formulation).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from iris.common.exceptions import ScientificBlocker
from iris.common.parameters import RunMode
from iris.common.rng import RngTree

from .ensemble import KineticSpec, ModelSet, k0_spec, uniform_weights_with_null_by_count
from .kinetics.fitting import K1Fit, fit_k1, loso_k1
from .kinetics.k1 import K1

LIT_COLUMNS = ["study_id", "source_id", "product", "formulation", "container", "temp_c", "time_days", "potency", "sd",
               "assay", "extracted_by", "verified_by", "page_table_ref"]


def load_literature(path: str | Path, mode: RunMode) -> pd.DataFrame:
    p = Path(path)
    if not p.exists() or p.stat().st_size == 0:
        raise ScientificBlocker("degradation_literature", f"{p} missing or empty", "complete L2 extraction")
    df = pd.read_csv(p)
    miss = [c for c in LIT_COLUMNS if c not in df.columns]
    if miss:
        raise ScientificBlocker("degradation_literature", f"columns missing {miss}", "use the documented schema")
    if df.empty:
        raise ScientificBlocker("degradation_literature", "no extracted rows", "extract multi-temperature potency data from primary sources")
    if mode is RunMode.PRODUCTION:
        df = df[df["verified_by"].notna() & (df["verified_by"].astype(str).str.strip() != "")]
        if df.empty:
            raise ScientificBlocker("degradation_literature", "no row has verified_by", "second-reader verification required for production")
    return df


def fit_study_models(df: pd.DataFrame, rng_tree: RngTree, n_draws: int = 400, min_obs: int = 4):
    """One K1 fit per (study, product, formulation). Returns (specs, fits, diagnostics)."""
    specs, fits, diag = [], {}, []
    for (sid, prod, form), g in df.groupby(["study_id", "product", "formulation"], dropna=False):
        key = f"{sid}|{prod}|{form}"
        if len(g) < min_obs or g["temp_c"].nunique() < 2:
            diag.append(dict(study=key, fitted=False, reason="too few observations/temperatures (kinetics not identifiable)"))
            continue
        obs = g.rename(columns={"study_id": "study"})[["study", "temp_c", "time_days", "potency", "sd"]].reset_index(drop=True)
        fit = fit_k1(obs, rng_tree.generator("fit", key))
        fits[key] = fit
        kref, ea = fit.draws(n_draws, rng_tree.generator("draws", key))
        tref = fit.t_ref_c
        specs.append(KineticSpec(key, "K1", (lambda kr, e, t0: (lambda i, s: K1(kr[i] * s, e[i], t0)))(kref, ea, tref), n_draws,
                                 source_ids=tuple(g["source_id"].astype(str).unique())))
        diag.append(dict(study=key, fitted=True, identifiable=fit.identifiable, reasons="; ".join(fit.reasons), n_obs=fit.n_obs, corr_lnk_ea=fit.corr_lnk_ea))
    return specs, fits, pd.DataFrame(diag)


def build_model_set(df: pd.DataFrame, rng_tree: RngTree, null_studies: list[str] | None = None) -> tuple[ModelSet, pd.DataFrame]:
    specs, fits, diag = fit_study_models(df, rng_tree)
    nulls = list(null_studies or [])
    specs += [k0_spec(s) for s in nulls]
    uniform_weights_with_null_by_count(specs, len(nulls))
    ms = ModelSet(specs, comparable_study_count=len([s for s in specs if s.model_id == "K1"]))
    return ms, diag
