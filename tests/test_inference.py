import numpy as np
import pytest

from visual_hygrometry import inference, scoring, splits


def test_cluster_se_equal_groups_is_se_of_group_means():
    rng = np.random.default_rng(0)
    g = np.repeat(np.arange(30), 10)
    d = rng.normal(size=30)[g] + rng.normal(size=300)
    m, se, G = inference.cluster_se(d, g)
    means = np.bincount(g, d) / 10
    assert G == 30 and m == pytest.approx(d.mean()) and se == pytest.approx(means.std(ddof=1) / np.sqrt(30))
    lo, hi = inference.cluster_interval(d, g)
    assert lo < inference.cluster_lower(d, g) < m < hi


def _grid(signal, seed, n_days=40, per_day=12):
    rng = np.random.default_rng(seed)
    g, slot = np.repeat(np.arange(n_days), per_day), np.tile(np.arange(per_day), n_days)
    C = np.c_[np.sin(slot / 2), rng.normal(size=len(g))]
    r = rng.normal(size=n_days)[g] + rng.normal(size=len(g))
    V = (signal * r + rng.normal(size=len(g)) + 0.5 * C[:, 1])[:, None]
    return C, V, C @ [1.0, 0.5] + r, g, slot


def test_perm_test_rejects_signal_and_not_null():
    for signal, expect in [(1.0, lambda p: p <= 0.05), (0.0, lambda p: p > 0.05)]:
        C, V, y, g, slot = _grid(signal, seed=1)
        sp = splits.kfold(splits.assign_folds(g, 4))
        obs, p, null = inference.perm_test(C, V, y, sp, g, slot, n_perm=19)
        assert expect(p) and len(null) == 19


def test_perm_test_needs_complete_grid():
    C, V, y, g, slot = _grid(0.0, seed=2)
    keep = np.arange(len(g)) != 5
    with pytest.raises(ValueError, match='every slot'):
        inference.perm_test(C[keep], V[keep], y[keep], splits.kfold(splits.assign_folds(g[keep], 4)), g[keep], slot[keep], n_perm=3)
