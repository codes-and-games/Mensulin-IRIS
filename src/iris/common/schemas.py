"""Strict, validated table schemas (person_day, thermal_exposure, virtual_population,
potency_draws, fusion_out). Validation is explicit: unknown / missing columns, dtypes,
ranges, nullability and evidence-class vocabulary are all enforced.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .exceptions import SchemaError
from .provenance import EvidenceClass, OUTPUT_CLASSES

PHASES = ("early_follicular", "late_follicular", "periovulatory", "early_luteal", "midluteal", "late_luteal")
N_PHASES = len(PHASES)


@dataclass(frozen=True)
class Col:
    name: str
    kind: str  # 'str','int','float','bool','datetime'
    nullable: bool = False
    lo: float | None = None
    hi: float | None = None
    allowed: tuple | None = None


@dataclass(frozen=True)
class TableSchema:
    name: str
    columns: tuple[Col, ...]
    extra_ok: bool = False

    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(df, pd.DataFrame):
            raise SchemaError(f"{self.name}: expected DataFrame, got {type(df)!r}")
        names = [c.name for c in self.columns]
        missing = [n for n in names if n not in df.columns]
        if missing:
            raise SchemaError(f"{self.name}: missing columns {missing}")
        if not self.extra_ok:
            extra = [c for c in df.columns if c not in names]
            if extra:
                raise SchemaError(f"{self.name}: unexpected columns {extra}")
        for col in self.columns:
            s = df[col.name]
            if not col.nullable and s.isna().any():
                raise SchemaError(f"{self.name}.{col.name}: nulls not permitted")
            nn = s.dropna()
            if nn.empty:
                continue
            if col.kind == "float":
                if not pd.api.types.is_numeric_dtype(nn) or pd.api.types.is_bool_dtype(nn):
                    raise SchemaError(f"{self.name}.{col.name}: expected numeric")
                if not np.isfinite(nn.to_numpy(dtype=float)).all():
                    raise SchemaError(f"{self.name}.{col.name}: non-finite values")
            elif col.kind == "int":
                if not pd.api.types.is_integer_dtype(nn) and not (
                    pd.api.types.is_float_dtype(nn) and (nn % 1 == 0).all()
                ):
                    raise SchemaError(f"{self.name}.{col.name}: expected integers")
            elif col.kind == "bool":
                if not pd.api.types.is_bool_dtype(nn):
                    raise SchemaError(f"{self.name}.{col.name}: expected bool")
            elif col.kind == "str":
                if not all(isinstance(v, str) for v in nn):
                    raise SchemaError(f"{self.name}.{col.name}: expected strings")
            elif col.kind == "datetime":
                if not pd.api.types.is_datetime64_any_dtype(nn):
                    raise SchemaError(f"{self.name}.{col.name}: expected datetime")
            if col.kind in ("float", "int"):
                v = nn.to_numpy(dtype=float)
                if col.lo is not None and (v < col.lo).any():
                    raise SchemaError(f"{self.name}.{col.name}: value below {col.lo}")
                if col.hi is not None and (v > col.hi).any():
                    raise SchemaError(f"{self.name}.{col.name}: value above {col.hi}")
            if col.allowed is not None and not nn.isin(col.allowed).all():
                bad = sorted(set(nn[~nn.isin(col.allowed)].astype(str)))[:5]
                raise SchemaError(f"{self.name}.{col.name}: values not allowed: {bad}")
        return df


PERSON_DAY = TableSchema("person_day", (
    Col("dataset", "str"), Col("person_id", "str"), Col("date_local", "str"), Col("tz", "str"),
    Col("tdd_u", "float", True, 0, 1000), Col("basal_u", "float", True, 0, 1000),
    Col("bolus_u", "float", True, 0, 1000), Col("carb_g", "float", True, 0, 3000),
    Col("carb_entries", "int", True, 0), Col("cgm_coverage", "float", True, 0, 1),
    Col("mean_glucose_mgdl", "float", True, 10, 1000), Col("tir_pct", "float", True, 0, 100),
    Col("tbr_pct", "float", True, 0, 100), Col("tar_pct", "float", True, 0, 100),
    Col("device_type", "str", True), Col("exclude_flag", "bool"), Col("exclude_reason", "str", True),
    Col("cycle_day", "int", True, 1), Col("cycle_len", "int", True, 10, 90),
    Col("cycle_pos", "float", True, 0, 1), Col("phase", "str", True, allowed=PHASES),
    Col("pwd_flags", "str", True),
))

_QC = ("ok", "range_flag", "fill_value", "gap_interpolated", "gap_missing", "unit_converted")
THERMAL_EXPOSURE = TableSchema("thermal_exposure", (
    Col("scenario_id", "str"), Col("context_id", "str"), Col("location_id", "str", True),
    Col("timestamp_utc", "datetime"), Col("t_out_c", "float", True, -90, 100),
    Col("t_air_c", "float", False, -90, 100), Col("t_vial_c", "float", False, -90, 100),
    Col("tau_min", "float", False, 0), Col("source_ids", "str"),
    Col("qc_flag", "str", allowed=_QC), Col("imputed_flag", "bool"),
    Col("evidence_class", "str", allowed=("COMPUTED", "SIMULATED")),
))

_VP_BASE = [
    Col("vp_id", "int", False, 0), Col("heterogeneity_scenario", "str"), Col("eta", "float"),
    Col("tdd_u", "float", False, 0.0), Col("cycle_len", "float", False, 21, 40),
    Col("ovulation_day", "float", False, 1, 40), Col("anovulatory", "bool"),
]
_VP_PHASE = []
for _p in range(1, N_PHASES + 1):
    _VP_PHASE += [Col(f"S_p{_p}", "float", False, 0), Col(f"gamma_p{_p}", "float", False, 0),
                  Col(f"rho_p{_p}", "float", False, 0), Col(f"R_p{_p}_u", "float", False, 0),
                  Col(f"isf_p{_p}_mgdl_per_u", "float", True, 0)]
_VP_TAIL = [Col("swing_unit", "float", False, 0), Col("swing_sens", "float", False, 0),
            Col("swing_rank", "float", False, 0, 1)]
VIRTUAL_POPULATION = TableSchema("virtual_population", tuple(_VP_BASE + _VP_PHASE + _VP_TAIL))

POTENCY_DRAWS = TableSchema("potency_draws", (
    Col("scenario_id", "str"), Col("kinetic_study", "str"), Col("kinetic_model", "str", allowed=("K0", "K1", "K2", "K3", "K4", "K5")),
    Col("epistemic_draw_j", "int", False, 0), Col("delta_data_c", "float"), Col("tau_min", "float", False, 0),
    Col("potency", "float", False, 0, 1), Col("is_null_model", "bool"),
))

FUSION_OUT = TableSchema("fusion_out", (
    Col("run_id", "str"), Col("epistemic_draw_j", "int", False, 0), Col("scenario_id", "str"),
    Col("phase", "str"), Col("dosing_case", "str", allowed=("A", "B")), Col("isf_const", "float", True, 0),
    Col("metric", "str"), Col("threshold", "float", True), Col("value", "float", True), Col("mc_se", "float", True, 0),
))


def validate_potency_draws(df: pd.DataFrame) -> pd.DataFrame:
    """Schema plus cross-field rule: K0 rows must be exact point masses at P == 1."""
    POTENCY_DRAWS.validate(df)
    k0 = df[df["kinetic_model"] == "K0"]
    if len(k0) and not (k0["potency"] == 1.0).all():
        raise SchemaError("potency_draws: K0 (label-stable null) rows must have potency == 1.0 exactly")
    if (df["is_null_model"] != (df["kinetic_model"] == "K0")).any():
        raise SchemaError("potency_draws: is_null_model must equal (kinetic_model == 'K0')")
    return df


def validate_output_class(ec) -> EvidenceClass:
    from .provenance import parse_evidence_class

    c = parse_evidence_class(ec)
    if c not in OUTPUT_CLASSES:
        raise SchemaError(f"evidence class {c.value} cannot label an IRIS-generated output")
    return c
