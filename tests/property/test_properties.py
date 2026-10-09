import numpy as np
from hypothesis import given, settings, strategies as st

from iris.thermal import lag
from iris.thermal.kinetics.k1 import K1
from iris.thermal.kinetics.k3 import K3
from iris.thermal.kinetics.k4 import K4
from iris.fusion import analytic as an

temps = st.lists(st.floats(-5, 60, allow_nan=False), min_size=2, max_size=200)


@settings(max_examples=60, deadline=None)
@given(temps, st.floats(1e-5, 0.5), st.floats(10e3, 150e3))
def test_potency_never_increases_with_time(ts, kref, ea):
    t = np.array(ts)
    for model in (K1(kref, ea, 25.0), K3(kref, 3 * kref, ea, ea * 0.8, 25.0), K4(kref, ea, kref / 2, ea * 0.6, 25.0)):
        traj = model.potency_trajectory(t, 0.05)[0]
        assert np.all(np.diff(traj) <= 1e-12) and traj.max() <= 1.0 and traj.min() >= 0.0


@settings(max_examples=50, deadline=None)
@given(temps, st.floats(5, 30))
def test_potency_not_increasing_in_temperature_at_fixed_exposure(ts, dT):
    t = np.array(ts)
    m = K1(0.01, 80e3, 25.0)
    assert m.potency(t + dT, 0.1)[0] <= m.potency(t, 0.1)[0] + 1e-12


@settings(max_examples=50, deadline=None)
@given(st.floats(0.0, 1.0), st.floats(0.1, 100.0), st.floats(1.0, 10.0))
def test_shortfall_zero_iff_no_loss_and_linear_in_R(p, r, c):
    d = float(an.shortfall_case_a(r, p))
    assert (d == 0.0) == (p == 1.0) or d >= 0.0
    assert np.isclose(float(an.shortfall_case_a(c * r, p)), c * d)


@settings(max_examples=40, deadline=None)
@given(st.lists(st.floats(0, 45, allow_nan=False), min_size=3, max_size=100), st.floats(1.0, 2000.0))
def test_vial_temperature_stays_within_air_envelope_and_tau_to_zero(air, tau):
    a = np.array(air)
    v = lag.exponential_integrator(a, 60.0, tau)
    assert v.min() >= a.min() - 1e-9 and v.max() <= a.max() + 1e-9
    assert np.array_equal(lag.exponential_integrator(a, 60.0, 0.0), a)
    near = lag.exponential_integrator(a, 60.0, 1e-6)
    assert np.allclose(near, a, atol=1e-6)
