"""Policy-enforced selection of model inputs.

Every array that reaches a model passes through `select` (deployment settings and the teacher) or `select_sci`
(matched information contrasts). Layers, in order:
  1. registration: a column absent from the data contract is refused (closed world);
  2. role: the field's x-role must be permitted in the setting;
  3. lineage: a field derived, transitively, from a label field is refused whatever its declared role;
  4. sensor roles: temperature features must not come from the label's own sensor unless explicitly allowed;
  5. phase: training-only settings are refused at inference;
  6. empirical audit: a single feature whose correlation ratio with the target reaches the configured eta^2 is refused.
Layers 1-5 are structural and exact; layer 6 is a heuristic net for mis-declared fields.
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from .data import ROOT, load_schema

NEVER = {'id', 'time', 'label', 'label_qc', 'provenance', 'calib', 'forbidden'}
TEMP_ROLES = {'temp_cond', 'temp_hist'}


class PolicyError(ValueError):
    pass


class Contract:
    def __init__(self, schema):
        self.fields = schema['properties']
        self.patterns = [(re.compile(p), s) for p, s in schema.get('patternProperties', {}).items()]
        self.labels = {k for k, s in self.fields.items() if s.get('x-role') == 'label'}

    def spec(self, col):
        if col in self.fields: return self.fields[col]
        return next((s for p, s in self.patterns if p.search(col)), None)

    def role(self, col): return (self.spec(col) or {}).get('x-role')

    def lineage(self, col):
        seen, todo = set(), list((self.spec(col) or {}).get('x-derived-from', []))
        while todo:
            c = todo.pop()
            if c not in seen:
                seen.add(c)
                todo += (self.spec(c) or {}).get('x-derived-from', [])
        return seen

    def violations(self, cols, roles):
        out = {}
        for c in cols:
            s = self.spec(c)
            if s is None: out[c] = 'unregistered in data contract'
            elif s['x-role'] not in roles: out[c] = f"role '{s['x-role']}' not permitted" + (f" ({s['x-reason']})" if 'x-reason' in s else '')
            elif self.lineage(c) & self.labels: out[c] = f'derived from label field(s) {sorted(self.lineage(c) & self.labels)}'
        return out


def load_settings(path=ROOT / 'configs' / 'inference_settings.yaml'): return yaml.safe_load(Path(path).read_text())


CONTRACT, SETTINGS = Contract(load_schema('sample')), load_settings()


def eta2(x, y, bins=50):
    """Correlation ratio: share of var(y) explained by quantile bins of x (1 = y is a function of x).

    Bins come from average ranks, so tied x values always share a bin and the result does not depend on row order.
    """
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    nb = max(2, min(bins, len(x) // 20))
    b = np.minimum(np.floor((pd.Series(x).rank(method='average').to_numpy() - 0.5) * nb / len(x)), nb - 1).astype(int)
    m = np.bincount(b, weights=y)[b] / np.bincount(b)[b]
    return np.var(m) / np.var(y)


def _check(df, cols, roles, target, targets, allow_shared_sensor, audit, where):
    bad = CONTRACT.violations(cols, roles)
    if target not in targets: bad[target] = f'not a permitted target of {where}'
    if bad: raise PolicyError(f'{where}: ' + '; '.join(f'{c}: {r}' for c, r in bad.items()))
    info = {'shared_sensor': 0.0}
    if any(CONTRACT.role(c) in TEMP_ROLES for c in cols) and {'ref_sensor_id', 'cond_sensor_id'} <= set(df):
        info['shared_sensor'] = float((df['ref_sensor_id'] == df['cond_sensor_id']).mean())
        if info['shared_sensor'] and not allow_shared_sensor:
            raise PolicyError(f'{where}: temperature features come from the label sensor in {info["shared_sensor"]:.0%} of rows; '
                              'errors are common-mode with the label. Pass allow_shared_sensor=True only with a documented limitation.')
    num = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]
    info['eta2'] = {c: eta2(df[c].to_numpy(float), df[target].to_numpy(float)) for c in num}
    hits = {c: v for c, v in info['eta2'].items() if v >= audit}
    if hits: raise PolicyError(f'{where}: near label-equivalent feature(s) {hits} (eta^2 >= {audit}); declare/explain before use')
    return info


def select(df, setting, cols=None, target='d_ref_k', phase='train', allow_shared_sensor=False, audit=None):
    """(X, y, info) for a deployment setting or the teacher. cols=None takes every permitted contract field present."""
    cfg = SETTINGS['settings'][setting]
    if phase == 'infer' and cfg.get('training_only'): raise PolicyError(f'{setting} is training-only and cannot run at inference')
    roles = set(cfg['inputs']) - NEVER
    cols = [c for c in df if not CONTRACT.violations([c], roles)] if cols is None else list(cols)
    info = _check(df, cols, roles, target, cfg['targets'], allow_shared_sensor, audit or SETTINGS['label_equivalence_eta2'], setting)
    return df[cols], df[target], info | {'setting': setting, 'cols': cols, 'unregistered': [c for c in df if CONTRACT.spec(c) is None]}


def select_sci(df, level, ctx, vis, target='d_ref_k', allow_shared_sensor=False, audit=None):
    """(Xc, Xvc, y, info) for the matched contrast q(D|V,C) vs q(D|C): identical context columns, visual columns added."""
    cfg, where = SETTINGS['sci'][level], f'sci_{level}'
    ctx, vis = list(ctx), list(vis)
    allowed_vis = set(cfg['visual']) - (NEVER - {'calib'} if level.endswith('_acq_control') else NEVER)  # calib only in the acquisition-only controls
    bad = CONTRACT.violations(ctx, set(cfg['context']) - NEVER) | CONTRACT.violations(vis, allowed_vis)
    if bad: raise PolicyError(f'{where}: ' + '; '.join(f'{c}: {r}' for c, r in bad.items()))
    info = _check(df, ctx + vis, (set(cfg['context']) - NEVER) | allowed_vis, target, SETTINGS['sci_targets'], allow_shared_sensor, audit or SETTINGS['label_equivalence_eta2'], where)
    return df[ctx], df[ctx + vis], df[target], info | {'setting': where, 'ctx': ctx, 'vis': vis}
