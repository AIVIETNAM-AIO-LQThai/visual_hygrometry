"""Standard synthetic worlds in data-contract column names (shared by the estimator notebooks from 04 on).

A world is a dict: `spec` (synthetic.Node SEM), `ctx` / `vis` (contract columns), `truth` (information on the measured
variables), `n_days`, optional `per_day`, `hours`, `shared` (label unit = conditioning unit) and `modify(df, rng)` for
non-linear structure that the linear-Gaussian SEM cannot express.
"""
from dataclasses import replace

import numpy as np
import pandas as pd

from . import data, synthetic
from .synthetic import Node

HOUR = ['hour_s1', 'hour_c1', 'hour_s2', 'hour_c2']


def cyc(a, b, peak=15): return lambda h: a + b * np.cos(2 * np.pi * (h - peak) / 24)


def gauss_world(gamma=.162, beta=.4, t_sd=3, r_sd=2, r_day=.5, r_ar=.9, v_day=.3, v_ar=.5):
    """Diurnal T, moisture residual r, D = mean(h) + beta T + r (D ~ 7 + 4 cos(hour) K), visual cue gamma r + noise."""
    return {'temp_cond_c': Node(sd=t_sd, mean=cyc(20, 5), day=.7, ar=.95), 'dres': Node(sd=r_sd, day=r_day, ar=r_ar),
            'd_ref_k': Node({'temp_cond_c': beta, 'dres': 1}, mean=cyc(7 - 20 * beta, 4 - 5 * beta)), 'vis_moist': Node({'dres': gamma}, 1.0, day=v_day, ar=v_ar)}


def rad_world(err_sd=1.0):
    """Shared radiation-biased unit: label D and conditioning T both carry err; the image sees the irradiance anomaly."""
    return {'t_true': Node(sd=3, mean=cyc(20, 5), day=.7, ar=.95), 'dres': Node(sd=2, day=.5, ar=.9),
            'd_true': Node({'t_true': .4, 'dres': 1}, mean=cyc(-1, 2)), 'cloud': Node(sd=1, day=.8, ar=.9),
            'err': Node({'cloud': err_sd}), 'temp_cond_c': Node({'t_true': 1, 'err': 1}), 'd_ref_k': Node({'d_true': 1, 'err': 1}),
            'vis_bright': Node({'cloud': 1}, .3)}


def regime(sds, p_humid=.5):
    """Day-level regime scales the moisture residual (SD sds[1] humid with probability p_humid, sds[0] dry); mean unchanged."""
    def f(df, rng):
        r = rng.random(df.day.max() + 1)[df.day] < p_humid
        df['regime'] = r.astype(float)
        df['d_ref_k'] = df.d_ref_k - df.dres + np.where(r, sds[1], sds[0]) * df.dres / df.attrs['dres_sd']
        return df
    return f


def frame(W, n_days, seed):
    """Simulate a world, attach the fixed hour basis, apply its non-linear modification, label sensor ids."""
    df = synthetic.simulate(W['spec'], n_days, W.get('per_day', 48), W.get('hours', (6, 18)), seed=seed)
    df = pd.concat([df, data.fourier(df.hour, 24, 2, 'hour')], axis=1).assign(hour_local=df.hour, ref_sensor_id='ref', cond_sensor_id='ref' if W.get('shared') else 'cond')
    df.attrs['dres_sd'] = W['spec']['dres'].sd if 'dres' in W['spec'] else 1
    return W['modify'](df, np.random.default_rng(seed + 7)) if 'modify' in W else df


def iid(W):
    """Same marginal per-row distribution with independent rows (day = ar = 0), for Monte-Carlo truths."""
    return W | {'spec': {k: replace(n, day=0.0, ar=0.0) for k, n in W['spec'].items()}}


def add_context_basis(df, knots):
    """Flexible E2 context: fixed-knot cubic spline in T and products of T with the hour Fourier basis."""
    S = data.spline(df.temp_cond_c, knots, 'temp_spl')
    X = pd.DataFrame({f'hourxtemp_{c[5:]}': df[c] * (df.temp_cond_c - 20) for c in HOUR}, index=df.index)
    return pd.concat([df, S, X], axis=1), HOUR + list(S) + list(X)


def add_context_levels(df, knots, doy_knots, fine_doy_knots, hour_season=False):
    """Nested E2 context bases of increasing capacity, all fixed in advance (no fitting, no visual input).

    L1: hour Fourier basis (2 harmonics), T spline, T x hour basis, day-of-year spline (the notebook 10 context);
    L2: L1 + third hour harmonic and its T product, T x day-of-year-spline products (season-dependent T effect) and a
        finer day-of-year spline (`fine_doy_knots`, sharper seasonal transitions);
    L3: L2 + tensor product of the 2-harmonic hour basis with the T spline (T shape varying with time of day);
    L4 (only with hour_season=True): L3 + hour basis x day-of-year spline (diurnal cycle changing over the season).
    df needs hour_local, temp_cond_c, doy and the HOUR columns. Returns (df, {level: columns}).
    """
    t = df.temp_cond_c - 20
    h3 = data.fourier(df.hour_local, 24, 3, 'hour')[['hour_s3', 'hour_c3']]
    S, Y, F = data.spline(df.temp_cond_c, knots, 'temp_spl'), data.spline(df.doy, doy_knots, 'doy_spl'), data.spline(df.doy, fine_doy_knots, 'doy_fspl')
    X = pd.DataFrame({f'hourxtemp_{c[5:]}': (df[c] if c in HOUR else h3[c]) * t for c in HOUR + list(h3)}, index=df.index)
    DT = Y.mul(t, axis=0).rename(columns=lambda c: f'doyxtemp_{c[7:]}')
    TS = pd.DataFrame({f'hourxtspl_{c[5:]}_{s[8:]}': df[c] * S[s] for c in HOUR for s in S}, index=df.index)
    L1 = HOUR + list(S) + list(X)[:len(HOUR)] + list(Y)
    L2 = L1 + list(h3) + list(X)[len(HOUR):] + list(DT) + list(F)
    HS = pd.DataFrame({f'hourxdoy_{c[5:]}_{y[7:]}': df[c] * Y[y] for c in HOUR for y in Y}, index=df.index) if hour_season else pd.DataFrame(index=df.index)
    new = [h3, S, X, Y, DT, F, TS, HS]
    df = df.drop(columns=[c for b in new for c in b if c in df])  # rebuilt, e.g. with a clamped day of year
    lv = {'L1': L1, 'L2': L2, 'L3': L2 + list(TS)} | ({'L4': L2 + list(TS) + list(HS)} if hour_season else {})
    return pd.concat([df] + new, axis=1), lv


def split_levels(df, splits, knots, doy_knots, fine_doy_knots, extra=(), hour_season=False):
    """Context levels for every split with day of year clamped to that split's training rows, so the seasonal bases
    hold their last fitted value beyond the fitted record instead of extrapolating unsupported basis functions.
    extra: further context columns of df (not day-of-year dependent) appended to every level.
    Returns ({level: [matrix per split]}, {level: columns})."""
    out = {}
    for tr, _ in splits:
        d, lv = add_context_levels(df.assign(doy=df.doy.clip(df.doy[tr].min(), df.doy[tr].max())), knots, doy_knots, fine_doy_knots, hour_season)
        for k, c in lv.items(): out.setdefault(k, []).append(d[c + list(extra)].to_numpy())
    return out, {k: c + list(extra) for k, c in lv.items()}
