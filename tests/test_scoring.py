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
