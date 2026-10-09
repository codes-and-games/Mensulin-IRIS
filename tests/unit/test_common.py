import csv
import numpy as np
import pandas as pd
import pytest

from iris.common.exceptions import (ClaimsViolation, EvidenceClassError, ProvenanceError, SchemaError,
                                    TestOnlyDataError, UnregisteredSourceError)
from iris.common.provenance import EvidenceClass, Provenance, assert_production_safe, parse_evidence_class
from iris.common.registry import SourceRegistry, REGISTRY_FIELDS, MANIFEST_FIELDS
from iris.common.rng import RngTree
from iris.common.schemas import PERSON_DAY, validate_potency_draws
from iris.common.hashing import sha256_file
from iris.tools.claims_lint import lint_text, assert_clean
from iris.tools.verify_registry import verify


def _write_registry(tmp_path, rows, manifest=()):
    (tmp_path / "data/raw").mkdir(parents=True, exist_ok=True)
    with open(tmp_path / "data/sources_registry.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=REGISTRY_FIELDS); w.writeheader()
        for r in rows: w.writerow({k: r.get(k, "") for k in REGISTRY_FIELDS})
    with open(tmp_path / "data/manifest.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=MANIFEST_FIELDS); w.writeheader()
        for r in manifest: w.writerow(r)


GOOD = dict(source_id="X1", **{"class": "PUBLISHED"}, title="t", citation_or_url="doi:x", access_date="2026-01-01",
            licence="CC-BY", verified_by="reviewer")


def test_evidence_class_rejects_measured():
    with pytest.raises(EvidenceClassError):
        parse_evidence_class("MEASURED")
    assert parse_evidence_class("computed") is EvidenceClass.COMPUTED


def test_registry_rejects_unregistered_and_unverified(tmp_path):
    _write_registry(tmp_path, [GOOD, dict(source_id="X2", **{"class": "PUBLISHED"}, title="t")])
    reg = SourceRegistry.load(tmp_path / "data/sources_registry.csv")
    assert reg.require("X1").source_id == "X1"
    with pytest.raises(UnregisteredSourceError):
        reg.require("NOPE")
    with pytest.raises(UnregisteredSourceError):
        reg.require("X2")               # registered but unverified
    assert reg.require("X2", allow_unverified=True)
    with pytest.raises(TestOnlyDataError):
        reg.require("TEST_ONLY:fixture")


def test_verify_registry_rejects_unregistered_file_and_hash_mismatch(tmp_path):
    f = tmp_path / "data/raw/a.csv"
    _write_registry(tmp_path, [GOOD])
    f.write_text("a,b\n1,2\n")
    rep = verify(tmp_path)
    assert "data/raw/a.csv" in rep.unregistered_files
    _write_registry(tmp_path, [GOOD], [dict(path="data/raw/a.csv", source_id="X1", sha256="0" * 64, bytes=8, read_only=True)])
    assert verify(tmp_path).hash_mismatches == ["data/raw/a.csv"]
    _write_registry(tmp_path, [GOOD], [dict(path="data/raw/a.csv", source_id="X1", sha256=sha256_file(f), bytes=8, read_only=True)])
    assert not verify(tmp_path).hard_errors()


def test_production_rejects_synthetic_lineage():
    p = Provenance(EvidenceClass.SIMULATED, "TEST_ONLY:fixture", synthetic=True)
    child = p.derive(evidence_class=EvidenceClass.COMPUTED, source_id="derived1", transformation="x", generated_by="t")
    assert "TEST_ONLY:fixture" in child.parent_source_ids and child.synthetic
    with pytest.raises(TestOnlyDataError):
        assert_production_safe([child])
    with pytest.raises(ProvenanceError):
        Provenance(EvidenceClass.SIMULATED, "plain", synthetic=True)


def test_provenance_chain_preserved():
    a = Provenance(EvidenceClass.PUBLIC_DATASET, "S27")
    b = a.derive(evidence_class=EvidenceClass.COMPUTED, source_id="recon", transformation="sinusoid", generated_by="reconstruct")
    c = b.derive(evidence_class=EvidenceClass.SIMULATED, source_id="potency", transformation="K1", generated_by="kin")
    assert c.parent_source_ids == ("S27", "recon")


def test_rng_streams_independent_and_reproducible():
    t = RngTree(7)
    a1 = t.generator("population", "tdd").random(5)
    _ = t.generator("thermal", "tau").random(1000)          # extra draws elsewhere...
    a2 = RngTree(7).generator("population", "tdd").random(5)
    assert np.array_equal(a1, a2)                            # ...do not perturb this stream
    assert not np.array_equal(a1, t.generator("population", "cycle").random(5))
    assert not np.array_equal(RngTree(8).generator("population", "tdd").random(5), a1)
    assert not np.array_equal(t.indexed("x", 0).random(3), t.indexed("x", 1).random(3))


def test_schema_enforcement():
    bad = pd.DataFrame({"scenario_id": ["a"], "kinetic_study": ["s"], "kinetic_model": ["K1"], "epistemic_draw_j": [0],
                        "delta_data_c": [0.0], "tau_min": [10.0], "potency": [1.2], "is_null_model": [False]})
    with pytest.raises(SchemaError):
        validate_potency_draws(bad)
    k0 = bad.assign(potency=0.99, kinetic_model="K0", is_null_model=True)
    with pytest.raises(SchemaError):
        validate_potency_draws(k0)                           # K0 must be exactly 1.0
    with pytest.raises(SchemaError):
        validate_potency_draws(bad.drop(columns=["tau_min"]))
    with pytest.raises(SchemaError):
        PERSON_DAY.validate(pd.DataFrame({"dataset": ["d"]}))


def test_claims_lint_flags_and_allows_attribution():
    assert lint_text("We measured the potency loss.")
    assert lint_text("Our patients in the simulation")
    assert lint_text("This storage is safe to use.")
    assert not lint_text("Smith et al. measured the loss; the model projects a shortfall in simulation.")
    assert not lint_text("The model projects X under the declared assumptions.")
    with pytest.raises(ClaimsViolation):
        assert_clean("a recommended dose is shown")
