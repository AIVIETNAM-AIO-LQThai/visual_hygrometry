"""Moist-air thermodynamics for reference labels.

Conventions: `temp_c`, `td_c` in degC; `d_k = temp_c - td_c` in K; `rh_pct` is relative humidity with respect to
liquid water (WMO convention, also below 0 degC); vapour pressures in hPa.

Labels use the Magnus form with WMO-No. 8 (CIMO Guide, 2018 ed., Annex 4.B) coefficients over water, stated for
-45..60 degC. Its dew-point inverse is exact, so RH -> Td -> RH round-trips to machine precision. `es_mk` is the
Murphy & Koop (2005, QJRMS 131:1539, eq. 10) liquid-water formula, used only as an accuracy reference.
"""
import numpy as np

A, B, C = 6.112, 17.62, 243.12


def es_magnus(temp_c): return A * np.exp(B * temp_c / (C + temp_c))


def es_mk(temp_c):
    T = np.asarray(temp_c, float) + 273.15
    return 0.01 * np.exp(54.842763 - 6763.22 / T - 4.210 * np.log(T) + 0.000367 * T
                         + np.tanh(0.0415 * (T - 218.8)) * (53.878 - 1331.22 / T - 9.44523 * np.log(T) + 0.014025 * T))


def vapor_pressure(temp_c, rh_pct): return rh_pct / 100 * es_magnus(temp_c)


def _gamma(temp_c, rh_pct): return np.log(rh_pct / 100) + B * temp_c / (C + temp_c)


def dewpoint(temp_c, rh_pct):
    g = _gamma(temp_c, rh_pct)
    return C * g / (B - g)


def depression(temp_c, rh_pct): return temp_c - dewpoint(temp_c, rh_pct)


def rh_from_dewpoint(temp_c, td_c): return 100 * es_magnus(td_c) / es_magnus(temp_c)


def rh_from_d(temp_c, d_k): return rh_from_dewpoint(temp_c, temp_c - d_k)


def d_sensitivity(temp_c, rh_pct):
    """(dD/dT at fixed RH [K/K], dD/dRH at fixed T [K per %RH]) of the Magnus depression."""
    dtd_dg = B * C / (B - _gamma(temp_c, rh_pct)) ** 2
    return 1 - dtd_dg * B * C / (C + temp_c) ** 2, -dtd_dg / rh_pct


def d_sd(temp_c, rh_pct, sd_t, sd_rh, rho=0.0):
    """First-order SD of D from T and RH reading errors with correlation `rho`."""
    gt, grh = d_sensitivity(temp_c, rh_pct)
    return np.sqrt((gt * sd_t) ** 2 + (grh * sd_rh) ** 2 + 2 * rho * gt * grh * sd_t * sd_rh)


def label_d(temp_c, rh_pct, rh_censor):
    """Reference D label with left-censoring at an instrument-derived saturation limit.

    Readings with rh_pct >= rh_censor (including physically implausible >100 %RH overshoot) cannot resolve D from 0.
    For those rows the returned d_k is the upper bound D(T, rh_censor) and `censored` is True; the score must then use
    P(D <= d_k), not a point density. Nothing is clipped silently.
    """
    censored = np.asarray(rh_pct >= rh_censor)
    return depression(temp_c, np.where(censored, rh_censor, rh_pct)), censored
