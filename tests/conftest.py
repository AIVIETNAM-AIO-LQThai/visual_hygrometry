import numpy as np
import pandas as pd
import pytest

from visual_hygrometry import thermo


@pytest.fixture
def samples():
    """Ten days of contract-shaped rows with an independent conditioning thermometer and two visual features."""
    rng = np.random.default_rng(0)
    t = pd.Series(pd.date_range('2025-06-01', periods=10 * 48, freq='30min', tz='UTC'))
    temp = 20 + 5 * np.sin(2 * np.pi * (t.dt.hour - 9) / 24) + rng.normal(0, 2, len(t))
    rh = np.clip(70 - 2.5 * (temp - 20) + rng.normal(0, 8, len(t)), 15, 99)
    df = pd.DataFrame({'sample_id': [f's{i}' for i in range(len(t))], 'site_id': 'X', 'camera_id': 'cam0', 'time_utc': t, 'utc_offset_min': 0,
                       'ref_sensor_id': 'hmp_a', 'cond_sensor_id': 'hmp_b', 'rh_ref_pct': rh, 'temp_ref_c': temp + rng.normal(0, .1, len(t)),
                       'temp_cond_c': temp + rng.normal(0, .1, len(t)), 'vis_haze': rng.normal(size=len(t)), 'vis_bright': rng.normal(size=len(t)),
                       'wind_ms': rng.gamma(2, 1.5, len(t))})
    df['td_ref_c'] = thermo.dewpoint(df.temp_ref_c, df.rh_ref_pct)
    df['d_ref_k'] = df.temp_ref_c - df.td_ref_c
    df['hour_local'] = t.dt.hour + t.dt.minute / 60
    return df
