"""Data-contract tests: schemas, types, units, missingness, provenance remain valid for the shipped tables and fixtures."""
import csv
from pathlib import Path

import pandas as pd
import pytest

from iris.common.exceptions import ProvenanceError, SchemaError, TestOnlyDataError
from iris.common.io import read_table, write_table, sidecar_path
from iris.common.parameters import RunMode
from iris.common.provenance import EvidenceClass, Provenance
from iris.common.registry import REGISTRY_FIELDS, SourceRegistry
from iris.common.schemas import PERSON_DAY, VIRTUAL_POPULATION, validate_potency_draws
from iris.common.gates import require_sources
from iris.features.person_day import finalize_person_day
from iris.tools.synthetic import synthetic_person_day
from conftest import REPO
import numpy as np


def test_shipped_registry_is_wellformed_and_unverified_by_default():
    reg = SourceRegistry.load(REPO / "data/sources_registry.csv", REPO / "data/manifest.csv")
    assert len(reg.rows) >= 25
    with open(REPO / "data/sources_registry.csv") as fh:
        assert next(csv.reader(fh)) == REGISTRY_FIELDS
    # nothing is verified until a human verifies it: production gate must refuse every shipped row
    with pytest.raises(Exception):
        require_sources(reg, ["S1"], RunMode.PRODUCTION)
    assert require_sources(reg, ["S1"], RunMode.PROVISIONAL)


def test_production_gate_rejects_test_fixtures():
    reg = SourceRegistry.load(REPO / "data/sources_registry.csv")
    with pytest.raises(TestOnlyDataError):
        require_sources(reg, ["TEST_ONLY:fixture"], RunMode.PRODUCTION)
    with pytest.raises(TestOnlyDataError):
        require_sources(reg, ["TEST_ONLY:fixture"], RunMode.PROVISIONAL)
    assert require_sources(reg, ["TEST_ONLY:fixture"], RunMode.TEST) == []


def test_person_day_schema_and_nullable_cycle_fields():
    df = synthetic_person_day(np.random.default_rng(0), n_persons=2, n_days=5, with_cycle_labels=False).drop(columns=["isf_clinician"])
    out = finalize_person_day(df)
    PERSON_DAY.validate(out)
    bad = out.copy(); bad.loc[0, "tdd_u"] = -1.0
    with pytest.raises(SchemaError):
        PERSON_DAY.validate(bad)
    bad2 = out.copy(); bad2["phase"] = "nonsense"
    with pytest.raises(SchemaError):
        PERSON_DAY.validate(bad2)


def test_virtual_population_schema(test_population):
    VIRTUAL_POPULATION.validate(test_population)
    bad = test_population.copy(); bad.loc[0, "cycle_len"] = 99.0
    with pytest.raises(SchemaError):
        VIRTUAL_POPULATION.validate(bad)


def test_table_roundtrip_requires_provenance_and_detects_tampering(tmp_path, test_potency):
    prov = Provenance(EvidenceClass.SIMULATED, "TEST_ONLY:syn", synthetic=True)
    p = tmp_path / "t.parquet"
    write_table(test_potency, p, [prov])
    df, pr = read_table(p)
    assert len(df) == len(test_potency) and pr[0].synthetic
    with pytest.raises(ValueError):
        write_table(test_potency, tmp_path / "u.parquet", [])
    test_potency.assign(potency=0.5).to_parquet(p, index=False)          # tamper after provenance was written
    with pytest.raises(ProvenanceError):
        read_table(p)
    sidecar_path(p).unlink()
    with pytest.raises(ProvenanceError):
        read_table(p)


def test_literature_tables_have_documented_schemas():
    for name, cols in {"degradation_literature.csv": "study_id,source_id,product,formulation,container,temp_c,time_days,potency,sd,assay,extracted_by,verified_by,page_table_ref",
                       "biological_evidence.csv": "parameter,value,ci_low,ci_high,unit,source_id,page_table_ref,population,extracted_by,verified_by,status"}.items():
        assert open(REPO / "literature" / name).readline().strip() == cols
    bio = pd.read_csv(REPO / "literature/biological_evidence.csv")
    assert (bio.loc[bio.status == "UNRESOLVED", "value"].isna()).all()      # unresolved parameters never carry values
    assert bio.loc[bio.status == "PENDING_VERIFY", "verified_by"].isna().all()  # pending rows have no second reader
    assert bio.loc[bio.status == "RESOLVED", "verified_by"].notna().all()        # resolved rows record a second reader
