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
