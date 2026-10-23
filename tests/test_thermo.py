import numpy as np
import pytest

from visual_hygrometry import thermo

# Saturation vapour pressure over liquid water (hPa), IAPWS-95-based steam tables.
STEAM = {0.01: 6.11657, 10: 12.282, 20: 23.393, 25: 31.699, 30: 42.470, 40: 73.849, 50: 123.52}


@pytest.mark.parametrize('t,p', STEAM.items())
def test_vapor_pressure_against_steam_tables(t, p):
    assert thermo.es_mk(t) == pytest.approx(p, rel=2e-4)
    assert thermo.es_magnus(t) == pytest.approx(p, rel=4e-3)


def test_hand_checked_dewpoint():
    # gamma = ln(0.5) + 17.62*20/263.12 = 0.64620; Td = 243.12*gamma/(17.62 - gamma) = 9.255 degC
    assert thermo.dewpoint(20.0, 50.0) == pytest.approx(9.255, abs=1e-3)
    assert thermo.depression(20.0, 100.0) == pytest.approx(0.0, abs=1e-12)


def test_round_trip_is_exact():
    t, rh = np.meshgrid(np.linspace(-30, 45, 16), np.linspace(5, 100, 20))
    assert np.allclose(thermo.rh_from_dewpoint(t, thermo.dewpoint(t, rh)), rh, atol=1e-10)
    assert np.allclose(thermo.rh_from_d(t, thermo.depression(t, rh)), rh, atol=1e-10)


def test_sensitivity_matches_finite_differences():
    t, rh, h = 17.0, 63.0, 1e-5
    gt, grh = thermo.d_sensitivity(t, rh)
    assert gt == pytest.approx((thermo.depression(t + h, rh) - thermo.depression(t - h, rh)) / (2 * h), rel=1e-6)
    assert grh == pytest.approx((thermo.depression(t, rh + h) - thermo.depression(t, rh - h)) / (2 * h), rel=1e-6)


def test_fixed_vapour_warming_raises_d_one_to_one():
    td = 12.0
    for t in (14.0, 20.0, 28.0):
        assert thermo.depression(t, thermo.rh_from_dewpoint(t, td)) == pytest.approx(t - td, abs=1e-10)


def test_censoring_flags_and_bounds_without_clipping():
    t, rh = np.array([20.0, 20.0, 20.0]), np.array([90.0, 98.0, 101.5])
    d, cens = thermo.label_d(t, rh, rh_censor=97.0)
    assert cens.tolist() == [False, True, True]
    assert d[0] == pytest.approx(thermo.depression(20.0, 90.0))
    assert d[1] == d[2] == pytest.approx(thermo.depression(20.0, 97.0))
    with pytest.warns(RuntimeWarning):  # invalid input stays visible as NaN, not repaired
        assert np.isnan(thermo.depression(20.0, -1.0))
