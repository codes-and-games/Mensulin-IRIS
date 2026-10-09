"""E2: sub-daily reconstruction (naive / sinusoid / Parton-Logan) against hourly truth, and outdoor->indoor context mapping fit on training buildings and
evaluated on HELD-OUT buildings. Needs registered hourly data and a registered comfort database; none => BLOCKED. Test mode uses TEST_ONLY synthetic data.
Parton-Logan stays fail-closed until its form and parameters are verified (S34)."""
import json

import numpy as np
import pandas as pd

from iris.common.exceptions import ScientificBlocker
from iris.common.parameters import RunMode
from iris.common.provenance import EvidenceClass, Provenance
from iris.thermal import context as cx
from iris.thermal import reconstruct as rc
from iris.tools import experiment_lib as xl
from iris.tools.synthetic import synthetic_climate, synthetic_comfort_table


def run(ctx):
    if ctx.mode is not RunMode.TEST:
        raise ScientificBlocker("hourly_truth_and_comfort_db", "no registered hourly climate truth (S27) or comfort database (S31)", "register, hash and verify, then re-run")
    prov = Provenance(EvidenceClass.SIMULATED, "TEST_ONLY:synthetic_E2", synthetic=True, generated_by="iris.thermal", run_id=ctx.run_id)
    series, truth = synthetic_climate(ctx.rng.generator("synthetic_climate"), n_days=90, sources=("A",), bias=(0.0,), noise=(0.0,))
    hourly = truth.to_numpy().reshape(-1, 24)
    tmax, tmin = hourly.max(axis=1), hourly.min(axis=1)
    rows = []
    for name, rec in (("naive_constant", rc.naive_constant(tmax, tmin)), ("sinusoid_hour_of_max_15", rc.sinusoid(tmax, tmin, 15.0)),
                      ("sinusoid_hour_of_max_12", rc.sinusoid(tmax, tmin, 12.0))):
        m = rc.reconstruction_metrics(truth.to_numpy(), rec); m.pop("residual_autocorr"); rows.append(dict(method=name, **m))
    try:
        rc.parton_logan(tmax, tmin, tmin, 6.0, 18.0, rc.PartonLoganParams(0.0, 0.0, 0.0))
    except ScientificBlocker as e:
        rows.append(dict(method="parton_logan", bias=np.nan, rmse=np.nan, residual_autocorr_lag1=np.nan, note=f"BLOCKED: {e.parameter}"))
    ctx.save_table(pd.DataFrame(rows), "reconstruction_errors", [prov])
    tab = synthetic_comfort_table(ctx.rng.generator("synthetic_comfort"))
    cm, val = cx.fit_linear_mapping(tab, "building_id", "t_out_c", "t_in_c", ctx.rng.generator("E2_split"))
    assert not (set(val["train_groups"]) & set(val["test_groups"])), "building leakage"
    d = cm.to_json_dict(); d.update(source_ids=["TEST_ONLY:synthetic_comfort"], evidence_class="SIMULATED", note="TEST_ONLY fit; not a context mapping for any real context")
    (ctx.tables / "context_mapping.json").write_text(json.dumps(d, indent=2, default=float))
    ctx.save_table(pd.DataFrame([val | {"train_groups": ",".join(val["train_groups"]), "test_groups": ",".join(val["test_groups"])}]), "context_validation", [prov])
