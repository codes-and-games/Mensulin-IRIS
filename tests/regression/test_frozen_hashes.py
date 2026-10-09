"""Frozen small configuration: results must reproduce exact hashes. A hash change means a scientific/numerical change that must be reviewed."""
import numpy as np
import pandas as pd

from iris.common.hashing import sha256_dataframe
from iris.common.parameters import RunMode
from iris.common.rng import RngTree
from iris.fusion.mc_engine import FusionConfig, run_fusion
from iris.population.generator import build_spec_from_config, generate
from iris.thermal.ensemble import KineticSpec, ModelSet, k0_spec
from iris.thermal.kinetics.k1 import K1
from iris.thermal.potency_draws import generate_potency_draws
from conftest import TEST_COMPLETION

import json
from pathlib import Path

FROZEN = Path(__file__).with_name("frozen_hashes.json")


def _pipeline(pop_cfg):
    pot_ms = ModelSet([KineticSpec("TEST_ONLY:A", "K1", lambda i, s: K1(0.002 * s, 80e3, 25.0), 1), k0_spec("TEST_ONLY:N")])
    pot = generate_potency_draws({"id": "S3", "kind": "constant", "params": {"temp_c": 37.0}}, 28, pot_ms, (10.0, 20.0), 10, RngTree(11), dt_min=10.0, transfer_sd=0.35)
    spec = build_spec_from_config(pop_cfg, RunMode.PROVISIONAL, eta=0.5, h_multiplier=1.0, completion=TEST_COMPLETION, n=500)
    pop = generate(spec, RngTree(11))
    fc = FusionConfig("FROZEN", "S3@28d#st0.35", 10, ("A",), "K_over_tdd_times_S", (1700.0,), (1.0, 2.0), (5.0,), (30.0,), n_perm_baseline=4)
    out = run_fusion(pop, pot, fc, RngTree(11), phases=("high_pop",))
    r = lambda d: d.round(10)
    return {"potency": sha256_dataframe(r(pot.drop(columns=[]))), "population": sha256_dataframe(r(pop)), "fusion": sha256_dataframe(r(out))}


def test_frozen_hashes(pop_cfg):
    h = _pipeline(pop_cfg)
    assert h == _pipeline(pop_cfg)            # same-process reproducibility
    if not FROZEN.exists():
        FROZEN.write_text(json.dumps(h, indent=2))   # first run freezes; commit the file
    assert json.loads(FROZEN.read_text()) == h
