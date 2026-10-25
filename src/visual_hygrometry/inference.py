"""Inference for the log-score contrast: dependence-aware intervals and a refitting permutation test.

Two questions are kept apart. *Evidence*: is there any information, H0: V independent of D given C? That is a test
(`perm_test`, or a one-sided interval bound). *Effect size*: how large is the information captured by the models?
That is an interval (`cluster_interval` on cross-fitted or frozen held-out scores). Whether an effect exceeds a
scientifically meaningful threshold is a third, separate comparison of the interval with that threshold.
"""
import numpy as np
from scipy import stats
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold, cross_val_predict

from .scoring import _standardise, crossfit


def cluster_se(d, groups):
    """Mean of row scores and its SE treating whole groups as the independent units (ratio estimator): (mean, se, G)."""
    _, inv = np.unique(groups, return_inverse=True)
    s, n = np.bincount(inv, weights=d), np.bincount(inv)
    G, m = len(s), s.sum() / n.sum()
    return m, np.sqrt(G / (G - 1) * np.sum((s - m * n) ** 2)) / n.sum(), G


def cluster_interval(d, groups, level=0.95):
    m, se, G = cluster_se(d, groups)
    q = stats.t.ppf(0.5 + level / 2, G - 1)
    return m - q * se, m + q * se


def cluster_lower(d, groups, level=0.95):
    """One-sided lower confidence bound (t with G - 1 df)."""
    m, se, G = cluster_se(d, groups)
    return m - stats.t.ppf(level, G - 1) * se


def perm_test(C, V, y, splits, groups, slot, n_perm=39, seed=0, keep=None, **kw):
    """Day-block conditional permutation test of H0: V independent of D given C, refitting the joint model every draw.

    V is split into a linear prediction from C (labels unused) and a residual. Residuals of whole groups are permuted,
    rows being matched across groups by `slot` (e.g. time-of-day index), so V structure that depends only on slot or
    is linear in C survives every draw while any link between the residual and D is broken. Validity needs the
    residual blocks to be exchangeable under H0: V structure that is non-linear in C-variables other than slot is
    *not* preserved and can make the test anti-conservative. Requires a complete group x slot grid.
    keep: optional row mask; only those rows enter the statistic (same rows in every draw).
    Returns (observed contrast, p-value, null contrasts).
    """
    _, gi = np.unique(groups, return_inverse=True)
    _, si = np.unique(slot, return_inverse=True)
    pos = np.full((gi.max() + 1, si.max() + 1), -1)
    pos[gi, si] = np.arange(len(gi))
    if (pos < 0).any(): raise ValueError('perm_test needs every group to have every slot')
    m, s = _standardise(C, slice(None))
    Z = np.c_[np.ones(len(C)), (C - m) / s]
    orth = lambda A: A - Z @ np.linalg.lstsq(Z, A, rcond=None)[0]
    R = orth(V)
    Vhat = V - R
    ls_c = crossfit(C, y, splits, groups, **kw)[2]
    rows = np.ones(len(y), bool) if keep is None else keep
    stat = lambda Vx: np.nanmean((crossfit(np.c_[C, Vx], y, splits, groups, **kw)[2] - ls_c)[rows])
    obs, rng = stat(V), np.random.default_rng(seed)
    # permuted residuals are re-projected so every draw shares the observed in-sample V-C projection exactly
    null = np.array([stat(Vhat + orth(R[pos[rng.permutation(pos.shape[0])][gi, si]])) for _ in range(n_perm)])
    return obs, (1 + np.sum(null >= obs)) / (1 + n_perm), null


def boost(): return HistGradientBoostingRegressor(max_iter=100, learning_rate=0.1)


def project(C, V, groups, inner=5):
    """Cross-fitted E[V | C] by gradient boosting, one column per visual feature; labels are never used.

    Added to the context of *both* models, it gives q(D|C) exactly the function of C that the image tracks, so the
    joint model can only gain from V - E[V|C]. Out-of-fold by groups, so V's own noise is not copied into the context.
    """
    cv = list(GroupKFold(inner).split(C, groups=groups))
    return np.column_stack([cross_val_predict(boost(), C, v, cv=cv) for v in np.asarray(V, float).T])


def adequacy(C, y, splits, groups, raw, Vhat=None, level=0.95, ls_flex=None):
    """Context-adequacy diagnostics: one-sided lower bounds of held-out log-score gains over the ridge context model q(D|C).

    'flex': a gradient-boosting Gaussian context model on the raw context variables `raw` (non-parametric in all of
    them, interactions included; pass `ls_flex` to reuse its scores). 'proj': q(D|C) plus the cross-fitted visual
    projection `Vhat` (the context repair that V could perform). A lower bound > 0 means the context model is not
    competitive and no contrast may be interpreted.
    """
    ls_c = crossfit(C, y, splits, groups)[2]
    d = (crossfit(raw, y, splits, groups, model=boost)[2] if ls_flex is None else ls_flex) - ls_c
    ok = np.isfinite(d)
    out = {'flex': cluster_lower(d[ok], groups[ok], level)}
    if Vhat is not None:
        d = crossfit(np.c_[C, Vhat], y, splits, groups)[2] - ls_c
        out['proj'] = cluster_lower(d[ok], groups[ok], level)
    return out
