"""Schema access, contract validation and causal feature construction."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def load_schema(name='sample'): return json.loads((ROOT / 'schemas' / f'{name}.schema.json').read_text())


def ns(t): return pd.DatetimeIndex(t).as_unit('ns').asi8


def validate(df, schema):
    """Row-level contract violations as a boolean frame (one column per failed rule, only rules that fail).

    Raises only when the table cannot be interpreted: missing required columns, non-UTC timestamps, non-numeric
    numeric fields. Everything else is reported for the caller to count and exclude explicitly.
    """
    missing = [c for c in schema['required'] if c not in df]
    if missing: raise ValueError(f'missing required columns: {missing}')
    bad = {}
    for c, spec in schema['properties'].items():
        if c not in df: continue
        x = df[c]
        if spec.get('format') == 'date-time' and not (isinstance(x.dtype, pd.DatetimeTZDtype) and str(x.dt.tz) == 'UTC'):
            raise ValueError(f'{c} must be tz-aware UTC, got {x.dtype}')
        if spec.get('type') == 'number':
            if not pd.api.types.is_numeric_dtype(x): raise ValueError(f'{c} must be numeric, got {x.dtype}')
            bad[f'{c}:nonfinite'] = np.isinf(x)
        if c in schema['required']: bad[f'{c}:missing'] = x.isna()
        if 'minimum' in spec: bad[f'{c}:minimum'] = x < spec['minimum']
        if 'maximum' in spec: bad[f'{c}:maximum'] = x > spec['maximum']
    if {'camera_id', 'time_utc'} <= set(df): bad['time_utc:duplicate'] = df.duplicated(['camera_id', 'time_utc'], keep=False)
    out = pd.DataFrame(bad, index=df.index)
    return out.loc[:, out.any()]


def causal_mean(t, x, at, window):
    """Mean of finite x over readings with t in (at - window, at]; NaN when the window holds none. Never reads past `at`."""
    t, at, w = ns(t), ns(at), pd.Timedelta(window).value
    o = np.argsort(t, kind='stable')
    t, x = t[o], np.asarray(x, float)[o]
    ok = np.isfinite(x)
    cs, cn = np.concatenate([[0], np.cumsum(np.where(ok, x, 0))]), np.concatenate([[0], np.cumsum(ok)])
    hi, lo = np.searchsorted(t, at, side='right'), np.searchsorted(t, at - w, side='right')
    n = cn[hi] - cn[lo]
    return np.where(n > 0, (cs[hi] - cs[lo]) / np.maximum(n, 1), np.nan)


def clock(time_utc, utc_offset_min):
    """Local standard-time hour and day of year (no DST)."""
    local = time_utc + pd.to_timedelta(utc_offset_min, unit='min')
    return pd.DataFrame({'hour_local': local.dt.hour + local.dt.minute / 60 + local.dt.second / 3600, 'doy': local.dt.day_of_year}, index=time_utc.index)


def fourier(x, period, k, name):
    """Fixed sine/cosine basis with k harmonics; data-independent, so it cannot leak test-set statistics."""
    w = 2 * np.pi * np.asarray(x, float)[:, None] * np.arange(1, k + 1) / period
    cols = [f'{name}_{f}{j}' for f in 'sc' for j in range(1, k + 1)]
    return pd.DataFrame(np.hstack([np.sin(w), np.cos(w)]), columns=cols, index=getattr(x, 'index', None))
