"""Proper scores, calibration diagnostics, block bootstrap and the cross-fitted log-score contrast.

For held-out data and fixed fitted models q_VC, q_C the expected contrast decomposes exactly as

    E[log q_VC(d|v,c) - log q_C(d|c)] = I(D;V|C) - E KL(p(.|v,c) || q_VC) + E KL(p(.|c) || q_C),

so the contrast equals the conditional mutual information only when both models are correct; an under-fitted
context model inflates it and an over-fitted or miscalibrated joint model deflates it.
"""
from dataclasses import dataclass

import numpy as np
from scipy.special import log_ndtr, ndtr
from scipy.stats import gaussian_kde, norm
from sklearn.linear_model import PoissonRegressor, Ridge
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ALPHAS = np.logspace(-3, 5, 17)


def gauss_ls(y, mu, sd, censored=None):
    """Log predictive density (nats) of y under N(mu, sd^2); rows flagged `censored` are upper bounds scored as log P(Y <= y)."""
    z = (y - mu) / sd
    ls = -0.5 * z ** 2 - np.log(sd) - 0.5 * np.log(2 * np.pi)
    return ls if censored is None else np.where(censored, log_ndtr(z), ls)


def gauss_crps(y, mu, sd):
    z = (y - mu) / sd
    return sd * (z * (2 * ndtr(z) - 1) + 2 * norm.pdf(z) - 1 / np.sqrt(np.pi))


def pit(y, mu, sd): return ndtr((y - mu) / sd)


def coverage(y, mu, sd, level=0.9): return np.mean(np.abs(y - mu) <= norm.ppf(0.5 + level / 2) * sd)


def block_bootstrap(x, groups, n_boot=2000, seed=0):
    """Bootstrap distribution of mean(x) resampling whole groups (the independent units) with replacement."""
    _, inv = np.unique(groups, return_inverse=True)
    s, n = np.bincount(inv, weights=x), np.bincount(inv)
    idx = np.random.default_rng(seed).integers(0, len(s), (n_boot, len(s)))
    return s[idx].sum(1) / n[idx].sum(1)


def ridge(alpha=1.0): return make_pipeline(StandardScaler(), Ridge(alpha=alpha))


def ridge_oof(X, y, cv, alphas=ALPHAS):
    """Out-of-fold predictions of standardised ridge for every alpha, shape (n, len(alphas)); one SVD per fold."""
    P = np.empty((len(y), len(alphas)))
    for tr, te in cv:
        m, s = X[tr].mean(0), X[tr].std(0)
        s[s == 0] = 1
        U, sv, Vt = np.linalg.svd((X[tr] - m) / s, full_matrices=False)
        P[te] = y[tr].mean() + ((X[te] - m) / s) @ Vt.T @ (sv / (sv ** 2 + alphas[:, None]) * (U.T @ (y[tr] - y[tr].mean()))).T
    return P


def crossfit(X, y, splits, groups, model=None, var='oof', resid='gauss', inner=5, censored=None):
    """Out-of-fold predictive distribution for the test rows of every (train, test) split: (mu, sd, log score).

    Mean: ridge with the penalty chosen by grouped inner CV (`model=None`), or any sklearn factory `model()`.
    var='oof': homoscedastic SD from grouped inner out-of-fold residuals.
    var='hetero': log-link (quasi-Poisson) regression of those squared residuals, consistent for E[r^2 | x].
    var='insample': SD of training residuals of the final fit (optimistic; kept to demonstrate the failure).
    resid='gauss': Gaussian errors. resid='kde': location-scale model whose standardised-residual density is a
    Gaussian KDE of the training rows' out-of-fold standardised residuals (absorbs skew and unexplained mixtures).
    """
    if resid == 'kde' and censored is not None: raise NotImplementedError('censored scores are implemented for Gaussian residuals only')
    mu, sd, ls = (np.full(len(y), np.nan) for _ in range(3))
    for tr, te in splits:
        cv = list(GroupKFold(inner).split(X[tr], groups=groups[tr]))
        if model is None:
            P = ridge_oof(X[tr], y[tr], cv)
            k = np.argmin(((y[tr, None] - P) ** 2).mean(0))
            m, oof = ridge(ALPHAS[k]).fit(X[tr], y[tr]), P[:, k]
        else:
            m, oof = model().fit(X[tr], y[tr]), cross_val_predict(model(), X[tr], y[tr], cv=cv)
        mu[te], r = m.predict(X[te]), y[tr] - oof
        if var == 'hetero':
            v = make_pipeline(StandardScaler(), PoissonRegressor(alpha=1e-4, max_iter=1000)).fit(X[tr], r ** 2)
            s_tr, sd[te] = np.sqrt(v.predict(X[tr])), np.sqrt(v.predict(X[te]))
        else:
            s_tr = np.std(y[tr] - m.predict(X[tr])) if var == 'insample' else np.sqrt(np.mean(r ** 2))
            sd[te] = s_tr
        if resid == 'kde':
            ls[te] = gaussian_kde(r / s_tr).logpdf((y[te] - mu[te]) / sd[te]) - np.log(sd[te])
        else:
            ls[te] = gauss_ls(y[te], mu[te], sd[te], None if censored is None else censored[te])
    return mu, sd, ls


@dataclass
class Contrast:
    d: np.ndarray      # per-row log q_VC - log q_C, nats
    groups: np.ndarray  # independent units for the bootstrap
    pred_c: tuple       # (mu, sd, log score) of the context model
    pred_vc: tuple      # (mu, sd, log score) of the joint model

    @property
    def mean(self): return self.d.mean()

    def ci(self, level=0.95, n_boot=2000, seed=0):
        a = (1 - level) / 2
        return np.quantile(block_bootstrap(self.d, self.groups, n_boot, seed), [a, 1 - a])


def contrast(Xc, Xvc, y, splits, groups, **kw):
    """Held-out log-score improvement of q(D|V,C) over q(D|C), both fitted by `crossfit` with identical settings."""
    pc, pv = crossfit(Xc, y, splits, groups, **kw), crossfit(Xvc, y, splits, groups, **kw)
    return Contrast(pv[2] - pc[2], np.asarray(groups), pc, pv)
