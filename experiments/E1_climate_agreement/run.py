"""E1: climate-input agreement and bias. Requires >= 2 REGISTERED, verified climate series (S27-S31) at the same coordinates/period;
none are present => BLOCKED (nothing fabricated). In test mode a TEST_ONLY synthetic set validates the metrics and the controls:
same-source-vs-itself must give zero difference; mismatched timezone/unit conventions must be rejected (no overlap)."""
import numpy as np
import pandas as pd

from iris.common.exceptions import NumericalError, ScientificBlocker
from iris.common.parameters import RunMode
from iris.common.provenance import EvidenceClass, Provenance
from iris.thermal.retrieve import agreement_metrics, align_sources, cross_source_sigma
from iris.tools import experiment_lib as xl
from iris.tools.synthetic import synthetic_climate


def run(ctx):
    if ctx.mode is not RunMode.TEST:
        raise ScientificBlocker("climate_sources", "no registered, verified climate series available (S27-S31 unresolved in climate_sources.yaml)",
                                "register address/version/licence, run fetch_sources, verify hashes, freeze the location rule and agreement thresholds in prereg")
    series, truth = synthetic_climate(ctx.rng.generator("synthetic_climate"))
    prov = Provenance(EvidenceClass.SIMULATED, "TEST_ONLY:synthetic_climate", synthetic=True, generated_by="iris.tools.synthetic", run_id=ctx.run_id)
    names = list(series)
    rows = []
    for i, a in enumerate(names):
        for b in names[i:]:
            x, y = align_sources(series[a], series[b])
            rows.append(dict(source_a=a, source_b=b, **agreement_metrics(x, y)))
    df = pd.DataFrame(rows)
    ctx.save_table(df, "cross_source_agreement", [prov])
    self_rows = df[df.source_a == df.source_b]
    assert (self_rows["mean_diff"] == 0).all() and (self_rows["rmse"] == 0).all(), "control failed: source vs itself must be exactly zero"
    # control: a timezone-shifted copy must NOT silently align (convention mismatch is an error, not a smaller n)
    shifted = series[names[0]].copy(); shifted.index = shifted.index + pd.Timedelta(days=4000)
    try:
        align_sources(series[names[0]], shifted); raise AssertionError("misaligned conventions were not rejected")
    except NumericalError:
        pass
    sig = cross_source_sigma(series, sigma_val=ctx.cfg["sigma_val_test_only"])
    ctx.save_table(pd.DataFrame([sig]), "sigma_data", [prov])
