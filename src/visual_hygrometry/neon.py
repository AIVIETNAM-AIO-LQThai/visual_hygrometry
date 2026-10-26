"""NEON data API and PhenoCam archive access for feasibility audits.

The API token is read from NEON_TOKEN in the repository's .env (ignored by Git) and is only ever sent to the NEON API.
Downloads go to data/raw/ (ignored by Git) and are skipped when already present; every file is recorded with SHA-256.
"""
import hashlib
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from .data import ROOT

API, PHENO = 'https://data.neonscience.org/api/v0', 'https://phenocam.nau.edu'
RAW = ROOT / 'data' / 'raw'


def token(path=ROOT / '.env'):
    return dict(l.split('=', 1) for l in Path(path).read_text().splitlines() if '=' in l)['NEON_TOKEN'].strip()


def files(product, site, month, package='basic'):
    """File records (name, url, size, md5) of one NEON product, site, month and data package.

    Without a package filter the API lists basic and expanded files together, and their readme/variables files share
    names but differ in content.
    """
    r = requests.get(f'{API}/data/{product}/{site}/{month}', params={'package': package}, headers={'X-API-Token': token()}, timeout=60)
    r.raise_for_status()
    return r.json()['data']['files']


def sha256(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fetch(url, dest, pause=0.0, missing_ok=False, retries=4):
    """Download url to dest unless it exists; returns (path, sha256), or (None, None) for a 404 when missing_ok.
    Connection errors, timeouts and 5xx responses are retried with exponential backoff (2, 8, 32, 128 s)."""
    dest = Path(dest)
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        for k in range(retries + 1):
            try:
                r = requests.get(url, timeout=120)
                if r.status_code < 500: break
            except (requests.ConnectionError, requests.Timeout):
                if k == retries: raise
            time.sleep(2 * 4 ** k)
        if missing_ok and r.status_code == 404: return None, None
        r.raise_for_status()
        dest.write_bytes(r.content)
        time.sleep(pause)
    return dest, sha256(dest)


def neon_files(product, site, month, pattern, package='basic'):
    """Download the files of a product-month-package whose names match `pattern`; returns a manifest."""
    rows = []
    for f in files(product, site, month, package):
        if re.search(pattern, f['name']):
            path, h = fetch(f['url'], RAW / 'neon' / site / month / product / package / f['name'])
            if f.get('md5') and hashlib.md5(path.read_bytes()).hexdigest() != f['md5']: raise IOError(f'md5 mismatch: {f["name"]}')
            rows.append({'product': product, 'package': package, 'name': f['name'], 'bytes': path.stat().st_size, 'sha256': h, 'path': path})
    return pd.DataFrame(rows).drop_duplicates('name')


def camera_day(sitename, day):
    """Image basenames (without extension) listed for one camera-day on the PhenoCam browse page."""
    r = requests.get(f'{PHENO}/webcam/browse/{sitename}/{day:%Y/%m/%d}/', timeout=60)
    r.raise_for_status()
    return sorted(set(re.findall(rf'/data/archive/{re.escape(sitename)}/\d{{4}}/\d{{2}}/({re.escape(sitename)}_\d{{4}}_\d{{2}}_\d{{2}}_\d{{6}})\.jpg', r.text)))


def archive_url(sitename, base, ext): return f'{PHENO}/data/archive/{sitename}/{base[-17:-13]}/{base[-12:-10]}/{base}.{ext}'


def parse_meta(text):
    """key=value camera settings; overlay_text quotes kept verbatim."""
    return dict(l.split('=', 1) for l in text.splitlines() if '=' in l)


TABLES = {'rh': ('DP1.00098.001', 'RH_1min'), 'taat': ('DP1.00003.001', 'TAAT_1min'), 'rad': ('DP1.00023.001', 'SLRNR_1min'), 'wind': ('DP1.00001.001', '2DWSD_2min')}
COLUMNS = {'rh': {'RHMean': 'rh', 'RHExpUncert': 'rh_unc', 'RHMaximum': 'rh_max', 'RHVariance': 'rh_var', 'RHFinalQF': 'rh_qf', 'tempRHMean': 't_probe',
                  'tempRHExpUncert': 't_probe_unc', 'tempRHFinalQF': 't_probe_qf', 'dewTempMean': 'td', 'dewTempExpUncert': 'td_unc', 'dewTempFinalQF': 'td_qf'},
           'taat': {'tempTripleMean': 't_asp', 'tempTripleExpUncert': 't_asp_unc', 'finalQF': 't_asp_qf'},
           'rad': {'inSWMean': 'sw', 'inSWFinalQF': 'sw_qf'},
           'wind': {'windSpeedMean': 'wind', 'windSpeedFinalQF': 'wind_qf'}}


def table(site, month, key):
    """The single tower-top basic table of one product-month as downloaded by `neon_files`."""
    product, name = TABLES[key]
    f = sorted((RAW / 'neon' / site / month / product / 'basic').glob(f'*.{name}.*basic*.csv'))
    if len(f) != 1: raise FileNotFoundError(f'{site} {month} {name}: {len(f)} files')
    return pd.read_csv(f[0], parse_dates=['startDateTime']).set_index('startDateTime')


def load_site(site, months):
    """1-min UTC series of the label probe (RH, probe T, dew point), the aspirated thermometer, incoming shortwave and
    wind (2-min values repeated over both minutes). NEON values, expanded uncertainties and final quality flags are kept
    as columns; nothing is filtered or filled beyond that repetition."""
    out = []
    for m in months:
        idx = pd.date_range(f'{m}-01', periods=pd.Period(m).days_in_month * 1440, freq='1min', tz='UTC')
        parts = [table(site, m, k)[list(c)].rename(columns=c).reindex(idx, method='ffill', limit=1) if k == 'wind' else table(site, m, k)[list(c)].rename(columns=c).reindex(idx)
                 for k, c in COLUMNS.items()]
        out.append(pd.concat(parts, axis=1))
    return pd.concat(out)


def frame_meta(text):
    """Camera state of one PhenoCam frame from its .meta text: burned-in UTC time and camera temperature (overlay),
    exposure and the automatic-processing switches."""
    m = parse_meta(text)
    o = m.get('overlay_text', '')
    utc = re.search(r'(\w{3} \w{3} \d{1,2} \d{4})\s+(\d{2}:\d{2}:\d{2}) UTC', o)
    temp = re.search(r'Camera Temperature:\s*(-?[\d.]+)', o)
    return dict(overlay_utc=pd.to_datetime(' '.join(utc.groups()), format='%a %b %d %Y %H:%M:%S', utc=True) if utc else pd.NaT,
                camera_temp_c=float(temp.group(1)) if temp else np.nan, exposure=float(m.get('exposure', 'nan')), overlay=m.get('overlay'),
                overlay_pos=f"{m.get('overlay_position')}/{m.get('overlay_x')}/{m.get('overlay_y')}", auto_exposure=m.get('auto_exposure'), agc=m.get('agc'),
                auto_haze=m.get('auto_haze'), ir_enable=m.get('ir_enable'), wb=f"{m.get('red')}/{m.get('green')}/{m.get('blue')}", resolution=m.get('resolution'))


def load_frames(cam, months, utc_offset_h):
    """Listed frames of a camera with filename-derived UTC time, .meta camera state and whether the JPEG is on disk."""
    rows = []
    for m in months:
        d = RAW / 'phenocam' / cam / m
        for b in pd.read_csv(d / 'listing.csv').base:
            meta = d / f'{b}.meta'
            rows.append({'base': b, 'month': m, 'jpg': d / f'{b}.jpg'} | (frame_meta(meta.read_text(errors='replace')) if meta.exists() else {}))
    F = pd.DataFrame(rows)
    F['utc'] = (pd.to_datetime(F.base.str[-17:], format='%Y_%m_%d_%H%M%S') - pd.Timedelta(hours=utc_offset_h)).dt.tz_localize('UTC')
    F['has_jpg'] = F.jpg.map(Path.exists)
    return F
