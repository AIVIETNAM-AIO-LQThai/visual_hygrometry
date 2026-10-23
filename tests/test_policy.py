import numpy as np
import pytest

from visual_hygrometry import policy
from visual_hygrometry.policy import PolicyError, select, select_sci

DEPLOY = ['co', 'ta', 'ctx', 'teacher']


@pytest.mark.parametrize('setting', DEPLOY)
def test_label_canary_refused_everywhere(samples, setting):
    """A label-equivalent column under an innocuous name never reaches a model, whichever way it is offered."""
    df = samples.assign(aux_sensor_7=samples.d_ref_k + np.random.default_rng(1).normal(0, .05, len(samples)))
    with pytest.raises(PolicyError, match='unregistered'):
        select(df, setting, cols=['vis_haze', 'aux_sensor_7'])
    X, _, info = select(df, setting)  # automatic selection skips it and reports it
    assert 'aux_sensor_7' not in X and 'aux_sensor_7' in info['unregistered']


@pytest.mark.parametrize('setting', DEPLOY)
def test_disguised_canary_caught_by_audit(samples, setting):
    """Mis-declared as a visual feature, the canary passes the structural layers and must hit the empirical audit."""
    df = samples.assign(vis_canary=samples.d_ref_k + np.random.default_rng(2).normal(0, .05, len(samples)))
    with pytest.raises(PolicyError, match='label-equivalent'):
        select(df, setting, cols=['vis_haze', 'vis_canary'])


@pytest.mark.parametrize('col', ['rh_ref_pct', 'td_ref_c', 'd_ref_k', 'temp_ref_c', 'd_censored'])
@pytest.mark.parametrize('setting', DEPLOY)
def test_labels_and_label_qc_refused(samples, setting, col):
    df = samples.assign(d_censored=False)
    with pytest.raises(PolicyError):
        select(df, setting, cols=['vis_haze', col])


@pytest.mark.parametrize('col', ['pm_raw_ugm3', 'wx_code', 'rh_nwp_pct'])
def test_humidity_coded_shortcuts_refused(samples, col):
    df = samples.assign(**{col: 1.0})
    for s in DEPLOY:
        with pytest.raises(PolicyError, match='forbidden'):
            select(df, s, cols=['vis_haze', col])


def test_lineage_overrides_declared_role(samples, monkeypatch):
    """A field declared 'met' but derived from RH (e.g. a lagged label) is refused by lineage."""
    spec = {'type': 'number', 'x-role': 'met', 'x-derived-from': ['td_ref_c']}
    monkeypatch.setitem(policy.CONTRACT.fields, 'rh_lag_1h', spec)
    with pytest.raises(PolicyError, match='derived from label'):
        select(samples.assign(rh_lag_1h=0.0), 'ctx', cols=['vis_haze', 'rh_lag_1h'])


def test_role_matrix(samples):
    """CO sees only visual/acquisition fields; temperature is TA and above; clock is CTX and above."""
    assert select(samples, 'co')[0].columns.tolist() == ['vis_haze', 'vis_bright']
    assert set(select(samples, 'ta')[0]) == {'vis_haze', 'vis_bright', 'temp_cond_c'}
    assert set(select(samples, 'ctx')[0]) == {'vis_haze', 'vis_bright', 'temp_cond_c', 'wind_ms', 'hour_local'}
    for s, col in [('co', 'temp_cond_c'), ('co', 'hour_local'), ('ta', 'hour_local'), ('ta', 'wind_ms')]:
        with pytest.raises(PolicyError, match='not permitted'):
            select(samples, s, cols=[col])


def test_teacher_is_training_only(samples):
    select(samples, 'teacher', phase='train')
    with pytest.raises(PolicyError, match='training-only'):
        select(samples, 'teacher', phase='infer')


def test_shared_sensor_requires_explicit_permission(samples):
    df = samples.assign(cond_sensor_id='hmp_a')
    with pytest.raises(PolicyError, match='label sensor'):
        select(df, 'ta')
    assert select(df, 'ta', allow_shared_sensor=True)[2]['shared_sensor'] == 1.0
    select(df, 'co')  # no temperature features, no coupling


def test_sci_contrast_is_matched(samples):
    Xc, Xvc, y, info = select_sci(samples, 'e2', ctx=['hour_local', 'temp_cond_c'], vis=['vis_haze'])
    assert Xvc.columns.tolist() == Xc.columns.tolist() + ['vis_haze']
    with pytest.raises(PolicyError):  # visual feature smuggled into the context side
        select_sci(samples, 'e2', ctx=['hour_local', 'vis_bright'], vis=['vis_haze'])
    with pytest.raises(PolicyError):  # temperature is not part of E1 context
        select_sci(samples, 'e1', ctx=['hour_local', 'temp_cond_c'], vis=['vis_haze'])
    with pytest.raises(PolicyError):  # context field passed as visual
        select_sci(samples, 'e2', ctx=['hour_local'], vis=['temp_cond_c'])


def test_legitimate_features_pass_audit(samples):
    _, _, info = select(samples, 'ctx')
    assert max(info['eta2'].values()) < 0.95


def test_eta2_ignores_row_order_and_keeps_ties_together():
    rng = np.random.default_rng(3)
    x, y = rng.integers(0, 3, 2000).astype(float), rng.normal(size=2000)
    y += x  # a 3-level feature explains part of y
    perm = rng.permutation(2000)
    assert policy.eta2(x, y) == pytest.approx(policy.eta2(x[perm], y[perm]), abs=1e-12)
    groups = [y[x == v] for v in range(3)]
    exact = sum(len(g) * (g.mean() - y.mean()) ** 2 for g in groups) / (len(y) * y.var())
    assert policy.eta2(x, y) == pytest.approx(exact, abs=1e-12)  # one bin per distinct value
