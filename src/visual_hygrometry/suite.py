"""Synthetic multi-season records and the M1 inference protocol on them (notebooks 14 and 16).

A world is a dict: `spec` (synthetic.Node SEM with constant means), optional `modify(df, rng)`, `vis` (visual columns),
`truth` (I(D; V | C), nats) and `illum` (clear-sky index in C: E2_illum). Every record gets the solar `climate`: T and
D follow lagged insolation and D has a dawn minimum tied to sunrise, so the diurnal cycle changes with sunrise and day
length across June–August at CPER's location. The protocol (`pipeline`) is the one validated in notebook 16:
capacity selection among CANDIDATES, clipped V, leave-one-season-out cross-fit, the shift and CRT nulls, the season-
cluster interval, the chronological gain and both adequacy auditors (stored as one-sided lower bounds).
"""
import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy import special, stats
from scipy.special import logsumexp
from scipy.stats import norm

from . import data, inference, policy, scoring, splits, synthetic, worlds
from .synthetic import Node

LAT, LON, OFF = 40.8155, -104.7456, -7  # CPER
DOY0, N_DAYS, PER_DAY, HOURS, N_SEAS, N_FUT = 152, 92, 14, (6, 20), 4, 3
KNOTS, DOY_K, DOY_F, ILL_K = np.arange(-4, 45, 4.0), np.arange(140, 261, 15.0), np.arange(146, 251, 7.5), np.linspace(.1, 1.3, 7)
CANDIDATES = ['L3', 'L4', 'S', 'S4']
N_NULL = 39
RFF_SCALES = [2.0, 3.0, 20.0, 10.0, 0.15]  # hour (h), T (K), day of year (d), solar elevation (deg), daylight fraction; K: 0.15

def spec(gamma=0.0, slow=(0.0, 0.0), cloud=(0.0, 0.0, 0.0), r_persist=.5, v_persist=.5, r_day=.6, v_day=.4, beta=.4, illum=False):
    """Hourly SEM with constant means; diurnal and seasonal cycles are added by `climate` from solar geometry.
    S: slow shared state (day-level, AR 0.95 across days); K: cloudiness, observed as a clear-sky index if illum."""
    (a, b), (cT, cD, cV) = slow, cloud
    s = {'slow': Node(sd=1.0, day=1.0, persist=.95), 'cloud': Node(sd=1.0, day=.6, ar=.8, persist=.5),
         'temp_cond_c': Node({'cloud': cT}, 3.0, mean=_const(16.0), day=.7, ar=.8, persist=.6),
         'dres': Node(sd=2.0, day=r_day, ar=.6, persist=r_persist),
         'd_ref_k': Node({'temp_cond_c': beta, 'dres': 1.0, 'slow': a, 'cloud': cD}, mean=_const(1.0)),
         'vis_moist': Node({'dres': gamma, 'slow': b, 'cloud': cV}, 1.0, day=v_day, ar=.5, persist=v_persist)}
    return s | ({'clearsky_k': Node({'cloud': -.15}, mean=_const(.7))} if illum else {})


class _const:
    """Picklable constant mean function of hour."""
    def __init__(self, c): self.c = c
    def __call__(self, h): return np.full_like(np.asarray(h, float), self.c)

def sun(df, lag=0.0, lat=LAT, lon=LON, off=OFF):
    """Positive sine of solar elevation `lag` hours earlier (heating lags the sun)."""
    return np.clip(np.sin(np.radians(data.solar(df.doy, df.hour - lag, lat, lon, off).solar_elev_deg.to_numpy())), 0, None)

def climate(df, rng, t_amp=9.0, t_lag=2.0, d_amp=6.0, d_lag=2.5, dawn=1.5):
    """Solar-driven diurnal cycles: T and D follow lagged insolation and D has a dawn minimum tied to sunrise. Every term
    is a deterministic function of (date, time), so it belongs to C."""
    fr = data.solar(df.doy, df.hour, LAT, LON, OFF).solar_dayfrac.to_numpy()
    df['temp_cond_c'] = df.temp_cond_c + t_amp * sun(df, t_lag)
    df['d_ref_k'] = df.d_ref_k + d_amp * sun(df, d_lag) - dawn * np.exp(-6 * np.clip(fr, 0, None)) + 0.4 * t_amp * sun(df, t_lag)
    return df

def make(W, n_seasons, seed):
    """n_seasons independent seasons of N_DAYS days (June–August), climate and world modification applied, solar
    geometry attached."""
    parts = []
    for y in range(n_seasons):
        d = synthetic.simulate(W['spec'], N_DAYS, PER_DAY, HOURS, seed=seed * 13 + y)
        parts.append(d.assign(year=y, doy=DOY0 + d.day, day=d.day + y * N_DAYS))
    df = pd.concat(parts, ignore_index=True)
    df = pd.concat([df, data.fourier(df.hour, 24, 2, 'hour')], axis=1).assign(hour_local=df.hour, ref_sensor_id='ref', cond_sensor_id='cond')
    rng = np.random.default_rng(seed + 7)
    df = W.get('climate', climate)(df, rng)
    if 'modify' in W: df = W['modify'](df, rng)
    return pd.concat([df, data.solar(df.doy, df.hour_local, LAT, LON, OFF)], axis=1)

def pipeline(df, W, full=True, force=None):
    """The protocol on one simulated record (seasons < N_SEAS analysed; later seasons only score the frozen chronological
    models). force: a context level used instead of the capacity search (diagnostics)."""
    s, extra = (df.year < N_SEAS).to_numpy(), []
    if W.get('illum'):
        I = data.spline(df.clearsky_k, ILL_K, 'illum_spl')
        df, extra = pd.concat([df, I], axis=1), list(I)
    dfl, lv = worlds.add_context_levels(df, KNOTS, DOY_K, DOY_F, hour_season=True, solar=True)
    _, _, y, _ = policy.select_sci(dfl, 'e2_illum' if W.get('illum') else 'e2', lv['S4'] + extra, W['vis'])  # contract check
    g, yr, doy = df.day.to_numpy(), df.year.to_numpy(), df.doy.to_numpy()
    seasonal = np.column_stack([dfl[c].to_numpy() * (yr == k) for k in range(N_SEAS) for c in dfl if c.startswith('doy_spl')])  # season-specific curves
    y, V, Cnull = y.to_numpy(), df[W['vis']].to_numpy(), np.c_[dfl[lv['S4'] + extra].to_numpy(), seasonal][s]
    wk = yr * 14 + (doy - DOY0) // 7
    raw = df[['hour_local', 'temp_cond_c', 'doy', 'solar_elev_deg', 'solar_dayfrac'] + (['clearsky_k'] if W.get('illum') else [])].to_numpy()
    names = [force] if force else CANDIDATES
    levels = lambda d, sp: [worlds.split_levels(d, sp, KNOTS, DOY_K, DOY_F, extra, hour_season=True, solar=True)[0][k] for k in names]
    sp = splits.kfold(yr[s])
    keep = scoring.support_mask(raw[s][:, :2], sp)
    D, chosen = inference.select_capacity(levels(df[s].reset_index(drop=True), sp), y[s], sp, wk[s], robust=True)
    r = scoring.contrast(D, [np.c_[d, v] for d, v in zip(D, inference.clip_to_training(V[s], sp))], y[s], sp, wk[s], keep=keep, robust=True)
    dz = np.full(s.sum(), np.nan)
    dz[r.scored] = r.d
    seas = pd.Series(dz).groupby(yr[s]).mean().to_numpy()
    q = stats.t.ppf(.975, len(seas) - 1) * seas.std(ddof=1) / np.sqrt(len(seas))
    wlo, whi = inference.cluster_interval(r.d, wk[s][r.scored])
    out = dict(est=r.mean, seas_lo=seas.mean() - q, seas_hi=seas.mean() + q, week_lo=wlo, week_hi=whi, level=np.mean(chosen), excluded=1 - keep.mean())
    fit, ev, fut = s & (yr < N_SEAS - 1), s & (yr == N_SEAS - 1), ~s
    spc = [(fit, ev | fut)]
    Dc, _ = inference.select_capacity(levels(df, spc), y, spc, wk, robust=True)
    rc = scoring.contrast(Dc, [np.c_[Dc[0], inference.clip_to_training(V, spc)[0]]], y, spc, wk, keep=scoring.support_mask(raw[:, :2], spc), robust=True)
    dc = np.full(len(y), np.nan)
    dc[rc.scored] = rc.d
    out |= dict(G=np.nanmean(dc[ev]), G_target=np.nanmean(dc[fut]))
    if not full: return out
    hour, ys, gs, ws, ss = df.hour_local.to_numpy()[s], y[s], g[s], wk[s], yr[s]
    test = lambda **kw: inference.perm_test(D, V[s], ys, sp, ws, hour, keep=keep, units=gs, strata=ss, Cnull=Cnull, clip=.005, robust=True, n_perm=N_NULL, **kw)[1]
    out |= dict(p_shift=test(shift_min=7, max_shifts=N_NULL),
                p_crt=test(seed=1, sampler=inference.conditional_sampler(V[s], np.c_[raw[s], ss], gs, hour, strata=ss, groups=ws)))
    ok = keep & np.isfinite(r.pred_c[2])
    lb = lambda d: inference.cluster_lower(d[ok], ws[ok])
    R = inference.rff(raw[s], RFF_SCALES + [0.15] * (raw.shape[1] - 5))
    P = inference.smooth_projection_splits(np.c_[Cnull, R], V[s], sp, ws)
    L1 = worlds.split_levels(df[s].reset_index(drop=True), sp, KNOTS, DOY_K, DOY_F, extra)[0]['L1']
    for tag, Cx, ls_c in [('', D, r.pred_c[2]), ('_L1', L1, scoring.crossfit(L1, ys, sp, ws, robust=True)[2])]:  # chosen; deliberately misspecified
        out['audit_lb' + tag] = lb(inference.challenger(Cx, R, ys, sp, ws, robust=True)[2] - ls_c)
        out['repair_lb' + tag] = lb(inference.repair_gain(Cx, P, ys, sp, ws, ls_c=ls_c, robust=True))
    return out

def one_rep(W, seed):
    df = make(W, N_SEAS + N_FUT, seed)
    out = dict(seed=seed) | pipeline(df, W)
    s, rng = (df.year < N_SEAS).to_numpy(), np.random.default_rng(seed + 3)
    a = pipeline(df[~(s & (rng.random(len(df)) < .01))].reset_index(drop=True), W, full=False)
    b = pipeline(df[~(s & (df.d_ref_k.to_numpy() <= np.quantile(df.d_ref_k[s], .01)))].reset_index(drop=True), W, full=False)
    return out | dict(dest_rand=a['est'] - out['est'], dest_rare=b['est'] - out['est'])

def safe_rep(W, seed):
    """A replicate that raises is recorded with its error and counted, never dropped."""
    try: return one_rep(W, seed)
    except Exception as e: return dict(seed=seed, error=f'{type(e).__name__}: {e}')

def run(worlds_, start, reps, stride=1000, n_jobs=16):
    """Replicates of every world, each world with its own seed range (start + stride * world index)."""
    par = Parallel(n_jobs=n_jobs, max_nbytes=None)
    return {k: pd.DataFrame(par(delayed(safe_rep)(W, start + stride * i + j) for j in range(reps))) for i, (k, W) in enumerate(worlds_.items())}


q90 = lambda x: np.quantile(np.abs(x), .9)

def summarise(worlds_, res, tau_audit=0.0, tau_repair=0.0):
    """Per world: Type I / power of both nulls, estimate vs E2 and vs the design's own G, interval coverage, stability,
    auditor flag rates (lower bound > tau) on the chosen and on the deliberately misspecified (L1) context."""
    rows = []
    for k, a in res.items():
        t, failed = worlds_[k]['truth'], int(a['error'].notna().sum()) if 'error' in a else 0
        a = a[a['error'].isna()] if 'error' in a else a
        tg = a.G_target.mean()  # expected future-season gain of models fitted on N_SEAS - 1 seasons
        cover = lambda lo, hi, x: ((a[lo] <= x) & (a[hi] >= x)).mean()
        rows.append(dict(world=k, truth=t, G_design=tg, rej_shift=(a.p_shift <= .05).mean(), rej_crt=(a.p_crt <= .05).mean(), est=a.est.mean(), bias=a.est.mean() - t,
                         est_minus_G=a.est.mean() - tg, cover_G=cover('seas_lo', 'seas_hi', tg), cover_E2=cover('seas_lo', 'seas_hi', t), cover_week_G=cover('week_lo', 'week_hi', tg),
                         chrono_G=a.G.mean(), dest_rand_q90=q90(a.dest_rand), dest_rare_q90=q90(a.dest_rare),
                         audit=(a.audit_lb > tau_audit).mean(), audit_L1=(a.audit_lb_L1 > tau_audit).mean(),
                         repair=(a.repair_lb > tau_repair).mean(), repair_L1=(a.repair_lb_L1 > tau_repair).mean(), level=a.level.mean(), failed=failed))
    return pd.DataFrame(rows).set_index('world')


# --- world components ---------------------------------------------------------------------------------------------
def sun_clock(amp, sd, lag=0.0):
    """Image = brightness proportional to (lagged) insolation, plus the image noise scaled by sd."""
    def f(df, rng):
        df['vis_moist'] = df.vis_moist * sd + amp * sun(df, lag)
        return df
    return f

def encodes(term, scale, v_sd):
    """D += term(df); the image `vis_ctx` = scale * term + noise: a context function the image tracks (a null)."""
    def f(df, rng):
        x = term(df)
        df['d_ref_k'] = df.d_ref_k + x
        df['vis_ctx'] = scale * x + rng.normal(0, v_sd, len(df))
        return df
    return f

def markov(p_stay, n, rng):
    """Two-state Markov chain over n days, stationary probability 0.5."""
    z = np.empty(n, bool)
    z[0] = rng.random() < .5
    for t in range(1, n): z[t] = z[t - 1] if rng.random() < p_stay else ~z[t - 1]
    return z

def regimes(p_d, p_v, mu=-2.0, sd=1.5, nu=1.0, shared=False):
    """Day-level weather regimes: D shifted by mu and its residual scaled by sd in regime 1; image shifted by nu in its
    regime. shared=False: independent chains (a null); shared=True: one chain for both (a common cause outside C)."""
    def f(df, rng):
        n = df.day.max() + 1
        zd = markov(p_d, n, rng)
        zv = zd if shared else markov(p_v, n, rng)
        df['d_ref_k'] = df.d_ref_k + np.where(zd[df.day], mu, 0) + np.where(zd[df.day], sd - 1, 0) * df.dres
        df['vis_moist'] = df.vis_moist + np.where(zv[df.day], nu, 0)
        return df
    return f

def vegetation(amp=(.5, 2.0), mid=(175, 215), width=8, camera_from=2, gain=1.4, offset=-.8):
    """Season-specific greening (random amplitude and timing per season) and a camera change from season camera_from."""
    def f(df, rng):
        a, m = rng.uniform(*amp, df.year.max() + 1), rng.uniform(*mid, df.year.max() + 1)
        df['vis_moist'] = df.vis_moist + a[df.year] * special.expit((df.doy - m[df.year]) / width)
        late = df.year >= camera_from
        df.loc[late, 'vis_moist'] = gain * df.loc[late, 'vis_moist'] + offset
        return df
    return f

def season_x_hour(d): return 0.8 * np.sin(2 * np.pi * (d.hour - 9) / 24) * np.tanh((d.doy - 200) / 15)

def gam(c): return np.sqrt(np.expm1(2 * c)) / 2  # image coefficient giving I = c for moisture residual SD 2, image noise SD 1

def cmi(sp, given=('temp_cond_c',)): return synthetic.cmi(sp, 'd_ref_k', 'vis_moist', list(given))

def truth_shared_regime(pi, mu_d, sd_d, nu_v, n=2_000_000, seed=0):
    """I(D; V | C) when a latent two-state regime shifts the D residual (mean mu_d, SD sd_d) and the image (mean nu_v,
    noise SD 1): exact mixture densities, Monte Carlo over n draws."""
    rng = np.random.default_rng(seed)
    r = rng.random(n) < pi
    d = np.where(r, mu_d[1], mu_d[0]) + np.where(r, sd_d[1], sd_d[0]) * rng.standard_normal(n)
    v = np.where(r, nu_v[1], nu_v[0]) + rng.standard_normal(n)
    lw, md, sd, nv = np.log([1 - pi, pi]), np.array(mu_d), np.array(sd_d), np.array(nu_v)
    joint = logsumexp(lw + norm.logpdf(d[:, None], md, sd) + norm.logpdf(v[:, None], nv, 1), axis=1)
    return np.mean(joint - logsumexp(lw + norm.logpdf(d[:, None], md, sd), axis=1) - logsumexp(lw + norm.logpdf(v[:, None], nv, 1), axis=1))