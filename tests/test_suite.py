import pickle

import numpy as np
import pytest

from visual_hygrometry import policy, suite, worlds

def test_records_have_seasons_solar_geometry_and_pass_the_contract():
    W = {'spec': suite.spec(gamma=.1), 'vis': ['vis_moist']}
    df = suite.make(W, 2, seed=3)
    assert df.year.nunique() == 2 and len(df) == 2 * suite.N_DAYS * suite.PER_DAY
    assert {'solar_elev_deg', 'solar_dayfrac', 'solar_decl_deg', 'solar_hour_angle_deg'} <= set(df)
    dfl, lv = worlds.add_context_levels(df, suite.KNOTS, suite.DOY_K, suite.DOY_F, hour_season=True, solar=True)
    Xc, _, _, _ = policy.select_sci(dfl, 'e2', lv['S4'], W['vis'])
    assert Xc.shape[1] == len(lv['S4'])
    noon = df[(df.hour == 12) & (df.year == 0)]
    assert np.corrcoef(noon.solar_elev_deg, noon.temp_cond_c)[0, 1] > 0  # the climate heats with the sun

def test_world_specs_pickle_for_parallel_workers():
    sp = pickle.loads(pickle.dumps(suite.spec(slow=(1, .5))))
    assert sp['temp_cond_c'].mean(np.array([6.0, 12.0]))[0] == 16.0

def test_shared_regime_truth_is_zero_without_a_shared_shift_and_matches_gaussian_limit():
    assert abs(suite.truth_shared_regime(.5, (0, 0), (2, 2), (0, 0), n=200_000)) < 2e-3
    assert suite.truth_shared_regime(.5, (0, -2), (2, 3), (0, 1), n=200_000) > 0.01