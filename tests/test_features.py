import numpy as np
import pytest

from visual_hygrometry import features

REG = features.REGIONS['HARV']


def _img(fill):
    return np.full((960, 1296, 3), fill, np.uint8)


def test_uniform_scene_has_zero_contrast_and_sharpness():
    f = features.scene_features(_img(120), REG)
    assert f['vis_far_contrast'] == pytest.approx(0) and f['vis_near_contrast'] == pytest.approx(0) and f['vis_far_sharp'] == pytest.approx(0)
    assert f['vis_near_gcc'] == pytest.approx(1 / 3) and f['vis_sky_br'] == pytest.approx(1) and set(f) == set(features.NAMES)


def test_overlay_pixels_never_reach_features():
    a, b = _img(100), _img(100)
    rng = np.random.default_rng(0)
    b[:88, :846] = rng.integers(0, 256, (88, 846, 3))  # burned-in text region only
    fa, fb = features.scene_features(a, REG), features.scene_features(b, REG)
    assert all(fa[k] == pytest.approx(fb[k]) or (np.isnan(fa[k]) and np.isnan(fb[k])) for k in features.NAMES)


def test_haze_lowers_far_contrast_and_saturation():
    rng = np.random.default_rng(1)
    scene = rng.integers(0, 256, (960, 1296, 3)).astype(float)
    hazy = 0.4 * scene + 0.6 * 200  # Koschmieder-type veil: attenuated scene plus airlight
    f0, f1 = (features.scene_features(x.astype(np.uint8), REG) for x in (scene, hazy))
    assert f1['vis_far_contrast'] < f0['vis_far_contrast'] and f1['vis_far_sat'] < f0['vis_far_sat'] and f1['vis_far_sharp'] < f0['vis_far_sharp']
