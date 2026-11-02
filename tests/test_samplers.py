import pickle

import numpy as np
import pytest

from visual_hygrometry import inference, samplers, splits

def _days(nd, per_day=13, n_strata=1, hour0=6):
    """Row layout: n_strata strata of nd days with per_day hourly rows each (unique units across strata)."""
    n = nd * per_day
    units = np.tile(np.repeat(np.arange(nd), per_day), n_strata) + np.repeat(np.arange(n_strata), n) * 1000
    slot = np.tile(np.arange(hour0, hour0 + per_day, dtype=float), nd * n_strata)
    return units, slot, np.repeat(np.arange(n_strata), n)

def _temp(units, slot, seed):
    rng = np.random.default_rng(seed)
    ud, inv = np.unique(units, return_inverse=True)
    return 14 + 8 * np.sin((slot - 8) / 24 * 2 * np.pi) + rng.normal(0, 3, len(ud))[inv]

def _ar_data(units, slot, strata, phi, rho, su, sw, rng, p=1, corr=0.0, tail=None, scale=None):
    """Day-level AR(rho) of SD su plus within-day AR(phi) of SD sw (innovations correlated by `corr` across p features,
    Student-t with `tail` df if given); the whole thing times `scale` rows."""
    L = np.linalg.cholesky(corr * np.ones((p, p)) + (1 - corr) * np.eye(p))
    E = np.zeros((len(units), p))
    for st in np.unique(strata):
        rows = np.flatnonzero(strata == st)
        _, inv = np.unique(units[rows], return_inverse=True)
        nd, u = inv.max() + 1, np.zeros(inv.max() + 1)
        u = np.zeros((nd, p))
        u[0] = rng.standard_normal(p) @ L.T
        for d in range(1, nd): u[d] = rho * u[d - 1] + np.sqrt(1 - rho ** 2) * rng.standard_normal(p) @ L.T
        w = np.zeros((len(rows), p))
        for t in range(len(rows)):
            z = rng.standard_normal(p) @ L.T
            if tail: z = z * np.sqrt((tail - 2) / rng.chisquare(tail))
            first = t == 0 or inv[t] != inv[t - 1]
            w[t] = z if first else phi * w[t - 1] + np.sqrt(1 - phi ** 2) * z
        E[rows] = su * u[inv] + sw * w
    return E if scale is None else E * scale

def _lag1(E, units, slot):
    """Day-demeaned lag-1 statistic of the first feature, as in the calibration."""
    inv, pos, nd, L = samplers._layout(units, slot)
    _, W, M = samplers._split(E[:, :1], inv, pos, nd, L)
    return float((W[:, 1:] * W[:, :-1]).sum() / (W ** 2).sum())

def test_scale_model_recovers_known_coefficients():
    rng = np.random.default_rng(0)
    n = 6000
    hour, temp = rng.uniform(6, 20, n), rng.normal(15, 4, n)
    tz = (temp - temp.mean()) / temp.std()
    b = np.array([-0.3, 0.5, -0.4, 0.35])
    s = np.sqrt(np.exp(b[0] + b[1] * np.sin(2 * np.pi * hour / 24) + b[2] * np.cos(2 * np.pi * hour / 24) + b[3] * tz))
    E = (s * rng.standard_normal(n))[:, None]
    sc = samplers.fit_scale(E, hour, temp)
    assert np.abs(sc.beta[0] - b).max() < 0.12
    assert np.corrcoef(sc(hour, temp)[:, 0], s)[0, 1] > 0.95
    assert sc.m == pytest.approx(temp.mean()) and sc.sd == pytest.approx(temp.std())  # held-out rows use these
    assert sc(np.array([12.0]), np.array([temp.mean() + temp.std()]))[0, 0] / sc(np.array([12.0]), np.array([temp.mean()]))[0, 0] == pytest.approx(np.exp(sc.beta[0, 3] / 2))
    assert samplers.fit_scale(E, hour, temp, on=False)(hour, temp).std() < 1e-9  # constant scale

def test_calibrated_within_day_ar_recovers_truth_where_naive_lag1_is_biased():
    units, slot, strata = _days(120, 13)
    E = _ar_data(units, slot, strata, 0.5, 0.5, 0.7, 1.0, np.random.default_rng(1), p=3)
    phi = samplers.fit_process(E, units, slot, strata, slot, _temp(units, slot, 2), 'P', n_cal=100).fits[0]['phi']
    assert np.abs(phi - 0.5).max() < 0.08
    naive = [_lag1(E[:, j:j + 1], units, slot) for j in range(3)]
    assert np.mean(naive) < 0.5 - 0.05 and np.mean(naive) < phi.mean() - 0.08  # day-demeaned lag-1 is biased low (notebook 17)

def test_candidate_p_refit_on_own_simulation_is_consistent():
    units, slot, strata = _days(150, 13)
    temp = _temp(units, slot, 3)
    E = _ar_data(units, slot, strata, 0.45, 0.6, 0.8, 1.0, np.random.default_rng(4), p=2, corr=0.5)
    proc = samplers.fit_process(E, units, slot, strata, slot, temp, 'P', n_cal=100)
    f = proc.fits[0]
    units2, slot2, strata2 = _days(400, 13)
    temp2 = _temp(units2, slot2, 5)
    E2 = proc.simulate(np.random.default_rng(6), units2, slot2, strata2, slot2, temp2)
    g = samplers.fit_process(E2, units2, slot2, strata2, slot2, temp2, 'P', n_cal=100).fits[0]
    assert np.abs(g['phi'] - f['phi']).max() < 0.1 and np.abs(g['ru'] - f['ru']).max() < 0.15
    assert np.abs(g['sw'] - f['sw']).max() < 0.25 and np.abs(g['su'] - f['su']).max() < 0.25
    assert np.corrcoef(E2.T)[0, 1] == pytest.approx(np.corrcoef(E.T)[0, 1], abs=0.15)

def test_heavy_tailed_innovations_give_low_df_and_heavy_simulated_tails():
    units, slot, strata = _days(120, 13)
    temp = _temp(units, slot, 7)
    heavy = _ar_data(units, slot, strata, 0.4, 0.3, 0.3, 1.0, np.random.default_rng(8), p=2, tail=4.5)
    light = _ar_data(units, slot, strata, 0.4, 0.3, 0.3, 1.0, np.random.default_rng(9), p=2)
    nu = lambda E: samplers.fit_process(E, units, slot, strata, slot, temp, 'P', n_cal=50).fits[0]['nu']
    assert nu(heavy) < 10 < nu(light) < 30
    E = samplers.fit_process(heavy, units, slot, strata, slot, temp, 'P', scale=False, n_cal=50).simulate(np.random.default_rng(0), *_days(300, 13)[:3], _days(300, 13)[1], np.zeros(300 * 13))
    z = E[:, 0] / E[:, 0].std()
    assert (z ** 4).mean() - 3 > 0.5
    assert samplers.fit_process(heavy, units, slot, strata, slot, temp, 'P', gaussian=True, n_cal=50).fits[0]['nu'] is None

def test_candidate_r_draws_donors_from_same_stratum_and_tercile():
    units, slot, strata = _days(36, 12, n_strata=2)
    rng = np.random.default_rng(10)
    temp = np.zeros(len(units))
    amp = {0: [1.0, 2.0, 3.0], 1: [10.0, 20.0, 30.0]}
    E, expect = np.zeros((len(units), 1)), np.zeros(len(units))
    sign = (-1.0) ** (np.arange(len(units)) % 12)
    for st in (0, 1):
        rows = np.flatnonzero(strata == st)
        _, inv = np.unique(units[rows], return_inverse=True)
        base = rng.permutation(inv.max() + 1) + rng.uniform(0, 0.5, inv.max() + 1)  # distinct daily maxima
        temp[rows] = base[inv] + 0.1 * (slot[rows] - 6)
        dmax = np.array([temp[rows][inv == d].max() for d in range(inv.max() + 1)])
        thr = np.quantile(dmax, [1 / 3, 2 / 3])
        terc = (dmax > thr[0]).astype(int) + (dmax > thr[1])
        expect[rows] = np.array(amp[st])[terc[inv]]
        E[rows, 0] = sign[rows] * expect[rows]  # the deviations from the day mean (zero) mark stratum and tercile
    proc = samplers.fit_process(E, units, slot, strata, slot, temp, 'R', scale=False)
    for seed in range(3):
        sim = proc.simulate(np.random.default_rng(seed), units, slot, strata, slot, temp)
        assert np.allclose(np.abs(sim[:, 0]), expect)
    hot = temp.copy()
    hot[strata == 0] += 100  # target days all in the upper tercile: donors must come from the upper tercile of stratum 0
    sim = proc.simulate(np.random.default_rng(0), units, slot, strata, slot, hot)
    assert np.allclose(np.abs(sim[strata == 0, 0]), 3.0) and np.allclose(np.abs(sim[strata == 1, 0]), expect[strata == 1])

def test_candidate_r_keeps_the_observed_day_mean_variance_with_the_corrected_ar():
    units, slot, strata = _days(92)
    temp = _temp(units, slot, 3)
    E = _ar_data(units, slot, strata, 0.0, 0.6, 1.0, 0.5, np.random.default_rng(4))
    pr = samplers.fit_process(E, units, slot, strata, slot, temp, kind='R')
    dvar = lambda X: np.array([X[units == d].mean() for d in np.unique(units)]).var()
    sims = [dvar(pr.simulate(np.random.default_rng(k), units, slot, strata, slot, temp)[:, 0]) for k in range(100)]
    assert np.mean(sims) == pytest.approx(dvar(E[:, 0]), rel=0.1)  # without the rescaling: +14 % here

def test_misspecified_options_behave_as_named():
    units, slot, strata = _days(150, 13)
    temp = _temp(units, slot, 11)
    E = _ar_data(units, slot, strata, 0.5, 0.6, 0.7, 1.0, np.random.default_rng(12), p=2, corr=0.7)
    fit = lambda **kw: samplers.fit_process(E, units, slot, strata, slot, temp, 'P', n_cal=50, **kw)
    sim = lambda proc: proc.simulate(np.random.default_rng(1), *_days(300, 13)[:2], np.zeros(300 * 13, int), _days(300, 13)[1], _temp(*_days(300, 13)[:2], 13))
    base, b, d = sim(fit()), sim(fit(phi_w=0.0)), sim(fit(independent=True))
    u2, s2 = _days(300, 13)[:2]
    assert _lag1(base, u2, s2) > 0.3 and abs(_lag1(b, u2, s2)) < 0.1  # M-b: no within-day persistence (demeaning bias only)
    assert np.corrcoef(base.T)[0, 1] > 0.4 and abs(np.corrcoef(d.T)[0, 1]) < 0.1  # M-d: independent features
    p1, p15, p3 = fit(), fit(persist=1.5), fit(persist=3.0)
    assert np.allclose(p15.fits[0]['phi'], np.minimum(1.5 * p1.fits[0]['phi'], 0.95)) and np.all(p15.fits[0]['ru'] >= p1.fits[0]['ru'])
    assert p3.fits[0]['phi'].max() == pytest.approx(0.95) and p3.fits[0]['ru'].max() <= 0.95
    c = fit(gaussian=True, scale=False)
    assert c.fits[0]['nu'] is None and not c.fits[0]['scale'].on  # M-c

def test_nb17_process_matches_conditional_sampler_coefficients():
    rng = np.random.default_rng(14)
    units, slot, strata = _days(30, 10, n_strata=2)
    temp = _temp(units, slot, 15)
    Craw = np.c_[slot, temp, rng.normal(size=len(units))]
    V = _ar_data(units, slot, strata, 0.4, 0.5, 0.6, 1.0, rng, p=2, corr=0.3) + np.c_[np.sin(slot / 3), 0.1 * temp]
    draw = inference.conditional_sampler(V, Craw, units, slot, strata=strata, groups=units // 7)
    plan = dict(zip(draw.__code__.co_freevars, [c.cell_contents for c in draw.__closure__]))['plan']
    proc = samplers.fit_process(V - draw.f, units, slot, strata, slot, temp, 'nb17')
    for (rows, inv, order, same, pu, pw, Lu, Lw, nd), st in zip(plan, (0, 1)):
        f = proc.fits[st]
        assert np.allclose(f['pu'], pu) and np.allclose(f['pw'], pw) and np.allclose(f['Lu'], Lu) and np.allclose(f['Lw'], Lw)
    sim = proc.simulate(np.random.default_rng(0), units, slot, strata, slot, temp)
    assert sim.shape == V.shape and np.isfinite(sim).all()

def test_worlds_have_shape_sd_and_their_defining_dependence():
    units, slot, strata = _days(500, 12)
    temp = _temp(units, slot, 16)
    sd, corr = np.array([1.0, 2.0]), np.array([[1, 0.5], [0.5, 1]])
    out = {k: samplers.world_residuals(k, units, slot, strata, slot, temp, sd, corr, np.random.default_rng(17)) for k in ('regime', 'garch', 'longmem')}
    for k, E in out.items():
        assert E.shape == (len(units), 2) and np.isfinite(E).all()
        assert np.allclose(E.std(0) / sd, 1, atol=0.3), k
    dm = lambda E: np.bincount(units, E[:, 1]) / 12
    acf7 = lambda x: np.corrcoef(x[7:], x[:-7])[0, 1]
    assert acf7(dm(out['longmem'])) > 0.15  # an AR(0.6) day level gives 0.6^7 = 0.03
    ar = _ar_data(units, slot, strata, 0.0, 0.6, 1.0, 0.3, np.random.default_rng(18))
    assert acf7(np.bincount(units, ar[:, 0]) / 12) < 0.1
    lay, Lc = samplers._layout(units, slot), np.linalg.cholesky(corr)
    h2 = lambda a, b: np.mean([samplers.holdout_stats(samplers._garch(np.random.default_rng(s), *lay, slot, temp, Lc, a=a, b=b), units, slot, slot, temp)[('H2', 'sq_lag1', 0)] for s in range(4)])
    assert h2(0.15, 0.75) > h2(0.0, 0.0) + 0.05  # GARCH raises the lag-1 autocorrelation of squared residuals
    assert np.corrcoef(out['garch'].T)[0, 1] > 0.2 and np.corrcoef(out['regime'].T)[0, 1] > 0.1

def test_blocks_partition_rows_with_gap_and_contiguity():
    units, _, strata = _days(40, 5, n_strata=2)
    gap, seen = 2, {0: np.zeros(len(units), int), 1: np.zeros(len(units), int)}
    got = list(samplers.blocks(units, strata, n_blocks=4, gap=gap))
    assert len(got) == 8
    for i, (fit, test) in enumerate(got):
        st = strata[test][0]
        assert (strata[test] == st).all() and (strata[fit] == st).all() and not (fit & test).any()
        seen[st] += test
        days = np.unique(units[test])
        assert len(days) == 10 and np.array_equal(days, np.arange(days[0], days[0] + 10))  # contiguous
        fd = np.unique(units[fit])
        assert np.abs(fd[:, None] - days[None]).min() > gap  # no fit day within gap days of the block
    for st in (0, 1): assert (seen[st][strata == st] == 1).all() and (seen[st][strata != st] == 0).all()
    assert samplers.acf_gap(np.zeros((len(units), 1)) + np.random.default_rng(0).normal(size=(len(units), 1)), units, strata) == 2
    slow = np.repeat(np.cumsum(np.random.default_rng(1).normal(size=40)), 5)[:, None]
    assert samplers.acf_gap(np.tile(slow, (2, 1)), units, strata) == 7

def _audit(E, units, slot, strata, temp, kind='P', **kw):
    return samplers.audit_score(samplers.holdout_audit(E, units, slot, strata, slot, temp, kind, 2, n_sim=40, n_cal=40, **kw))

def _garch_data(units, slot, strata, rng, p=2):
    """Strongly volatility-clustered within-day residuals (GARCH(1,1) alpha .3 beta .65, reset each day)."""
    _, inv = np.unique(units, return_inverse=True)
    E, h = np.zeros((len(units), p)), np.ones(p)
    for t in range(len(units)):
        if t == 0 or inv[t] != inv[t - 1]: h, prev = np.ones(p), np.zeros(p)
        e = np.sqrt(h) * rng.standard_normal(p)
        E[t] = e
        h = 0.05 + 0.3 * e ** 2 + 0.65 * h
    return E

def test_holdout_audit_small_for_well_specified_p_and_flags_volatility_clustering():
    units, slot, strata = _days(100, 12, n_strata=2)
    temp = _temp(units, slot, 19)
    good = _ar_data(units, slot, strata, 0.5, 0.5, 0.7, 1.0, np.random.default_rng(20), p=2, corr=0.5)
    tab = samplers.holdout_audit(good, units, slot, strata, slot, temp, 'P', 2, n_sim=40, n_cal=40)
    share, A = samplers.audit_score(tab)
    assert set(share.index) == {'H1', 'H2', 'H3', 'H4', 'H5', 'H6'} and A <= 0.3
    assert {'family', 'statistic', 'feature', 'block', 'stratum', 'outside'} <= set(tab.columns) and tab.block.nunique() == 4
    bad = _garch_data(units, slot, strata, np.random.default_rng(21))
    share_bad, _ = _audit(bad, units, slot, strata, temp)
    assert share_bad['H2'] > share['H2'] + 0.3
    assert samplers.audit_score(samplers.holdout_audit(good, units, slot, strata, slot, temp, 'nb17', 2, n_sim=20))[1] >= 0  # nb17 audits too

def test_factory_is_picklable_and_crt_runs():
    rng = np.random.default_rng(22)
    g, slot = np.repeat(np.arange(40), 8), np.tile(np.arange(8.0), 40)
    C = np.c_[slot, rng.normal(size=len(g)), np.sin(slot)]
    V = (0.3 * C[:, 1] + rng.normal(size=len(g)) + rng.normal(size=40)[g])[:, None]
    y = C[:, 1] + rng.normal(size=len(g))
    fac = pickle.loads(pickle.dumps(samplers.factory('P', n_cal=20)))
    draw = fac(V, C, g, slot, strata=None, groups=g // 5)
    star = draw(np.random.default_rng(0))
    assert star.shape == V.shape and draw.f.shape == V.shape and not np.allclose(star, V)
    assert np.allclose(pickle.loads(pickle.dumps(draw))(np.random.default_rng(0)), star)
    sp = splits.kfold(splits.assign_folds(g, 4))
    for d in (None, draw):
        obs, p = samplers.crt(C, V, y, sp, g // 5, slot, None, C, samplers.factory('R'), C, g, np.zeros(len(g), int), n_perm=4, draw=d)
        assert np.isfinite(obs) and 0 < p <= 1
