"""Residual processes for the conditional randomisation test, synthetic null worlds and the held-out audit (M1.4).

A *process* models the visual residual E = V - E^[V | C] per stratum (season) as a day-level AR(1) plus a within-day AR(1),
with a scale that depends on hour and temperature. Kinds: 'P' (parametric: simulation-calibrated within-day AR, joint
Student-t innovations), 'R' (resampling: donor days within the same temperature tercile) and 'nb17' (the notebook 17
`inference.conditional_sampler` residual model, for the audit). `factory` turns a kind into a sampler with the signature
of `inference.conditional_sampler`; `world_residuals` generates residuals outside both model classes; `holdout_audit`
checks a process on blocks of days it was not fitted on. Days are the sorted unique `units` of a stratum (consecutive
units are consecutive days) and the rows of a day are ordered by `slot`.
"""
import numpy as np
import pandas as pd

from . import inference
from .inference import _ar1

PHI = np.arange(20) * 0.05  # calibration grid for the within-day AR coefficient


# --- day structure and small helpers ---------------------------------------------------------------------------------
def _layout(units, slot):
    """Day structure of one stratum's rows: day index (rank of the unit), position within the day (slot order), number
    of days and length of the longest day."""
    _, inv = np.unique(units, return_inverse=True)
    cnt = np.bincount(inv)
    o = np.lexsort((slot, inv))
    pos = np.empty(len(inv), int)
    pos[o] = np.arange(len(inv)) - (np.cumsum(cnt) - cnt)[inv[o]]
    return inv, pos, len(cnt), int(cnt.max())

def _grid(X, inv, pos, nd, L):
    """Rows -> days x positions (x features) array, zero where the day has no row."""
    X = np.asarray(X)
    G = np.zeros((nd, L) + X.shape[1:], bool if X.dtype == bool else float)
    G[inv, pos] = X
    return G

def _split(X, inv, pos, nd, L):
    """Day means (days x features), deviations from them on the day grid and the grid's row mask."""
    M = _grid(np.ones(len(inv), bool), inv, pos, nd, L)
    u = _grid(X, inv, pos, nd, L).sum(1) / M.sum(1)[:, None]
    return u, (_grid(X, inv, pos, nd, L) - u[:, None]) * M[..., None], M

def _corr(A):
    """Correlation matrix of the columns (identity if constant or a single column)."""
    p = A.shape[1]
    if p == 1 or len(A) < 3: return np.eye(p)
    with np.errstate(all='ignore'): C = np.corrcoef(A.T)
    C = np.where(np.isfinite(C), C, 0.0)
    np.fill_diagonal(C, 1.0)
    return C

def _chol(R):
    """Cholesky factor of a correlation matrix; eigenvalues are clipped when it is not positive definite."""
    p = len(R)
    try: return np.linalg.cholesky(R + 1e-8 * np.eye(p))
    except np.linalg.LinAlgError:
        w, v = np.linalg.eigh(R)
        R = (v * np.maximum(w, 1e-6)) @ v.T
        d = np.sqrt(np.diag(R))
        return np.linalg.cholesky(R / np.outer(d, d))

def _ar_days(z, phi):
    """Stationary AR(1) across days (axis 0) from unit-variance innovations z (days x features); phi scalar or per feature."""
    u = np.empty_like(z)
    u[0] = z[0]
    for t in range(1, len(z)): u[t] = phi * u[t - 1] + np.sqrt(1 - np.square(phi)) * z[t]
    return u

def _ar_pos(z, phi):
    """Stationary AR(1) along the positions (axis 1) of a days x positions x features array; phi scalar, per feature or
    per day (days x 1)."""
    w = np.empty_like(z)
    w[:, 0] = z[:, 0]
    for k in range(1, z.shape[1]): w[:, k] = phi * w[:, k - 1] + np.sqrt(1 - np.square(phi)) * z[:, k]
    return w

def _tmix(rng, shape, nu):
    """Multiplier turning normal vectors into unit-variance multivariate Student t with nu df (one mixing variable per
    row, the last axis of `shape` being 1)."""
    return np.sqrt((nu - 2) / rng.chisquare(nu, shape))


# --- scale model --------------------------------------------------------------------------------------------------------
def _poisson(X, y, steps=50):
    """Log-link quasi-Poisson regression by damped Newton steps (coefficient vector)."""
    b = np.zeros(X.shape[1])
    b[0] = np.log(max(y.mean(), 1e-12))
    ll = lambda b: y @ (X @ b) - np.exp(np.clip(X @ b, -50, 50)).sum()
    for _ in range(steps):
        mu = np.exp(np.clip(X @ b, -50, 50))
        step = np.linalg.solve((X * mu[:, None]).T @ X + 1e-8 * np.eye(len(b)), X.T @ (y - mu))
        t, l0 = 1.0, ll(b)
        while t > 1e-6 and ll(b + t * step) < l0 - 1e-10: t /= 2
        b = b + t * step
        if np.abs(t * step).max() < 1e-9: break
    return b

class _Scale:
    """Fitted scale model s(C) = sqrt(E[e^2 | C]): log E[e^2 | C] = a + b1 sin(2 pi h/24) + b2 cos(2 pi h/24) + c T_z per
    feature, T_z standardised with the fit rows' mean and SD. on=False: a constant scale (the SD of E)."""
    def __init__(self, E, hour, temp, on=True):
        self.on, self.m, self.sd = on, float(np.mean(temp)), float(max(np.std(temp), 1e-12))
        self.const = E.std(0) + 1e-12
        self.beta = np.array([_poisson(self._design(hour, temp), e ** 2) for e in E.T]) if on else None  # features x 4
    def _design(self, hour, temp):
        h = 2 * np.pi * np.asarray(hour, float) / 24
        return np.c_[np.ones(len(h)), np.sin(h), np.cos(h), (np.asarray(temp, float) - self.m) / self.sd]
    def __call__(self, hour, temp):
        if not self.on: return np.tile(self.const, (len(hour), 1))
        return np.sqrt(np.exp(np.clip(self._design(hour, temp) @ self.beta.T, -50, 50)))

def fit_scale(E, hour, temp, on=True):
    """Scale model of the residuals E (rows x features) on hour and temperature; call it as s(hour, temp) -> rows x
    features. Coefficients are in .beta (a, b1, b2, c per feature)."""
    return _Scale(np.asarray(E, float).reshape(len(E), -1), hour, temp, on)


# --- within-day calibration ----------------------------------------------------------------------------------------------
def _calibrate(M, n_sets, rng):
    """For unit-variance AR(1) days with the day structure M (days x positions mask), on the grid PHI: the mean lag-1
    statistic of day-demeaned consecutive-slot pairs (sum of products over pairs / sum of squares, as observed), the mean
    variance of the deviations g and the variance of the day means h. Common random numbers across the grid."""
    z = rng.standard_normal((n_sets,) + M.shape)
    n = M.sum(1)
    out = []
    for phi in PHI:
        x = _ar_pos(z.transpose(1, 2, 0), phi).transpose(2, 0, 1) * M
        m = x.sum(2) / n
        w = (x - m[..., None]) * M
        ss = (w ** 2).sum((1, 2))
        out.append(((w[..., 1:] * w[..., :-1]).sum((1, 2)) / np.maximum(ss, 1e-12), ss / M.sum(), m.var(1)))
    r, g, h = (np.array([o[k].mean() for o in out]) for k in range(3))
    return np.maximum.accumulate(r), g, h


# --- residual process ------------------------------------------------------------------------------------------------------
def _fit_P(E, units, slot, hour, temp, o):
    sc = fit_scale(E, hour, temp, o['scale'])
    Z, p = E / sc(hour, temp), E.shape[1]
    inv, pos, nd, L = _layout(units, slot)
    u, W, M = _split(Z, inv, pos, nd, L)
    r = (W[:, 1:] * W[:, :-1]).sum((0, 1)) / np.maximum((W ** 2).sum((0, 1)), 1e-12)  # observed lag-1, as in _calibrate
    rbar, g, h = _calibrate(M, o['n_cal'], np.random.default_rng(o['seed']))
    phi = np.interp(r, rbar, PHI) if o['phi_w'] is None else np.broadcast_to(np.asarray(o['phi_w'], float), p).copy()
    vdm = u.var(0)
    sw2 = (W ** 2).sum((0, 1)) / len(Z) / np.maximum(np.interp(phi, PHI, g), 1e-12)
    su2 = np.maximum(vdm - sw2 * np.interp(phi, PHI, h), 0.05 * vdm)
    ru = np.clip(np.array([_ar1(c) for c in u.T]) * vdm / np.maximum(su2, 1e-12), 0, 0.95)
    inn = (W[:, 1:] - phi * W[:, :-1])[M[:, 1:]]  # within-day innovations
    Ru, Rw = (np.eye(p), np.eye(p)) if o['independent'] else (_corr(u), _corr(inn))
    x = inn / np.where(inn.std(0) > 0, inn.std(0), 1)
    nu = None if o['gaussian'] or len(inn) < 5 else 4 + 6 / np.clip(np.mean((x ** 4).mean(0) - 3), 0.25, 6)
    return dict(scale=sc, phi=np.minimum(phi * o['persist'], 0.95), sw=np.sqrt(sw2), su=np.sqrt(su2),
                ru=np.minimum(ru * o['persist'], 0.95), Lu=_chol(Ru), Lw=_chol(Rw), nu=nu)

def _sim_P(f, inv, pos, nd, L, slot, hour, temp, rng):
    p = len(f['sw'])
    u = _ar_days(rng.standard_normal((nd, p)) @ f['Lu'].T, f['ru']) * f['su']
    eta = rng.standard_normal((nd, L, p)) @ f['Lw'].T
    if f['nu'] is not None: eta *= _tmix(rng, (nd, L, 1), f['nu'])
    w = _ar_pos(eta, f['phi']) * f['sw']
    return f['scale'](hour, temp) * (u[inv] + w[inv, pos])

def _fit_R(E, units, slot, hour, temp, o):
    sc = fit_scale(E, hour, temp, o['scale'])
    Z = E / sc(hour, temp)
    inv, pos, nd, L = _layout(units, slot)
    u, W, M = _split(Z, inv, pos, nd, L)
    ru = np.array([_ar1(c) for c in u.T])
    u = u - u.mean(0)
    inn = u[1:] - ru * u[:-1] if nd > 2 else u
    inn = inn * np.sqrt(u.var(0) * (1 - ru ** 2) / np.maximum(inn.var(0), 1e-12))  # the corrected AR keeps the observed day-mean variance
    tg = _grid(temp, inv, pos, nd, L)
    tg[~M] = -np.inf
    dmax = tg.max(1)
    thr = np.quantile(dmax, [1 / 3, 2 / 3])
    terc = (dmax > thr[0]).astype(int) + (dmax > thr[1])
    pools = [np.flatnonzero(terc == k) for k in range(3)]
    o_ = np.lexsort((pos, inv))
    b = np.r_[0, np.cumsum(np.bincount(inv))]
    days = [(slot[o_[b[d]:b[d + 1]]], W[d][M[d]]) for d in range(nd)]  # donor deviations, rows in slot order
    return dict(scale=sc, ru=ru, inn=inn, days=days, thr=thr,
                pools=[q if len(q) else np.arange(nd) for q in pools])

def _sim_R(f, inv, pos, nd, L, slot, hour, temp, rng, burn=100):
    p = len(f['ru'])
    e = f['inn'][rng.integers(len(f['inn']), size=nd + burn)]
    u = np.zeros((nd + burn, p))
    for t in range(1, nd + burn): u[t] = f['ru'] * u[t - 1] + e[t]
    u = u[burn:]
    tg = _grid(temp, inv, pos, nd, L)
    tg[~_grid(np.ones(len(inv), bool), inv, pos, nd, L)] = -np.inf
    dmax = tg.max(1)
    terc = (dmax > f['thr'][0]).astype(int) + (dmax > f['thr'][1])
    o_ = np.lexsort((pos, inv))
    b = np.r_[0, np.cumsum(np.bincount(inv))]
    w = np.empty((len(inv), p))
    for d in range(nd):
        r = o_[b[d]:b[d + 1]]
        sd, dev = f['days'][rng.choice(f['pools'][terc[d]])]
        if len(sd) == 1: w[r] = dev[0]
        else:
            k = np.clip(np.searchsorted(sd, slot[r]), 1, len(sd) - 1)  # nearest slot, as inference.donor_sampler
            w[r] = dev[np.where(np.abs(slot[r] - sd[k - 1]) <= np.abs(sd[k] - slot[r]), k - 1, k)]
    return f['scale'](hour, temp) * (u[inv] + w)

def _fit_nb17(E, units, slot, hour, temp, o):
    """Coefficients exactly as inside `inference.conditional_sampler` (within-day coefficient uncorrected)."""
    inv, p = np.unique(units, return_inverse=True)[1], E.shape[1]
    u = np.array([E[inv == j].mean(0) for j in range(inv.max() + 1)])
    w = E - u[inv]
    order = np.lexsort((slot, inv))
    same = inv[order][1:] == inv[order][:-1]
    pu = np.array([_ar1(c) for c in u.T])
    pw = np.array([np.clip((w[order][1:][same] * w[order][:-1][same]).sum(0)[k] / max((w[order] ** 2).sum(0)[k], 1e-12), 0, .995) for k in range(p)])
    Lu, Lw = (np.linalg.cholesky(np.cov(a.T).reshape(p, p) + 1e-12 * np.eye(p)) for a in (u, w))
    return dict(pu=pu, pw=pw, Lu=Lu, Lw=Lw)

def _sim_nb17(f, inv, pos, nd, L, slot, hour, temp, rng):
    p = len(f['pu'])
    u = _ar_days(rng.standard_normal((nd, p)) @ f['Lu'].T, f['pu'])
    w = _ar_pos(rng.standard_normal((nd, L, p)) @ f['Lw'].T, f['pw'])
    return u[inv] + w[inv, pos]

_KINDS = {'P': (_fit_P, _sim_P), 'R': (_fit_R, _sim_R), 'nb17': (_fit_nb17, _sim_nb17)}

class Process:
    """Fitted residual process (see `fit_process`); `fits` holds the parameters per stratum."""
    def __init__(self, kind, p, fits): self.kind, self.p, self.fits = kind, p, fits

    def simulate(self, rng, units, slot, strata, hour, temp):
        """Residuals (rows x features) for any target rows of fitted strata: the scale model uses the target rows' own
        hour and temperature, consecutive sorted unique units of a stratum are consecutive days, the start is stationary."""
        units, slot, hour, temp = (np.asarray(a) for a in (units, slot, hour, temp))
        strata = np.zeros(len(units), int) if strata is None else np.asarray(strata)
        out, sim = np.zeros((len(units), self.p)), _KINDS[self.kind][1]
        for st in np.unique(strata):
            rows = np.flatnonzero(strata == st)
            out[rows] = sim(self.fits[st], *_layout(units[rows], slot[rows]), slot[rows], hour[rows], temp[rows], rng)
        return out

def fit_process(E, units, slot, strata, hour, temp, kind='P', phi_w=None, gaussian=False, scale=True, independent=False,
                persist=1.0, n_cal=200, seed=0):
    """Fits a residual process to E (rows x features) per stratum. kind 'P': scale model, Z = E / s; within-day AR(1)
    calibrated by simulation (day-demeaned lag-1 statistic inverted on the grid PHI, n_cal simulated sets per point),
    variance components and day-level AR(1) corrected for the within-day contribution, observed correlation of day means
    and of within-day innovations, joint Student-t within-day innovations (df 4 + 6 / mean excess kurtosis in [0.25, 6]).
    Options for misspecified variants (P only): phi_w overrides the within-day AR (0: none), gaussian=True normal
    innovations, scale=False a constant scale, independent=True identity correlations, persist multiplies the day-level
    and within-day AR coefficients after calibration (capped at 0.95; variances unchanged). kind 'R': scale model, AR(1)
    day means with jointly resampled innovation vectors, within-day deviations of donor fit days of the same temperature
    tercile (of the daily maximum) matched by nearest slot; only `scale` applies. kind 'nb17': the notebook 17 model (no
    scale, Gaussian). Returns a `Process`; `.simulate(rng, units, slot, strata, hour, temp)` gives residuals for any rows."""
    E = np.asarray(E, float)
    E = E.reshape(len(E), -1)
    units, slot, hour, temp = (np.asarray(a) for a in (units, slot, hour, temp))
    strata = np.zeros(len(E), int) if strata is None else np.asarray(strata)
    o = dict(phi_w=phi_w, gaussian=gaussian, scale=scale, independent=independent, persist=persist, n_cal=n_cal, seed=seed)
    fit = _KINDS[kind][0]
    fits = {}
    for st in np.unique(strata):
        r = np.flatnonzero(strata == st)
        fits[st] = fit(E[r], units[r], slot[r], hour[r], temp[r], o)
    return Process(kind, E.shape[1], fits)


# --- CRT samplers ---------------------------------------------------------------------------------------------------------
class _Draw:
    """draw(rng) -> V* = f + simulated residuals on the fitted rows; draw.f is the fitted mean."""
    def __init__(self, f, proc, units, slot, strata, temp): self.f, self.proc, self.args = f, proc, (units, slot, strata, slot, temp)
    def __call__(self, rng): return self.f + self.proc.simulate(rng, *self.args)

class _Factory:
    def __init__(self, kind, opts): self.kind, self.opts = kind, opts
    def __call__(self, V, Craw, units, slot, strata=None, groups=None, inner=5):
        """Like `inference.conditional_sampler(V, Craw, units, slot, strata, groups, inner)`: the mean is the cross-fitted
        boosted E^[V | C]; the residual process uses hour = slot and temperature = Craw[:, 1]. Returns draw(rng)."""
        V = np.asarray(V, float).reshape(len(V), -1)
        units, slot = np.asarray(units), np.asarray(slot, float)
        strata = np.zeros(len(V), int) if strata is None else np.asarray(strata)
        f = inference.project(Craw, V, units if groups is None else groups, inner)
        proc = fit_process(V - f, units, slot, strata, slot, np.asarray(Craw)[:, 1], self.kind, **self.opts)
        return _Draw(f, proc, units, slot, strata, np.asarray(Craw)[:, 1])

def factory(kind='P', **opts):
    """Picklable sampler factory with the signature of `inference.conditional_sampler`, for the residual process `kind`
    ('P', 'R', 'nb17') with the options of `fit_process` (e.g. `suite.pipeline` takes it as W['sampler'])."""
    return _Factory(kind, opts)

def crt(D, V, y, splits, groups, hour, keep, Cnull, sampler_factory, Craw, units, strata, n_perm=39, seed=0, draw=None, **kw):
    """CRT p-value of the protocol (`inference.perm_test`, V clipped at 0.005, robust scoring) with the sampler
    `sampler_factory(V, Craw, units, hour, strata=strata, groups=groups)`, or a pre-fitted `draw` (V fixed across datasets).
    Returns (observed contrast, p)."""
    if draw is None: draw = sampler_factory(V, Craw, units, hour, strata=strata, groups=groups)
    obs, p, _ = inference.perm_test(D, V, y, splits, groups, hour, n_perm=n_perm, seed=seed, keep=keep, units=units, strata=strata,
                                    Cnull=Cnull, clip=.005, robust=True, sampler=draw, **kw)
    return obs, p


# --- synthetic null worlds (W1-W3) -----------------------------------------------------------------------------------------
def _regime(rng, inv, pos, nd, L, hour, temp, Lc):
    p = len(Lc)
    shift = 0.8 * np.random.default_rng(12345).standard_normal((3, p)) @ Lc.T  # fixed draw: type x feature mean shifts
    shift -= shift.mean(0)
    s = np.empty(nd, int)
    s[0] = rng.integers(3)
    for t in range(1, nd): s[t] = s[t - 1] if rng.random() < 0.75 else (s[t - 1] + 1 + rng.integers(2)) % 3
    c, phi = np.array([0.7, 1.0, 1.6])[s][:, None], np.array([0.2, 0.4, 0.6])[s][:, None]
    u = _ar_days(rng.standard_normal((nd, p)) @ Lc.T, 0.5)
    w = _ar_pos(rng.standard_normal((nd, L, p)) @ Lc.T, phi)
    x = (shift[s] + np.sqrt(0.3) * c * u)[:, None] + np.sqrt(0.7) * c[..., None] * w
    return x[inv, pos] / np.sqrt((shift ** 2).mean(0) + (np.array([0.7, 1.0, 1.6]) ** 2).mean())

def _garch(rng, inv, pos, nd, L, hour, temp, Lc, a=0.15, b=0.75, nu=5):
    p = len(Lc)
    u = _ar_days(rng.standard_normal((nd, p)) @ Lc.T, 0.6)
    z = rng.standard_normal((nd, L, p)) @ Lc.T * _tmix(rng, (nd, L, 1), nu)
    h, eps = np.ones((nd, p)), np.empty_like(z)
    for k in range(L):  # GARCH(1,1) within the day, reset (h = unconditional variance 1) at the day start
        eps[:, k] = np.sqrt(h) * z[:, k]
        h = (1 - a - b) + a * eps[:, k] ** 2 + b * h
    x = (np.sqrt(0.3) * u)[:, None] + np.sqrt(0.7) * _ar_pos(eps, 0.4)
    sc = (1 + 0.4 * np.sin(2 * np.pi * (hour - 9) / 24)) * np.exp(0.15 * (temp - temp.mean()) / max(temp.std(), 1e-12))
    return x[inv, pos] * (sc / np.sqrt((sc ** 2).mean()))[:, None]

def _longmem(rng, inv, pos, nd, L, hour, temp, Lc, d=0.4, lags=200):
    p = len(Lc)
    psi = np.ones(lags)
    for k in range(1, lags): psi[k] = psi[k - 1] * (k - 1 + d) / k
    psi /= np.sqrt((psi ** 2).sum())  # unit variance of the truncated MA
    e = rng.standard_normal((nd + lags - 1, p)) @ Lc.T
    u = np.column_stack([np.convolve(e[:, j], psi, 'valid') for j in range(p)])
    z = (np.exp(0.5 * (rng.standard_normal((nd, L, p)) @ Lc.T)) - np.exp(0.125)) / np.sqrt(np.exp(0.25) * (np.exp(0.25) - 1))  # skewed
    x = np.sqrt(0.4) * u[:, None] + np.sqrt(0.6) * _ar_pos(z, 0.5)
    return x[inv, pos]

_WORLDS = {'regime': _regime, 'garch': _garch, 'longmem': _longmem}

def world_residuals(kind, units, slot, strata, hour, temp, sd, corr, rng):
    """Synthetic visual residuals (rows x features) of a null world outside the model class of the samplers: 'regime'
    (3-state Markov day types, stay 0.75, type mean shifts SD 0.8 from a fixed seed, scales 0.7/1.0/1.6, within-day AR
    0.2/0.4/0.6, plus a day-level AR(0.5)), 'garch' (day AR(0.6) + within-day AR(0.4) with GARCH(1,1) innovations
    alpha 0.15 beta 0.75 reset each day, t5 shocks, scale (1 + 0.4 sin(2 pi (h - 9)/24)) exp(0.15 T_z)) and 'longmem'
    (ARFIMA(0, 0.4, 0) day level with 40 % of the variance, truncated at 200 MA lags, + within-day AR(0.5) with skewed
    innovations exp(0.5 N) standardised). Components are built with unit variance in the shares stated (0.3 / 0.7 day /
    within for the first two) and the total is divided by its theoretical (regime) or sample (garch scale) RMS, so the
    per-feature SD is approximately `sd`; correlation across features is `corr` (up to the mixing of components)."""
    units, slot, hour, temp = (np.asarray(a) for a in (units, slot, hour, temp))
    strata = np.zeros(len(units), int) if strata is None else np.asarray(strata)
    sd = np.asarray(sd, float).reshape(-1)
    Lc = _chol(np.asarray(corr, float).reshape(len(sd), len(sd)))
    out = np.zeros((len(units), len(sd)))
    for st in np.unique(strata):
        rows = np.flatnonzero(strata == st)
        out[rows] = _WORLDS[kind](rng, *_layout(units[rows], slot[rows]), hour[rows], temp[rows], Lc)
    return out * sd


# --- held-out audit ---------------------------------------------------------------------------------------------------------
def acf_gap(E, units, strata, lo=2, hi=7, thr=0.1):
    """Smallest lag L (days) at which the median over features and strata of |ACF of the day means| is below thr,
    clipped to [lo, hi] (hi if it never is)."""
    E, units, strata = np.asarray(E, float).reshape(len(E), -1), np.asarray(units), np.asarray(strata)
    U = []
    for st in np.unique(strata):
        _, inv = np.unique(units[strata == st], return_inverse=True)
        U.append(np.array([E[strata == st][inv == j].mean(0) for j in range(inv.max() + 1)]))
    for L in range(1, hi + 1):
        a = [abs(np.corrcoef(u[L:, j], u[:-L, j])[0, 1]) for u in U if len(u) > L + 2 for j in range(u.shape[1])]
        if a and np.nanmedian(a) < thr: return int(np.clip(L, lo, hi))
    return hi

def _blocks(units, strata, n_blocks, gap):
    units, strata = np.asarray(units), np.asarray(strata)
    for st in np.unique(strata):
        rows = np.flatnonzero(strata == st)
        _, inv = np.unique(units[rows], return_inverse=True)
        for k, b in enumerate(np.array_split(np.arange(inv.max() + 1), n_blocks)):
            if not len(b): continue
            test, fit = np.zeros(len(units), bool), np.zeros(len(units), bool)
            test[rows[np.isin(inv, b)]] = True
            fit[rows[(inv < b[0] - gap) | (inv > b[-1] + gap)]] = True
            yield st, k, fit, test

def blocks(units, strata, n_blocks=4, gap=2):
    """Per stratum, the sorted unique days are split into n_blocks contiguous blocks; yields (fit_mask, test_mask) row
    masks for each block: the test rows are the block's days, the fit rows the same stratum's days farther than `gap`
    days (in day-index units) from the block. Strata are in sorted order, blocks in time order."""
    for _, _, fit, test in _blocks(units, strata, n_blocks, gap): yield fit, test

def _pc(x, y):
    """Pearson correlation of paired samples (NaN if fewer than 4 pairs or constant)."""
    if len(x) < 4 or x.std() == 0 or y.std() == 0: return np.nan
    return float(np.corrcoef(x, y)[0, 1])

def holdout_stats(E, units, slot, hour, temp):
    """Held-out diagnostics H1-H6 of ONE block's residuals E (rows x features), a Series indexed (family, statistic,
    feature or 'i>j'): H1 within-day lags 2 and 3 of day-demeaned residuals; H2 lag-1 autocorrelation of their squares;
    H3 lag-7 ACF of day means (NaN below 15 days); H4 corr(w_i(t), w_j(t+1)) within days, i != j; H5 share of rows with
    >= 2 features |z| > 2 (block SDs; p >= 2); H6 SD ratio of the upper to the lower temperature tercile (of the block)
    within hour bands <10, 10-14, >=14 and SD ratio hour >= 14 over hour <= 9."""
    E = np.asarray(E, float).reshape(len(E), -1)
    units, slot, hour, temp = (np.asarray(a) for a in (units, slot, hour, temp))
    p = E.shape[1]
    u, W, M = _split(E, *_layout(units, slot))
    pair = lambda A, B, k, j, l: _pc(A[:, k:, j][M[:, k:]], B[:, :-k, l][M[:, k:]])  # corr of A at t with B at t - k
    out = {}
    for j in range(p):
        out |= {('H1', 'within_lag2', j): pair(W, W, 2, j, j), ('H1', 'within_lag3', j): pair(W, W, 3, j, j),
                ('H2', 'sq_lag1', j): pair(W ** 2, W ** 2, 1, j, j),
                ('H3', 'day_lag7', j): _pc(u[7:, j], u[:-7, j]) if len(u) >= 15 else np.nan}
    out |= {('H4', 'cross_lag1', f'{i}>{j}'): pair(W, W, 1, j, i) for i in range(p) for j in range(p) if i != j}  # w_i(t), w_j(t+1)
    if p >= 2:
        z = np.abs((E - E.mean(0)) / E.std(0))
        out[('H5', 'multi_tail', 'all')] = float(((z > 2).sum(1) >= 2).mean())
    lo, hi = np.quantile(temp, [1 / 3, 2 / 3])
    def ratio(a, b):
        if a.sum() < 3 or b.sum() < 3: return np.full(p, np.nan)
        with np.errstate(all='ignore'): return E[a].std(0) / E[b].std(0)
    for name, band in [('lt10', hour < 10), ('10to14', (hour >= 10) & (hour < 14)), ('ge14', hour >= 14)]:
        r = ratio(band & (temp >= hi), band & (temp <= lo))
        out |= {('H6', f'sd_temp_{name}', j): r[j] for j in range(p)}
    r = ratio(hour >= 14, hour <= 9)
    out |= {('H6', 'sd_hour', j): r[j] for j in range(p)}
    return pd.Series(out, dtype=float)

def holdout_audit(E, units, slot, strata, hour, temp, kind, gap, n_sim=100, seed=0, n_blocks=4, **opts):
    """Held-out audit of residual process `kind`: for every (stratum, block) the process is fitted on the fit rows of
    `blocks(units, strata, n_blocks, gap)`, the test block's residuals are simulated n_sim times from the block's own rows and
    `holdout_stats` of the observed block is compared with the simulated ones (`inference.envelope`, 95 % band). Returns
    one row per statistic (family, statistic, feature, block, stratum, obs, lo, hi, p, outside); NaN statistics dropped."""
    E = np.asarray(E, float).reshape(len(E), -1)
    units, slot, strata, hour, temp = (np.asarray(a) for a in (units, slot, strata, hour, temp))
    rows = []
    for si, (st, k, fit, test) in enumerate(_blocks(units, strata, n_blocks, gap)):
        if not fit.any(): continue
        proc = fit_process(E[fit], units[fit], slot[fit], strata[fit], hour[fit], temp[fit], kind, **opts)
        rng, args = np.random.default_rng([seed, si]), [a[test] for a in (units, slot, strata, hour, temp)]
        sims = pd.DataFrame([holdout_stats(proc.simulate(rng, args[0], args[1], args[2], args[3], args[4]), args[0], args[1], args[3], args[4]) for _ in range(n_sim)])
        env = inference.envelope(holdout_stats(E[test], units[test], slot[test], hour[test], temp[test]), sims)
        env.index.names = ['family', 'statistic', 'feature']
        rows.append(env.reset_index().assign(block=k, stratum=st))
    t = pd.concat(rows, ignore_index=True)
    return t[t[['obs', 'lo', 'hi']].notna().all(axis=1)].reset_index(drop=True)

def audit_score(table):
    """Share of cells outside the band per family and the decision statistic A = the maximum over families."""
    share = table.groupby('family')['outside'].mean()
    return share, float(share.max())
