import numpy as np

from visual_hygrometry import neon

_rng = np.random.default_rng(0)
GLYPH = {str(d): np.vstack([_rng.integers(0, 2, (8, 6)), np.ones((1, 6), int)]) for d in range(10)}  # 1x bitmaps, no empty column
GLYPH['U'] = GLYPH['T'] = GLYPH['C'] = np.ones((9, 5), int)


def _overlay(text, bg=80, ink=200):
    """A grey frame with `text` in a 2x pixel font on a uniform box (glyph gap 4 px, space 12 px, colon two 2-px dots)."""
    a = np.full((960, 1296), 150.0)
    a[:30, :900] = bg
    x = 10
    for ch in text:
        if ch == ' ':
            x += 12
            continue
        g = np.zeros((9, 1), int) if ch == ':' else GLYPH[ch]
        if ch == ':': g[[2, 7]] = 1
        big = np.kron(g, np.ones((2, 2)))
        a[6:6 + big.shape[0], x:x + big.shape[1]][big > 0] = ink
        x += big.shape[1] + 4
    return a


def test_overlay_time_is_read_with_templates_learned_from_known_frames():
    train = ['01:23:45', '67:89:01', '45:67:89']
    X = np.vstack([neon.overlay_time_digits(_overlay(f'2023 {t} UTC')) for t in train])
    Y = np.array(list(''.join(t.replace(':', '') for t in train)))
    templates = {c: X[Y == c].mean(0) for c in '0123456789'}
    s, margin = neon.read_overlay_time(neon.overlay_time_digits(_overlay(f'2020 {"19:50:06"} UTC', bg=95, ink=230)), templates)
    assert s == '195006' and margin > 0
    assert neon.overlay_time_digits(_overlay('2020 UTC')) is None and neon.read_overlay_time(None, templates)[0] is None
