"""Inference for the log-score contrast: dependence-aware intervals and a refitting permutation test.

Two questions are kept apart. *Evidence*: is there any information, H0: V independent of D given C? That is a test
(`perm_test`, or a one-sided interval bound). *Effect size*: how large is the information captured by the models?
That is an interval (`cluster_interval` on cross-fitted or frozen held-out scores). Whether an effect exceeds a
scientifically meaningful threshold is a third, separate comparison of the interval with that threshold.
"""
import numpy as np
import pandas as pd
from scipy import linalg, stats
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold, cross_val_predict

from . import scoring
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

def perm_test(C, V, y, splits, groups, slot, n_perm=39, seed=0, keep=None, units=None, strata=None, Cnull=None, shift_min=None, clip=None, sampler=None, max_shifts=None, **kw):
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
    sampler: a function rng -> null V (e.g. `conditional_sampler`, a conditional randomisation test); it replaces the
    permutation and shift generators and draws n_perm nulls. max_shifts: an evenly spaced subset of the shift
    configurations (fewer refits; the attainable minimum p rises to 1 / (max_shifts + 1)).
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
    if sampler is not None:
        null = np.array([stat(sampler(rng)) for _ in range(n_perm)])
    else:
        shifts = [None] * n_perm if shift_min is None else shift_configs(groups if units is None else units, strata, shift_min)
        if max_shifts and shift_min is not None and len(shifts) > max_shifts: shifts = [shifts[i] for i in np.unique(np.linspace(0, len(shifts) - 1, max_shifts).round().astype(int))]
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

def _ar1(x):
    """Lag-1 autocorrelation of an ordered series with Kendall's first-order small-sample correction r + (1 + 3r)/n,
    clipped to [0, 0.995]."""
    x = np.asarray(x, float) - np.mean(x)
    if len(x) < 3: return 0.0
    r = x[1:] @ x[:-1] / max(x @ x, 1e-12)
    return float(np.clip(r + (1 + 3 * r) / len(x), 0, 0.995))

def conditional_sampler(V, Craw, units, slot, strata=None, groups=None, inner=5):
    """Null generator for a conditional randomisation test: V* = E^[V | C] + a simulated residual process.

    E^[V | C] is a cross-fitted boosted regression on the raw context Craw (grouped by `groups`, e.g. weeks); labels are
    never read. Residuals are modelled per stratum (season, camera epoch) as a day-level AR(1) across consecutive units
    plus an AR(1) within each unit (ordered by slot), with innovations correlated across visual columns as observed.
    Valid to the extent that this model of V | C is right; persistence, regime switching and heteroscedasticity outside
    it are not reproduced. Returns draw(rng) -> V*, with the fitted mean as draw.f.
    """
    V = np.asarray(V, float).reshape(len(V), -1)
    units, slot = np.asarray(units), np.asarray(slot, float)
    strata = np.zeros(len(V), int) if strata is None else np.asarray(strata)
    f = project(Craw, V, units if groups is None else groups, inner)
    E, plan = V - f, []
    for st in np.unique(strata):
        rows = np.flatnonzero(strata == st)
        ud, inv = np.unique(units[rows], return_inverse=True)
        u = np.array([E[rows][inv == j].mean(0) for j in range(len(ud))])  # day means, days x columns
        w = E[rows] - u[inv]
        order = np.lexsort((slot[rows], inv))
        same = inv[order][1:] == inv[order][:-1]
        pu = np.array([_ar1(c) for c in u.T])
        pw = np.array([np.clip((w[order][1:][same] * w[order][:-1][same]).sum(0)[k] / max((w[order] ** 2).sum(0)[k], 1e-12), 0, .995) for k in range(V.shape[1])])
        Lu, Lw = (np.linalg.cholesky(np.cov(a.T).reshape(V.shape[1], V.shape[1]) + 1e-12 * np.eye(V.shape[1])) for a in (u, w))
        plan.append((rows, inv, order, same, pu, pw, Lu, Lw, len(ud)))

    def draw(rng):
        out = f.copy()
        for rows, inv, order, same, pu, pw, Lu, Lw, nd in plan:
            zu = rng.standard_normal((nd, V.shape[1])) @ Lu.T
            u = np.empty_like(zu)
            u[0] = zu[0]
            for t in range(1, nd): u[t] = pu * u[t - 1] + np.sqrt(1 - pu ** 2) * zu[t]
            zw = rng.standard_normal((len(rows), V.shape[1])) @ Lw.T
            w = np.empty_like(zw)
            w[0] = zw[0]
            for t in range(1, len(rows)): w[t] = np.where(same[t - 1], pw * w[t - 1] + np.sqrt(1 - pw ** 2) * zw[t], zw[t])
            out[rows[order]] += u[inv[order]] + w
        return out
    draw.f = f  # the fitted E^[V | C], so that residuals of observed and simulated V can be compared
    return draw

def rff(raw, scales, n=400, seed=0):
    """Random Fourier features of the raw context (Gaussian kernel with per-variable length scales). Fixed seed and no
    labels; long scales for time-index variables (e.g. 20 days for day of year) keep them from following weather."""
    rng = np.random.default_rng(seed)
    W, b = rng.standard_normal((raw.shape[1], n)), rng.uniform(0, 2 * np.pi, n)
    return np.sqrt(2 / n) * np.cos((np.asarray(raw, float) / np.asarray(scales, float)) @ W + b)

def challenger(C, R, y, splits, groups, **kw):
    """Context-only adequacy challenger on the same held-out splits as the contrast: the audited context design plus
    smooth non-linear functions of the context (`rff` features R), one ridge with the penalty chosen by grouped inner CV.
    Returns held-out (mu, sd, log score). A boosted residual correction was rejected: trees on day of year memorise
    persistent weather and lose on held-out weeks (notebook 14 §2)."""
    return crossfit([np.c_[c, R] for c in C] if isinstance(C, list) else np.c_[C, R], y, splits, groups, **kw)

def smooth_projection_splits(X, V, splits, groups, inner=5):
    """Train-only ridge projection of V on a fixed design X (e.g. the richest context basis plus `rff` features): inner
    out-of-fold on training rows, fitted on all training rows for test rows. Labels are never used."""
    V = np.asarray(V, float).reshape(len(V), -1)
    out = []
    for tr, te in splits:
        P, idx = np.full(V.shape, np.nan), np.flatnonzero(tr)
        cv = [(np.isin(np.arange(len(V)), idx[a]), np.isin(np.arange(len(V)), idx[b])) for a, b in GroupKFold(inner).split(idx, groups=groups[tr])]
        for k in range(V.shape[1]):
            P[tr, k] = crossfit(X, V[:, k], cv, groups, inner=inner)[0][tr]
            P[te, k] = scoring.ridge_fit(X, V[:, k], tr, groups, inner)['predict'](X[te])
        out.append(P)
    return out

def repair_gain(C, P, y, splits, groups, ls_c=None, **kw):
    """Secondary adequacy diagnostic: held-out log-score gain from adding the train-only projection P of V on the context
    (`smooth_projection_splits`) to the context model. A gain means the context misses a function of C that the image
    tracks, i.e. the joint model could repair the context. Diagnostic only; never part of the primary contrast."""
    ls_c = crossfit(C, y, splits, groups, **kw)[2] if ls_c is None else ls_c
    return crossfit([np.c_[c, p] for c, p in zip(C if isinstance(C, list) else [C] * len(splits), P)], y, splits, groups, **kw)[2] - ls_c
def residual_stats(R, units, slot, strata, hour, temp):
    """Dependence, conditional-variation and shape statistics of visual residuals R (rows x features), per stratum,
    as a Series indexed by (statistic, feature or feature pair, stratum):
    day_lag1 / day_lag7 (autocorrelation of day means over consecutive units), within_lag1 (of deviations from the day
    mean, consecutive slots of one unit), corr (row-level correlation of two features), sd_hour (SD at hour >= 14 over
    SD at hour <= 9), sd_temp (SD in the upper over the lower temperature tercile), skew, kurt (excess) and tail3 (share
    of |z| > 3). Used to compare observed residuals with those of `conditional_sampler` draws (`envelope`)."""
    R = np.asarray(R, float).reshape(len(R), -1)
    units, slot, strata, hour, temp = map(np.asarray, (units, slot, strata, hour, temp))
    ac = lambda x, k: np.corrcoef(x[k:], x[:-k])[0, 1]
    out = {}
    for st in np.unique(strata):
        rows = np.flatnonzero(strata == st)
        ud, inv = np.unique(units[rows], return_inverse=True)
        X = R[rows]
        u = np.array([X[inv == j].mean(0) for j in range(len(ud))])
        o = np.lexsort((slot[rows], inv))
        w, same = (X - u[inv])[o], inv[o][1:] == inv[o][:-1]
        lo, hi = np.quantile(temp[rows], [1 / 3, 2 / 3])
        z = (X - X.mean(0)) / X.std(0)
        for j in range(X.shape[1]):
            out |= {('day_lag1', j, st): ac(u[:, j], 1), ('day_lag7', j, st): ac(u[:, j], 7),
                    ('within_lag1', j, st): np.corrcoef(w[1:, j][same], w[:-1, j][same])[0, 1],
                    ('sd_hour', j, st): X[hour[rows] >= 14, j].std() / X[hour[rows] <= 9, j].std(),
                    ('sd_temp', j, st): X[temp[rows] >= hi, j].std() / X[temp[rows] <= lo, j].std(),
                    ('skew', j, st): (z[:, j] ** 3).mean(), ('kurt', j, st): (z[:, j] ** 4).mean() - 3, ('tail3', j, st): (np.abs(z[:, j]) > 3).mean()}
        c = np.corrcoef(X.T)
        out |= {('corr', f'{i}-{j}', st): c[i, j] for i in range(X.shape[1]) for j in range(i + 1, X.shape[1])}
    return pd.Series(out)

def envelope(obs, sims, level=0.95):
    """Observed statistics against simulated ones (rows of `sims`, same index as `obs`): the central `level` band of
    the simulations, a two-sided Monte Carlo p-value and whether the observation lies outside the band."""
    sims = pd.DataFrame(sims)
    lo, hi = sims.quantile((1 - level) / 2), sims.quantile((1 + level) / 2)
    p = np.minimum(1, 2 * np.minimum((sims <= obs).mean() + 1 / (len(sims) + 1), (sims >= obs).mean() + 1 / (len(sims) + 1)))
    return pd.DataFrame({'obs': obs, 'sim_median': sims.median(), 'lo': lo, 'hi': hi, 'p': p, 'outside': (obs < lo) | (obs > hi)})
