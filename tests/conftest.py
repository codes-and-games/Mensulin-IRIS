"""Shared fixtures. Everything synthetic here is TEST_ONLY and must never reach a production run."""
import numpy as np
import pandas as pd
import pytest
import yaml
from pathlib import Path

from iris.common.parameters import RunMode
from iris.common.rng import RngTree

REPO = Path(__file__).resolve().parents[1]
TEST_COMPLETION = {"profile_completion": "two_anchor_cosine", "concordance_sd": "sd_from_concordance_normal",
                   "gamma_amplitude": 0.03, "xi_sd": 0.03, "anovulatory_prevalence": 0.0}   # TEST_ONLY stress levels


@pytest.fixture
def rng_tree():
    return RngTree(12345)


@pytest.fixture
def pop_cfg():
    return yaml.safe_load(open(REPO / "configs/population/population_default.yaml"))


@pytest.fixture
def test_population(pop_cfg, rng_tree):
    """SYNTHETIC / TEST_ONLY virtual population (provisional anchors + stress completions)."""
    from iris.population.generator import build_spec_from_config, generate
    spec = build_spec_from_config(pop_cfg, RunMode.PROVISIONAL, eta=0.5, h_multiplier=1.0, completion=TEST_COMPLETION, n=3000)
    return generate(spec, rng_tree)


@pytest.fixture
def test_potency():
    """SYNTHETIC / TEST_ONLY potency draws."""
    return pd.DataFrame({"scenario_id": "TEST@7d", "kinetic_study": "TEST_ONLY:syn", "kinetic_model": "K1",
                         "epistemic_draw_j": np.arange(12), "delta_data_c": 0.0, "tau_min": 15.0,
                         "potency": np.linspace(0.85, 0.99, 12), "is_null_model": False})
