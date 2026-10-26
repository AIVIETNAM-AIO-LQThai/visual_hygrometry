"""NEON data API and PhenoCam archive access for feasibility audits.

The API token is read from NEON_TOKEN in the repository's .env (ignored by Git) and is only ever sent to the NEON API.
Downloads go to data/raw/ (ignored by Git) and are skipped when already present; every file is recorded with SHA-256.
"""
import hashlib
import re
import time
from pathlib import Path

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


def fetch(url, dest, pause=0.0):
    """Download url to dest unless it exists; returns (path, sha256)."""
    dest = Path(dest)
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, timeout=120)
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
