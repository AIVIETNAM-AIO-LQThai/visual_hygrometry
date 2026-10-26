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


def test_donors_exact_on_complete_grid_and_nearest_otherwise():
    g, slot = np.repeat(np.arange(6), 4), np.tile(np.arange(4.0), 6)
    src = inference.donor_sampler(g, slot)(np.random.default_rng(0))
    assert np.array_equal(slot[src], slot) and len(set(zip(g, g[src]))) == 6  # whole units move together
    keep = ~((g == 2) & (slot == 1))  # one missing frame
    src = inference.donor_sampler(g[keep], slot[keep])(np.random.default_rng(1))
    assert np.abs(slot[keep][src] - slot[keep]).max() <= 1
    strata = (g >= 3).astype(int)
    for seed in range(5):
        src = inference.donor_sampler(g, slot, strata)(np.random.default_rng(seed))
        assert np.array_equal(strata[src], strata)


def test_perm_test_runs_on_incomplete_grid_with_week_units():
    C, V, y, g, slot = _grid(0.0, seed=2)
    keep = np.random.default_rng(3).random(len(g)) > 0.1
    sp = splits.kfold(splits.assign_folds(g[keep], 4))
    obs, p, null = inference.perm_test(C[keep], V[keep], y[keep], sp, g[keep], slot[keep], n_perm=5, units=g[keep] // 5)
    assert 0 < p <= 1 and len(null) == 5


def test_project_splits_never_uses_test_rows():
    rng = np.random.default_rng(8)
    g = np.repeat(np.arange(40), 10)
    C = rng.normal(size=(len(g), 2))
    V = (C[:, 0] ** 2 + rng.normal(0, .3, len(g)))[:, None]
    sp = splits.kfold(splits.assign_folds(g, 4))
    P = inference.project_splits(C, V, sp, g)
    V2 = V.copy()
    V2[sp[0][1]] = 1e6  # corrupt the first split's test-row visuals
    P2 = inference.project_splits(C, V2, sp, g)
    tr, te = sp[0]
    assert np.allclose(P[0][tr | te], P2[0][tr | te]) and not np.isnan(P[0][tr | te]).any()


def test_project_recovers_context_function_without_copying_noise():
    rng = np.random.default_rng(3)
    g = np.repeat(np.arange(80), 25)
    C = rng.uniform(-3, 3, (len(g), 2))
    f, noise = np.sin(2 * C[:, 0]) + C[:, 1] ** 2, rng.normal(size=len(g))
    Vhat = inference.project(C, (f + noise)[:, None], g)[:, 0]
    assert np.corrcoef(Vhat, f)[0, 1] > 0.95 and abs(np.corrcoef(Vhat - f, noise)[0, 1]) < 0.1


def test_adequacy_flags_missing_nonlinearity_only():
    rng = np.random.default_rng(4)
    g = np.repeat(np.arange(80), 25)
    t = rng.normal(0, 2, len(g))
    sp = splits.kfold(splits.assign_folds(g, 5))
    raw = t[:, None]
    for y, flagged in [(0.5 * t + rng.normal(size=len(g)), False), (0.5 * t + 0.4 * t ** 2 + rng.normal(size=len(g)), True)]:
        V = (0.4 * t ** 2 + rng.normal(0, .3, len(g)))[:, None]
        out = inference.adequacy(raw, y, sp, g, raw, Vhat=inference.project(raw, V, g))
        assert (out['flex'] > 0) == flagged and (out['proj'] > 0) == flagged


def test_perm_test_keep_mask_restricts_rows_consistently():
    C, V, y, g, slot = _grid(0.5, seed=5)
    sp = splits.kfold(splits.assign_folds(g, 4))
    full = inference.perm_test(C, V, y, sp, g, slot, n_perm=5, seed=1)
    same = inference.perm_test(C, V, y, sp, g, slot, n_perm=5, seed=1, keep=np.ones(len(g), bool))
    assert full[0] == pytest.approx(same[0]) and np.allclose(full[2], same[2])
    part = inference.perm_test(C, V, y, sp, g, slot, n_perm=5, seed=1, keep=slot < 6)
    assert part[0] != pytest.approx(full[0])


def test_cyclic_shift_preserves_unit_order_and_enumerates_shifts():
    g, slot = np.repeat(np.arange(10), 3), np.tile(np.arange(3.0), 10)
    src = inference.donor_sampler(g, slot)(np.random.default_rng(0), shift=3)
    assert np.array_equal(g[src], (g + 3) % 10) and np.array_equal(slot[src], slot)
    C, V, y, gg, ss = _grid(0.0, seed=4, n_days=20)
    sp = splits.kfold(splits.assign_folds(gg, 4, 'contiguous'))
    _, p, null = inference.perm_test(C, V, y, sp, gg, ss, shift_min=5)
    assert len(null) == 20 - 10 + 1 and p >= 1 / 12


def test_hac_interval_widens_under_serial_dependence():
    rng = np.random.default_rng(5)
    G = 400
    e = np.zeros(G)
    for t in range(1, G): e[t] = 0.85 * e[t - 1] + rng.normal()
    g = np.repeat(np.arange(G), 5)
    d = e[g] + rng.normal(0, .1, len(g))
    lo, hi = inference.hac_interval(d, g, lag=12)
    clo, chi = inference.cluster_interval(d, g)
    assert hi - lo > 2.5 * (chi - clo)
