"""Blocked folds and history-aware purging for temporally dependent samples.

A sample's dependency interval [start, end] spans everything it reads or is scored against: the visual and context
look-back before its time and the label averaging window after it. Two samples whose intervals overlap (or lie within
an embargo of each other) are not independent, so a training sample must never overlap an evaluation sample.
"""
import numpy as np
import pandas as pd

from .data import ns


def blocks(time_utc, unit='D', utc_offset_min=0):
    """Calendar block per sample in local standard time: 'D' day, 'W' week."""
    local = (time_utc + pd.to_timedelta(utc_offset_min, unit='min')).dt.tz_localize(None)
    return local.dt.to_period(unit).astype(str).to_numpy()


def assign_folds(block, k, how='interleaved', seed=0):
    """Fold id per sample with every block wholly inside one fold.

    contiguous: k runs of consecutive blocks (strongest separation; folds differ in season).
    interleaved: block i -> fold i mod k (each fold spans the season range).
    random: shuffled blocks.
    """
    ub = np.unique(block)
    if len(ub) < k: raise ValueError(f'{len(ub)} blocks cannot fill {k} folds')
    n = len(ub)
    f = {'contiguous': np.arange(n) * k // n, 'interleaved': np.arange(n) % k, 'random': np.random.default_rng(seed).permutation(n) % k}[how]
    return f[np.searchsorted(ub, block)]


def purge(train, test, start, end, embargo='0s'):
    """Training mask without samples whose [start, end] comes within `embargo` of any test interval."""
    s, e, emb = ns(start), ns(end), pd.Timedelta(embargo).value
    ts, te = s[test] - emb, e[test] + emb
    o = np.argsort(ts)
    ts, te = ts[o], np.maximum.accumulate(te[o])
    j = np.searchsorted(ts, e[train], side='right') - 1
    hit = (j >= 0) & (te[np.maximum(j, 0)] >= s[train])
    out = np.array(train, bool)
    out[np.flatnonzero(train)[hit]] = False
    return out


def kfold(fold, start=None, end=None, embargo='0s'):
    """(train, test) boolean masks per fold; purged when dependency intervals are given."""
    out = []
    for f in np.unique(fold):
        test = fold == f
        train = ~test if start is None else purge(~test, test, start, end, embargo)
        if not train.any(): raise ValueError(f'fold {f}: purge left no training samples')
        out.append((train, test))
    return out
