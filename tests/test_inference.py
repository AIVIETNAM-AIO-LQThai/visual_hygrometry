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


def test_shift_configs_count_min_p_and_strata():
    days = np.repeat(np.arange(31), 4)
    ks = inference.shift_configs(days, shift_min=7)
    assert len(ks) == 18 and 1 / (len(ks) + 1) == pytest.approx(0.0526, abs=1e-4)  # one month cannot reach p <= 0.05
    strata = (np.arange(90) >= 40).astype(int)
    assert inference.shift_configs(np.arange(90), strata, 7) == list(range(7, 34))  # shortest stratum: 40 units
    with pytest.raises(ValueError, match='no cyclic shift'):
        inference.shift_configs(np.arange(30), (np.arange(30) >= 20).astype(int), 7)


def _levels(seed, n_days=40, tensor=0.0):
    from visual_hygrometry import worlds
    df = worlds.frame({'spec': worlds.gauss_world(.3), 'vis': ['vis_moist']}, n_days, seed).assign(doy=lambda d: 160 + d.day)
    T, h = df.temp_cond_c.to_numpy(), df.hour.to_numpy()
    df['d_ref_k'] = df.d_ref_k + tensor * ((T - 20) ** 2 / 9 - 1) * np.cos(2 * np.pi * (h - 12) / 24)  # T curvature varying with hour
    df, lv = worlds.add_context_levels(df, np.arange(-4, 45, 4.0), np.arange(140, 261, 15.0), np.arange(140, 261, 7.5))
    return df, [df[c].to_numpy() for c in lv.values()], df.d_ref_k.to_numpy(), df.day.to_numpy()


def test_select_capacity_never_reads_test_labels_and_finds_the_tensor_term():
    df, L, y, g = _levels(4, n_days=60, tensor=3.0)
    sp = splits.kfold(splits.assign_folds(g // 8, 3, 'contiguous'))
    designs, chosen = inference.select_capacity(L, y, sp, g // 4)
    y2 = y.copy()
    y2[sp[0][1]] = 1e6  # corrupt the first split's test labels
    d2, c2 = inference.select_capacity(L, y2, sp[:1], g // 4)
    assert c2[0] == chosen[0] and d2[0] is designs[0]
    assert all(c == 2 for c in chosen)  # the hour-varying T shape needs the tensor level


def test_clip_to_training_uses_training_quantiles_only():
    V = np.r_[np.arange(100.0), 1e3][:, None]
    tr = np.r_[np.ones(100, bool), False]
    (Vc,) = inference.clip_to_training(V, [(tr, ~tr)], q=0.0)
    assert Vc[-1, 0] == 99.0 and np.array_equal(Vc[:100], V[:100])


def test_perm_test_clip_matches_contrast_on_clipped_designs():
    C, V, y, g, slot = _grid(1.0, seed=2)
    V[0] = 50.0  # an extreme image row
    sp = splits.kfold(splits.assign_folds(g, 4))
    obs, _, null = inference.perm_test(C, V, y, sp, g, slot, units=g, shift_min=7, clip=0.01)
    r = scoring.contrast(C, [np.c_[C, v] for v in inference.clip_to_training(V, sp, 0.01)], y, sp, g)
    assert obs == pytest.approx(r.mean) and len(null) == len(inference.shift_configs(g, None, 7))


def test_split_levels_hold_season_at_the_training_edge():
    from visual_hygrometry import worlds
    df, L, y, g = _levels(4, n_days=40)
    sp = splits.kfold(splits.assign_folds(g // 10, 4, 'contiguous'))
    lv, cols = worlds.split_levels(df, sp, np.arange(-4, 45, 4.0), np.arange(140, 261, 15.0), np.arange(140, 261, 7.5))
    tr, te = sp[-1]  # last block: every test day lies beyond the training days
    Y = lv['L1'][-1][:, [cols['L1'].index(c) for c in cols['L1'] if c.startswith('doy_spl')]]
    edge = Y[tr][np.argmax(df.doy[tr].to_numpy())]
    assert np.allclose(Y[te], edge) and len(lv['L3']) == len(sp)
    designs, chosen = inference.select_capacity(list(lv.values()), y, sp, g // 4)
    assert all(d is lv[k][j] for j, (d, k) in enumerate(zip(designs, [list(lv)[c] for c in chosen])))
