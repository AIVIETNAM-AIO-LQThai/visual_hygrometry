import numpy as np
import pytest
from scipy import integrate, stats

from visual_hygrometry import scoring, splits, synthetic
from visual_hygrometry.synthetic import Node


def test_gauss_scores_match_scipy():
    y, mu, sd = np.array([0.3, -1.2, 2.0]), np.array([0.0, 0.5, 1.0]), np.array([1.0, 0.7, 2.0])
    assert np.allclose(scoring.gauss_ls(y, mu, sd), stats.norm.logpdf(y, mu, sd))
    cens = np.array([False, True, False])
    assert scoring.gauss_ls(y, mu, sd, cens)[1] == pytest.approx(stats.norm.logcdf(-1.2, .5, .7))
    num = integrate.quad(lambda x: (stats.norm.cdf(x, 1, 2) - (x >= 2.0)) ** 2, -30, 30, points=[2.0])[0]
    assert scoring.gauss_crps(2.0, 1.0, 2.0) == pytest.approx(num, rel=1e-6)


def test_block_bootstrap_resamples_groups():
    x, g = np.r_[np.zeros(10), np.ones(10)], np.repeat([0, 1], 10)
    b = scoring.block_bootstrap(x, g, 4000)
    assert set(np.round(b, 6)) <= {0.0, 0.5, 1.0}  # whole groups move together
    assert b.mean() == pytest.approx(0.5, abs=0.02)


def test_ridge_path_matches_sklearn():
    rng = np.random.default_rng(0)
    X, y = rng.normal(size=(300, 4)) * [1, 10, .1, 3], rng.normal(size=300)
    cv = [(np.arange(200), np.arange(200, 300))]
    P = scoring.ridge_oof(X, y, cv, np.array([0.1, 10.0]))
    for j, a in enumerate([0.1, 10.0]):
        assert np.allclose(P[200:, j], scoring.ridge(a).fit(X[:200], y[:200]).predict(X[200:]), atol=1e-10)


def test_hetero_variance_targets_mean_square_not_geometric_mean():
    """Unexplained regime heteroscedasticity must give the arithmetic mean variance, explained one the regime variances."""
    rng = np.random.default_rng(1)
    reg = np.repeat(rng.integers(0, 2, 200), 20)
    y = np.where(reg, .7, 2.5) * rng.normal(size=len(reg))
    g, sp = np.repeat(np.arange(200), 20), [(np.arange(4000) < 3000, np.arange(4000) >= 3000)]
    _, sd_c, _ = scoring.crossfit(rng.normal(size=(4000, 1)), y, sp, g, var='hetero')
    _, sd_v, _ = scoring.crossfit(reg[:, None].astype(float), y, sp, g, var='hetero')
    assert np.nanmean(sd_c ** 2) == pytest.approx(np.mean(y[:3000] ** 2), rel=.05)
    assert np.nanmean(sd_v[reg == 1] ** 2) == pytest.approx(.49, rel=.15) and np.nanmean(sd_v[reg == 0] ** 2) == pytest.approx(6.25, rel=.15)


def test_cmi_matches_closed_form():
    s, g, tau = 2.0, 0.7, 1.3
    spec = {'r': Node(sd=s), 'v': Node({'r': g}, tau)}
    assert synthetic.cmi(spec, 'r', 'v') == pytest.approx(0.5 * np.log(1 + g ** 2 * s ** 2 / tau ** 2))
    spec = {'t': Node(sd=2.0), 'd': Node({'t': 0.5}, 1.0), 'v': Node({'t': 1.0}, 0.5)}
    assert synthetic.cmi(spec, 'd', 'v', 't') == pytest.approx(0.0, abs=1e-12)


def _world(gamma):
    return {'temp': Node(sd=3, mean=lambda h: 20 + 5 * np.cos(2 * np.pi * (h - 15) / 24), day=.7, ar=.95),
            'dres': Node(sd=2, day=.5, ar=.9),
            'd': Node({'temp': .4, 'dres': 1}, mean=lambda h: 4 + 2 * np.cos(2 * np.pi * (h - 15) / 24)),
            'vis': Node({'dres': gamma}, 1.0)}


@pytest.mark.parametrize('gamma', [0.0, 0.3])
def test_contrast_unbiased_over_replicates(gamma):
    """Single-sample spread at 60 days is ~0.02 nats (sampling, shared with the true-model score); bias must be far smaller.
    Coverage of the bootstrap interval is a repeated-sampling property studied in notebook 01, not a unit test."""
    spec = _world(gamma)
    truth = synthetic.cmi(spec, 'd', 'vis', 'temp')
    est = []
    for seed in range(12):
        df = synthetic.simulate(spec, n_days=60, seed=seed)
        H = np.c_[np.sin(2 * np.pi * df.hour / 24), np.cos(2 * np.pi * df.hour / 24)]
        sp = splits.kfold(splits.assign_folds(df.day.to_numpy(), 5))
        est.append(scoring.contrast(np.c_[H, df.temp], np.c_[H, df.temp, df.vis], df.d.to_numpy(), sp, df.day.to_numpy()).mean)
    assert abs(np.mean(est) - truth) < 0.015


def _censored_data(n_days=150, per_day=20, seed=4):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n_days * per_day, 2))
    d = 1.5 + X @ [1.0, -0.5] + rng.normal(0, 1.2, len(X))
    cens = d < 1.0
    return X, np.where(cens, 1.0, d), cens, np.repeat(np.arange(n_days), per_day)


def test_tobit_recovers_parameters_where_naive_fit_is_biased():
    X, y, cens, _ = _censored_data()
    assert 0.2 < cens.mean() < 0.5
    th = scoring._tobit(X, y, cens, alpha=1e-6)
    assert np.allclose(th[:3], [1.5, 1.0, -0.5], atol=0.08) and np.exp(th[-1]) == pytest.approx(1.2, rel=.05)
    naive = np.linalg.lstsq(np.c_[np.ones(len(X)), X], y, rcond=None)[0]
    assert abs(naive[1] - 1.0) > 0.1  # treating bounds as exact values attenuates the slope


def test_censored_crossfit_scores_bounds_with_cdf():
    X, y, cens, g = _censored_data()
    sp = splits.kfold(splits.assign_folds(g, 5))
    mu, sd, ls = scoring.crossfit(X, y, sp, g, censored=cens)
    assert np.nanmean(sd) == pytest.approx(1.2, rel=.08)
    assert np.allclose(ls[cens], stats.norm.logcdf(y[cens], mu[cens], sd[cens]))
    with pytest.raises(NotImplementedError):
        scoring.crossfit(X, y, sp, g, censored=cens, var='hetero')


def test_binned_family_handles_censoring_by_lowest_bin():
    X, y, cens, g = _censored_data(n_days=60)
    sp = splits.kfold(splits.assign_folds(g, 3))
    P, b, ls = scoring.crossfit_binned(X, y, sp, g, edges=[1.0, 2.0, 3.0, 4.0], Cs=(1.0,), inner=3, censored=cens)
    assert (b[cens] == 0).all() and np.allclose(P.sum(1), 1) and np.allclose(ls, np.log(P[np.arange(len(b)), b]))
    with pytest.raises(ValueError, match='lowest bin'):
        scoring.crossfit_binned(X, y, sp, g, edges=[0.5, 2.0], censored=cens)


def test_oracle_conditional_matches_cmi():
    spec = _world(0.4)
    df = synthetic.simulate(spec, n_days=400, seed=5)
    mc, sc = synthetic.conditional(spec, df, 'd', ['temp'])
    mv, sv = synthetic.conditional(spec, df, 'd', ['temp', 'vis'])
    d = scoring.gauss_ls(df.d, mv, sv) - scoring.gauss_ls(df.d, mc, sc)
    assert d.mean() == pytest.approx(synthetic.cmi(spec, 'd', 'vis', 'temp'), abs=0.01)


def test_nearly_empty_column_cannot_explode_held_out_rows():
    rng = np.random.default_rng(6)
    g = np.repeat(np.arange(50), 20)
    x, y = rng.normal(size=len(g)), rng.normal(size=len(g))
    edge = np.where(np.arange(len(g)) < 2, 1e-4, 0.0)  # basis function with almost no training support
    edge[-20:] = 0.6                                    # ... but fully active on the held-out day
    sp = [(g < 49, g == 49)]
    mu, sd, ls = scoring.crossfit(np.c_[x, edge], y, sp, g)
    assert np.all(np.abs(mu[g == 49]) < 3) and np.all(ls[g == 49] > -10)


def test_light_context_penalty_shrinks_context_less():
    rng = np.random.default_rng(7)
    g = np.repeat(np.arange(40), 25)
    X = rng.normal(size=(len(g), 2))
    y = 3 * X[:, 0] + 0.2 * X[:, 1] + rng.normal(size=len(g))
    sp = [(g < 30, g >= 30)]
    assert np.allclose(scoring.crossfit(X, y, sp, g)[0], scoring.crossfit(X, y, sp, g, ctx_cols=1, ctx_pen=1.0)[0], equal_nan=True)
    tr = g < 30
    m, s = scoring._standardise(X, tr, ctx_cols=1, ctx_pen=0.01)
    assert s[0] == pytest.approx(0.1 * X[tr, 0].std()) and s[1] == pytest.approx(X[tr, 1].std())


def test_robust_score_is_proper_mixture_with_bounded_tail_growth():
    mu, sd = np.zeros(3), np.ones(3)
    y = np.array([0.0, 3.0, 50.0])
    ls = scoring.gauss_ls(y, mu, sd, robust=True)
    mix = lambda x: .99 * stats.norm.pdf(x) + .01 * stats.cauchy.pdf(x, scale=4)
    assert np.allclose(ls, np.log(mix(y)))
    assert integrate.quad(mix, -np.inf, np.inf)[0] == pytest.approx(1.0, abs=1e-6)
    assert ls[2] > -15 and scoring.gauss_ls(y, mu, sd)[2] < -1000  # 50 sd error: ~-13 nats instead of -1251
    c = scoring.gauss_ls(np.array([-1.0]), np.zeros(1), np.ones(1), censored=np.array([True]), robust=True)
    assert c[0] == pytest.approx(np.log(.99 * stats.norm.cdf(-1) + .01 * stats.cauchy.cdf(-1, scale=4)))


def test_support_mask_uses_training_rows_only():
    R = np.r_[np.linspace(0, 10, 100), [-5.0, 5.0, 25.0]]
    sp = [(np.arange(103) < 100, np.arange(103) >= 100)]
    keep = scoring.support_mask(R, sp, q=0.0)
    assert keep.tolist()[-3:] == [False, True, False] and not keep[:100].any()
    g = np.repeat(np.arange(103), 1)
    y = np.r_[np.random.default_rng(0).normal(size=100), 0, 0, 0]
    r = scoring.contrast(R[:, None], np.c_[R, R], y, sp, g, keep=keep)
    assert r.scored.sum() == 1 and len(r.d) == 1


def test_persistent_day_levels_keep_marginal_variance():
    spec = {'x': synthetic.Node(sd=2.0, day=1.0, persist=0.8)}
    df = synthetic.simulate(spec, 4000, per_day=2, seed=1)
    d = df.groupby('day').x.first().to_numpy()
    assert d.var() == pytest.approx(4.0, rel=0.1) and np.corrcoef(d[1:], d[:-1])[0, 1] == pytest.approx(0.8, abs=0.03)
    same = synthetic.simulate({'x': synthetic.Node(sd=2.0, day=1.0)}, 50, seed=2).x
    assert np.allclose(same, synthetic.simulate({'x': synthetic.Node(sd=2.0, day=1.0, persist=0.0)}, 50, seed=2).x)


def test_per_split_design_list_equals_fixed_design():
    rng = np.random.default_rng(9)
    g = np.repeat(np.arange(30), 10)
    X, y = rng.normal(size=(300, 2)), rng.normal(size=300)
    sp = splits.kfold(splits.assign_folds(g, 3))
    assert np.allclose(scoring.crossfit(X, y, sp, g)[2], scoring.crossfit([X] * 3, y, sp, g)[2])
    z9 = lambda r: scoring.gauss_ls(np.array([9.0]), np.zeros(1), np.ones(1), robust=r)[0]
    assert z9((0.01, 4.0)) == pytest.approx(z9(True)) and z9((0.02, 4.0)) > z9(True)
