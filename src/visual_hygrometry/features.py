"""Predefined low-dimensional scene features from overlay-masked PhenoCam frames (Exp 2a-A, decision D-021).

Regions are fixed per site from one reference frame, by scene geometry only, before any label is inspected. Values are
computed on auto-exposed, in-camera-processed sRGB JPEG data: they are processed-RGB descriptors, not radiances, and
inherit auto-exposure, AGC and in-camera haze compensation as acquisition confounders.
"""
import numpy as np
from PIL import Image

OVERLAY = [(0, 0, 846, 29), (0, 29, 312, 58), (0, 58, 160, 88)]  # (x0, y0, x1, y1) at 1296 x 960, notebook 07
REGIONS = {  # (x0, y0, x1, y1) at 1296 x 960; sky right of the overlay, far band below the horizon, near foreground
    'HARV': {'sky': (900, 0, 1296, 50), 'far': (0, 100, 1296, 190), 'near': (0, 560, 1296, 960)},
    'CPER': {'sky': (860, 0, 1296, 90), 'far': (0, 110, 1296, 200), 'near': (0, 600, 1296, 960)}}
NAMES = ['vis_sky_lum', 'vis_sky_br', 'vis_far_contrast', 'vis_near_contrast', 'vis_contrast_ratio', 'vis_far_sat', 'vis_near_gcc', 'vis_near_dark', 'vis_far_sharp']


def masked(rgb):
    """Float RGB in [0, 1] with every overlay pixel set to NaN."""
    a = np.asarray(rgb, float) / 255
    for x0, y0, x1, y1 in OVERLAY: a[y0:y1, x0:x1] = np.nan
    return a


def _crop(a, box):
    x0, y0, x1, y1 = box
    return a[y0:y1, x0:x1]


def scene_features(rgb, regions):
    """The nine predefined features of one 1296 x 960 RGB frame."""
    a = masked(rgb)
    lum = a @ [0.2126, 0.7152, 0.0722]
    sky, far, near = (_crop(a, regions[k]) for k in ('sky', 'far', 'near'))
    lf, ln = _crop(lum, regions['far']), _crop(lum, regions['near'])
    rms = lambda l: np.nanstd(l) / np.nanmean(l)
    mx, mn = np.nanmax(far, axis=2), np.nanmin(far, axis=2)
    lap = lf[1:-1, 1:-1] * 4 - lf[:-2, 1:-1] - lf[2:, 1:-1] - lf[1:-1, :-2] - lf[1:-1, 2:]
    return dict(zip(NAMES, [np.nanmean(_crop(lum, regions['sky'])), np.nanmean(sky[..., 2]) / np.nanmean(sky[..., 0]), rms(lf), rms(ln), rms(lf) / rms(ln),
                            np.nanmean(np.where(mx > 0, (mx - mn) / np.where(mx > 0, mx, 1), 0)), np.nanmean(near[..., 1] / near.sum(axis=2)),
                            np.nanpercentile(ln, 10), np.nanvar(lap)]))


def frame_features(path, site):
    """Features of one frame plus QC: `qc_sky_clip`, the share of sky-band pixels with a channel at 254 or above
    (auto-exposure set for the scene clips a bright sky; clipped sky features carry no information)."""
    with Image.open(path) as im:
        if im.size != (1296, 960): raise ValueError(f'{path}: unexpected size {im.size}')
        rgb = np.asarray(im.convert('RGB'))
    with np.errstate(invalid='ignore', divide='ignore'):
        f = scene_features(rgb, REGIONS[site])
    return f | {'qc_sky_clip': (_crop(rgb, REGIONS[site]['sky']) >= 254).any(axis=2).mean()}
