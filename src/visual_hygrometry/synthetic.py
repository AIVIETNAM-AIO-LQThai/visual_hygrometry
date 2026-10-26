"""Linear-Gaussian synthetic worlds with analytically known conditional mutual information.

Conditional on local hour h every node is x_i = mean_i(h) + sum_j B_ij x_j + e_i, with exogenous noise e_i of SD `sd`.
A share `day` of each noise variance is a per-day level (optionally AR(1) across days, `persist`) and the rest an AR(1)
series within the day, so samples are dependent within and across days while every row keeps the same marginal
covariance Sigma = A diag(sd^2) A^T, A = (I - B)^-1.
Any conditional mutual information given h and a subset of nodes is then exact:

    I(Y;X|G,h) = 0.5 [log|S_YG| + log|S_XG| - log|S_G| - log|S_XYG|].
"""
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd


@dataclass
class Node:
    parents: dict = field(default_factory=dict)  # parent name -> linear coefficient
    sd: float = 0.0                             # exogenous noise SD
    mean: Callable | None = None                # deterministic function of local hour
    day: float = 0.0                            # share of noise variance constant within a day
    ar: float = 0.0                             # AR(1) coefficient of the within-day part, per sample step
    persist: float = 0.0                        # AR(1) coefficient of the day-level part across consecutive days


def _ar1(n_days, per_day, phi, rng):
    z = rng.standard_normal((n_days, per_day))
    w = np.empty_like(z)
    w[:, 0] = z[:, 0]
    for t in range(1, per_day): w[:, t] = phi * w[:, t - 1] + np.sqrt(1 - phi ** 2) * z[:, t]
    return w.ravel()


def simulate(spec, n_days, per_day=48, hours=(6, 18), seed=0):
    """One row per sample: day index, local hour and every node of `spec` (given in topological order)."""
    rng = np.random.default_rng(seed)
    h = np.tile(np.linspace(*hours, per_day, endpoint=False), n_days)
    day = np.repeat(np.arange(n_days), per_day)
    cols = {'day': day, 'hour': h}
    for k, n in spec.items():
        u = rng.standard_normal(n_days)
        for t in range(1, n_days * (n.persist > 0)): u[t] = n.persist * u[t - 1] + np.sqrt(1 - n.persist ** 2) * u[t]
        e = np.sqrt(n.day) * u[day] + np.sqrt(1 - n.day) * _ar1(n_days, per_day, n.ar, rng)
        cols[k] = (n.mean(h) if n.mean else 0) + sum(c * cols[p] for p, c in n.parents.items()) + n.sd * e
    return pd.DataFrame(cols)


def _system(spec):
    names = list(spec)
    B = np.zeros((len(names),) * 2)
    for i, n in enumerate(spec.values()):
        for p, c in n.parents.items(): B[i, names.index(p)] = c
    A = np.linalg.inv(np.eye(len(names)) - B)
    return names, A, A @ np.diag([n.sd ** 2 for n in spec.values()]) @ A.T


def covariance(spec):
    names, _, S = _system(spec)
    return pd.DataFrame(S, names, names)


def cmi(spec, y, x, given=()):
    """Exact I(y; x | given, hour) in nats; y, x, given are node names or lists of names."""
    S = covariance(spec)
    y, x, g = ([v] if isinstance(v, str) else list(v) for v in (y, x, given))
    ld = lambda c: np.linalg.slogdet(S.loc[c, c].to_numpy())[1] if c else 0.0
    return 0.5 * (ld(y + g) + ld(x + g) - ld(g) - ld(x + y + g))


def conditional(spec, df, y, given=()):
    """Exact Gaussian p(y | given, hour) for every row of a simulated frame, as (mu, sd) arrays (oracle predictive)."""
    names, A, S = _system(spec)
    E = np.column_stack([n.mean(df.hour.to_numpy()) if n.mean else np.zeros(len(df)) for n in spec.values()]) @ A.T
    iy, ig = names.index(y), [names.index(g) for g in given]
    if not ig: return E[:, iy], np.full(len(df), np.sqrt(S[iy, iy]))
    K = np.linalg.solve(S[np.ix_(ig, ig)], S[ig, iy])
    return E[:, iy] + (df[list(given)].to_numpy() - E[:, ig]) @ K, np.full(len(df), np.sqrt(S[iy, iy] - S[iy, ig] @ K))
