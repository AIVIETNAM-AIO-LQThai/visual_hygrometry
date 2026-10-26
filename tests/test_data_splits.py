import json

import jsonschema
import numpy as np
import pandas as pd
import pytest

from visual_hygrometry import data, splits


@pytest.mark.parametrize('name', ['sample', 'frame', 'sensor'])
def test_schemas_are_valid_json_schema(name):
    jsonschema.Draft202012Validator.check_schema(data.load_schema(name))


def test_validate_reports_without_repairing(samples):
    df = samples.copy()
    df.loc[3, 'rh_ref_pct'], df.loc[5, 'temp_cond_c'], df.loc[7, 'time_utc'] = 112.0, np.inf, df.loc[6, 'time_utc']
    bad = data.validate(df, data.load_schema())
    assert bad['rh_ref_pct:maximum'].sum() == 1 and bad['temp_cond_c:nonfinite'].sum() == 1
    assert bad['time_utc:duplicate'].sum() == 2
    assert df.loc[3, 'rh_ref_pct'] == 112.0
    with pytest.raises(ValueError, match='UTC'):
        data.validate(df.assign(time_utc=df.time_utc.dt.tz_localize(None)), data.load_schema())
    with pytest.raises(ValueError, match='missing'):
        data.validate(df.drop(columns='ref_sensor_id'), data.load_schema())


def test_causal_mean_never_reads_the_future():
    t = pd.date_range('2025-06-01', periods=12, freq='1h', tz='UTC')
    x = np.arange(12.0)
    x[8] = 1e6  # spike after the query times
    at = t[[3, 7]]
    m = data.causal_mean(t, x, at, '3h')
    assert m.tolist() == [2.0, 6.0]  # window (at-3h, at] -> readings at-2h..at
    assert np.isnan(data.causal_mean(t, x, at - pd.Timedelta('1D'), '3h')).all()


def test_clock_uses_standard_time_and_fourier_is_periodic():
    t = pd.Series(pd.to_datetime(['2025-07-01T04:30Z', '2025-12-31T23:59Z']))
    c = data.clock(t, -300)  # UTC-5 all year: no daylight-saving shift in July
    assert c.hour_local.round(3).tolist() == [23.5, 18.983] and c.doy.tolist() == [181, 365]
    f = data.fourier(pd.Series([0.0, 6.0, 24.0]), 24, 2, 'hour')
    assert list(f) == ['hour_s1', 'hour_s2', 'hour_c1', 'hour_c2'] and np.allclose(f.iloc[0], f.iloc[2]) and np.allclose(f.iloc[1], [1, 0, 0, -1])


def test_folds_hold_whole_days(samples):
    b = splits.blocks(samples.time_utc, 'D', utc_offset_min=420)
    for how in ['contiguous', 'interleaved', 'random']:
        f = splits.assign_folds(b, 5, how)
        assert pd.Series(f).groupby(b).nunique().max() == 1
        assert np.bincount(f).min() > 0
    with pytest.raises(ValueError):
        splits.assign_folds(b, 20)


def test_purge_removes_overlapping_histories(samples):
    t = samples.time_utc
    start, end = t - pd.Timedelta('6h'), t + pd.Timedelta('15min')
    fold = splits.assign_folds(splits.blocks(t, 'D'), 5, 'contiguous')
    for train, test in splits.kfold(fold, start, end, embargo='1h'):
        s, e = data.ns(start), data.ns(end)
        emb = pd.Timedelta('1h').value
        tr, te = np.flatnonzero(train), np.flatnonzero(test)
        overlap = (s[tr, None] <= e[None, te] + emb) & (e[tr, None] >= s[None, te] - emb)
        assert not overlap.any()
        # purging only removes samples near fold boundaries: 6 h look-back + 15 min + 2 x 1 h embargo
        assert (~train & ~test).sum() <= 2 * 48 * 9.5 / 24
    naive = [(fold != f, fold == f) for f in range(5)]
    tr, te = naive[1]
    s, e = data.ns(start), data.ns(end)
    assert ((s[tr][:, None] <= e[te][None]) & (e[tr][:, None] >= s[te][None])).any()  # unpurged day blocks do overlap


def test_spline_basis_is_fixed_and_partitions_unity():
    knots = np.arange(0, 41, 4.0)
    a = data.spline(pd.Series([3.0, 17.5, 39.0]), knots, 'temp_spl')
    b = data.spline(pd.Series([3.0, 17.5, 39.0, -100.0, 250.0]), knots, 'temp_spl')
    assert np.allclose(a.to_numpy(), b.to_numpy()[:3])  # no dependence on the other rows
    assert np.allclose(a.sum(axis=1), 1) and list(a)[0] == 'temp_spl0' and a.shape[1] == len(knots) + 2


def test_chrono_split_orders_and_purges():
    b = np.repeat(np.arange(10), 3)
    fit, ev = splits.chrono(b, frac=0.6, gap=1)
    assert set(b[fit]) == set(range(6)) and set(b[ev]) == {7, 8, 9} and not (fit & ev).any()
    with pytest.raises(ValueError):
        splits.chrono(b, frac=0.95, gap=1)
