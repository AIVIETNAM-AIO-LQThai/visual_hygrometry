"""Inference for the log-score contrast: dependence-aware intervals and a refitting permutation test.

Two questions are kept apart. *Evidence*: is there any information, H0: V independent of D given C? That is a test
(`perm_test`, or a one-sided interval bound). *Effect size*: how large is the information captured by the models?
That is an interval (`cluster_interval` on cross-fitted or frozen held-out scores). Whether an effect exceeds a
scientifically meaningful threshold is a third, separate comparison of the interval with that threshold.
"""
import numpy as np
from scipy import linalg, stats
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


def donor_sampler(units, slot, strata=None):
    """Draws a donor row for every row: whole units (days, weeks) are permuted, within strata if given, and each row
    takes the donor unit's row with the nearest slot (exact on complete grids, nearest available time otherwise).
    draw(rng) permutes units at random; draw(rng, shift=k) instead shifts the ordered units cyclically by k (within
    each stratum), which keeps the serial dependence of the donated series intact."""
    _, ui = np.unique(units, return_inverse=True)
    rows = [np.flatnonzero(ui == j) for j in range(ui.max() + 1)]
    rows = [r[np.argsort(slot[r], kind='stable')] for r in rows]
    st = np.zeros(len(rows), int) if strata is None else np.unique([strata[r[0]] for r in rows], return_inverse=True)[1]
    classes = [np.flatnonzero(st == c) for c in np.unique(st)]

    def draw(rng, shift=None):
        perm = np.arange(len(rows))
        for c in classes: perm[c] = rng.permutation(c) if shift is None else np.roll(c, -shift)
        src = np.empty(len(slot), int)
        for j, d in enumerate(perm):
            rj, rd = rows[j], rows[d]
            if len(rd) == 1:
                src[rj] = rd[0]
                continue
            sj, sd = slot[rj], slot[rd]
            k = np.clip(np.searchsorted(sd, sj), 1, len(sd) - 1)
            src[rj] = rd[np.where(np.abs(sj - sd[k - 1]) <= np.abs(sd[k] - sj), k - 1, k)]
        return src
    return draw


def shift_configs(units, strata=None, shift_min=7):
    """Cyclic shifts k used by the shift null: one k applied to every stratum, k in [shift_min, n_min - shift_min] with
    n_min the shortest stratum (in units). Every configuration is distinct, none is the identity, and each stratum is
    shifted by at least shift_min units. The smallest attainable p-value is 1 / (len + 1)."""
    u = np.asarray(units)
    if strata is None: n_min = len(np.unique(u))
    else: n_min = min(len(np.unique(u[np.asarray(strata) == c])) for c in np.unique(strata))
    ks = list(range(shift_min, n_min - shift_min + 1))
    if not ks: raise ValueError(f'shortest stratum has {n_min} units: no cyclic shift of at least {shift_min} is available')
    return ks


def select_capacity(levels, y, splits, groups, inner=5, **kw):
    """Context design per split, chosen among nested `levels` (smallest first; each a full-length matrix or a list
    with one per split, e.g. `worlds.split_levels`) by the grouped inner-CV log score of the context-only model on that
    split's training rows. Visual columns and test-row labels are never read, so both models of a contrast receive the
    same chosen design. Returns (designs, chosen level index)."""
    out, chosen = [], []
    for j, (tr, _) in enumerate(splits):
        lv = [L[j] if isinstance(L, list) else L for L in levels]
        idx = np.flatnonzero(tr)
        cv = [(np.isin(np.arange(len(y)), idx[a]), np.isin(np.arange(len(y)), idx[b])) for a, b in GroupKFold(inner).split(idx, groups=groups[tr])]
        k = min(inner, min(len(np.unique(groups[a])) for a, _ in cv))  # penalty folds inside each selection fold
        score = [np.nanmean(crossfit(L, y, cv, groups, inner=k, **kw)[2][tr]) for L in lv]
        chosen.append(int(np.argmax(score)))
        out.append(lv[chosen[-1]])
    return out, chosen


def clip_to_training(V, splits, q=0.005):
    """Per split, V with every column clipped to its training rows' [q, 1 - q] quantiles, so a fitted visual
    coefficient is never extrapolated beyond the image range it was estimated on (part of the joint model)."""
    V = np.asarray(V, float)
    return [np.clip(V, *np.quantile(V[tr], [q, 1 - q], axis=0)) for tr, _ in splits]


def perm_test(C, V, y, splits, groups, slot, n_perm=39, seed=0, keep=None, units=None, strata=None, Cnull=None, shift_min=None, clip=None, **kw):
    """Conditional permutation test of H0: V independent of D given C, refitting the joint model for every draw.

    Null generator: V = (linear prediction from Cnull) + residual R; whole `units` (default: `groups`, e.g. days; pass
    week ids for multi-day persistence) exchange their residuals, within `strata` if given (regimes, seasons), rows being
    matched by nearest `slot` (time of day, or day-in-block * 24 + hour). Permuted residuals are re-projected on the
    orthogonal complement of Cnull so every draw shares the observed in-sample V-Cnull projection. The generator uses
    (C, V) of the analysis sample but never D; model fitting and scoring inside every draw follow the same train-only
    rules as the observed statistic.
    Validity needs residual units to be exchangeable under H0 (within strata). Structure of V that is non-linear in
    Cnull, or dependence that outlasts a unit, is not preserved and can make the test anti-conservative.
    shift_min: use the cyclic-shift null instead: every shift in `shift_configs` is enumerated (n_perm is ignored); with
    G units and no strata that is G - 2 shift_min + 1 nulls, so p >= 1 / (G - 2 shift_min + 2). It preserves serial dependence across units exactly, so it is the null for
    multi-day persistence; it assumes stationarity of the residual series (wrap-around joins its end to its start).
    C: context design, or a list of per-split designs (then Cnull is required). keep: rows entering the statistic.
    clip: quantile q of `clip_to_training`, applied to the observed and to every null V alike.
    Returns (observed contrast, p-value, null contrasts).
    """
    if Cnull is None: Cnull = C
    m, s = _standardise(Cnull, slice(None))
    Z = np.c_[np.ones(len(Cnull)), (Cnull - m) / s]
    orth = lambda A: A - Z @ _lstsq(Z, A)
    R = orth(V)
    Vhat = V - R
    if clip is not None:
        Cl = C if isinstance(C, list) else [C] * len(splits)
        cat = lambda Vx: [np.c_[c, v] for c, v in zip(Cl, clip_to_training(Vx, splits, clip))]
    else:
        cat = lambda Vx: [np.c_[c, Vx] for c in C] if isinstance(C, list) else np.c_[C, Vx]
    ls_c = crossfit(C, y, splits, groups, **kw)[2]
    rows = np.ones(len(y), bool) if keep is None else keep
    stat = lambda Vx: np.nanmean((crossfit(cat(Vx), y, splits, groups, **kw)[2] - ls_c)[rows])
    draw, rng = donor_sampler(groups if units is None else units, np.asarray(slot, float), strata), np.random.default_rng(seed)
    obs = stat(V)
    shifts = [None] * n_perm if shift_min is None else shift_configs(groups if units is None else units, strata, shift_min)
    null = np.array([stat(Vhat + orth(R[draw(rng, k)])) for k in shifts])
    n_perm = len(null)
    return obs, (1 + np.sum(null >= obs)) / (1 + n_perm), null


def hac_interval(d, groups, level=0.95, lag=None):
    """Interval for the mean of row scores from the series of group (day) means in group order, with a Newey-West
    (Bartlett) long-run variance; lag defaults to floor(4 (G/100)^(2/9)). For serially dependent groups."""
    ug, inv = np.unique(groups, return_inverse=True)
    s, n = np.bincount(inv, weights=d), np.bincount(inv)
    m = s.sum() / n.sum()
    u = (s - m * n) / n.mean()
    G = len(u)
    L = int(4 * (G / 100) ** (2 / 9)) if lag is None else lag
    lrv = u @ u / G + 2 * sum((1 - j / (L + 1)) * (u[j:] @ u[:-j]) / G for j in range(1, L + 1))
    se = np.sqrt(max(lrv, 0) / G)
    q = stats.t.ppf(0.5 + level / 2, G - 1)
    return m - q * se, m + q * se


def _lstsq(Z, A):
    """Least-squares coefficients; falls back to pivoted QR when the SVD-based driver fails on a rank-deficient Z
    (the fitted projection Z @ coef is the same for every least-squares solution)."""
    try: return np.linalg.lstsq(Z, A, rcond=None)[0]
    except np.linalg.LinAlgError: return linalg.lstsq(Z, A, lapack_driver='gelsy')[0]


def boost(): return HistGradientBoostingRegressor(max_iter=100, learning_rate=0.1)


def project(C, V, groups, inner=5):
    """Cross-fitted E[V | C] by gradient boosting, one column per visual feature; labels are never used.

    Added to the context of *both* models, it gives q(D|C) exactly the function of C that the image tracks, so the
    joint model can only gain from V - E[V|C]. Out-of-fold by groups, so V's own noise is not copied into the context.
    """
    cv = list(GroupKFold(inner).split(C, groups=groups))
    return np.column_stack([cross_val_predict(boost(), C, v, cv=cv) for v in np.asarray(V, float).T])


def project_splits(C, V, splits, groups, inner=5):
    """Train-only E[V | C] for every split: a full-length array per split whose training rows hold out-of-fold
    predictions within the training groups and whose test rows are predicted by a model fitted on all training rows.
    Test (and any other) rows never enter the projection used for that split."""
    V = np.asarray(V, float)
    out = []
    for tr, te in splits:
        P = np.full(V.shape, np.nan)
        P[tr] = project(C[tr], V[tr], groups[tr], inner)
        P[te] = np.column_stack([boost().fit(C[tr], v[tr]).predict(C[te]) for v in V.T])
        out.append(P)
    return out


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
