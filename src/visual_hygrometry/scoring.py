"""Proper scores, calibration diagnostics, block bootstrap and the cross-fitted log-score contrast.

For held-out data and fixed fitted models q_VC, q_C the expected contrast decomposes exactly as

    E[log q_VC(d|v,c) - log q_C(d|c)] = I(D;V|C) - E KL(p(.|v,c) || q_VC) + E KL(p(.|c) || q_C),

so the contrast equals the conditional mutual information only when both models are correct; an under-fitted
context model inflates it and an over-fitted or miscalibrated joint model deflates it. Under misspecification the
contrast is the information *captured by these models*, not I(D;V|C).

Families: 'gauss' (ridge mean; homoscedastic, log-link or in-sample variance; Gaussian or KDE residual density;
censored rows fitted by a penalised Tobit likelihood) and 'binned' (multinomial logistic model over fixed bins of D,
whose estimand is I(B;V|C) <= I(D;V|C) for the binned target B).
"""
from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.special import log_ndtr, ndtr
from scipy.stats import gaussian_kde, norm
from sklearn.linear_model import LogisticRegression, PoissonRegressor, Ridge
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ALPHAS = np.logspace(-3, 5, 17)
LOG2PI = np.log(2 * np.pi)
DEFENSIVE = 0.01  # weight of a wide N(0, 4^2) component in KDE residual densities: bounds the loss on tail rows


def gauss_ls(y, mu, sd, censored=None):
    """Log predictive density (nats) of y under N(mu, sd^2); rows flagged `censored` are upper bounds scored as log P(Y <= y)."""
    z = (y - mu) / sd
    ls = -0.5 * z ** 2 - np.log(sd) - 0.5 * LOG2PI
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


def _standardise(X, rows):
    m, s = X[rows].mean(0), X[rows].std(0)
    s[s == 0] = 1
    return m, s


def ridge(alpha=1.0): return make_pipeline(StandardScaler(), Ridge(alpha=alpha))


def ridge_oof(X, y, cv, alphas=ALPHAS):
    """Out-of-fold predictions of standardised ridge for every alpha, shape (n, len(alphas)); one SVD per fold."""
    P = np.empty((len(y), len(alphas)))
    for tr, te in cv:
        m, s = _standardise(X, tr)
        U, sv, Vt = np.linalg.svd((X[tr] - m) / s, full_matrices=False)
        P[te] = y[tr].mean() + ((X[te] - m) / s) @ Vt.T @ (sv / (sv ** 2 + alphas[:, None]) * (U.T @ (y[tr] - y[tr].mean()))).T
    return P


def _ridge_predict(X, y, tr, te, alpha):
    m, s = _standardise(X, tr)
    Z = (X[tr] - m) / s
    w = np.linalg.solve(Z.T @ Z + alpha * np.eye(Z.shape[1]), Z.T @ (y[tr] - y[tr].mean()))
    return y[tr].mean() + ((X[te] - m) / s) @ w


def _tobit(Z, y, cens, alpha, th=None):
    """Penalised left-censored Gaussian MLE on standardised Z; returns (b0, w, log sd). Censored y are upper bounds."""
    p = Z.shape[1]
    th = np.r_[y.mean(), np.zeros(p), np.log(y.std())] if th is None else th

    def f(th):
        w, ls = th[1:p + 1], th[-1]
        z = (y - th[0] - Z @ w) / np.exp(ls)
        lam = np.exp(norm.logpdf(z) - log_ndtr(z))
        ll = np.where(cens, log_ndtr(z), -0.5 * z ** 2 - ls - 0.5 * LOG2PI)
        gmu, gls = np.where(cens, -lam, z) / np.exp(ls), np.where(cens, -lam * z, z ** 2 - 1)
        return -ll.sum() + 0.5 * alpha * w @ w, -np.r_[gmu.sum(), Z.T @ gmu - alpha * w, gls.sum()]
    return minimize(f, th, jac=True, method='L-BFGS-B').x


def _censored_sd(r, cens):
    """MLE of a common SD for residuals r = y - mu with left-censored rows."""
    f = lambda ls: -np.where(cens, log_ndtr(r / np.exp(ls)), -0.5 * (r / np.exp(ls)) ** 2 - ls).sum()
    return np.exp(minimize_scalar(f, bounds=(np.log(r.std()) - 5, np.log(r.std()) + 5), method='bounded').x)


def _crossfit_tobit(X, y, splits, groups, cens, inner, alphas=ALPHAS[::2]):
    mu, sd, ls = (np.full(len(y), np.nan) for _ in range(3))
    for tr, te in splits:
        Xt, yt, ct, gt = X[tr], y[tr], cens[tr], groups[tr]
        oof = np.empty((len(yt), len(alphas)))
        for itr, ite in GroupKFold(inner).split(Xt, groups=gt):
            m, s = _standardise(Xt, itr)
            th = None
            for j, a in enumerate(alphas[::-1]):  # strong to weak penalty, warm-started
                th = _tobit((Xt[itr] - m) / s, yt[itr], ct[itr], a, th)
                oof[ite, len(alphas) - 1 - j] = th[0] + ((Xt[ite] - m) / s) @ th[1:-1]
        score = [gauss_ls(yt, oof[:, j], _censored_sd(yt - oof[:, j], ct), ct).sum() for j in range(len(alphas))]
        k = int(np.argmax(score))
        m, s = _standardise(Xt, slice(None))
        th = _tobit((Xt - m) / s, yt, ct, alphas[k])
        mu[te], sd[te] = th[0] + ((X[te] - m) / s) @ th[1:-1], _censored_sd(yt - oof[:, k], ct)
        ls[te] = gauss_ls(y[te], mu[te], sd[te], cens[te])
    return mu, sd, ls


def crossfit(X, y, splits, groups, model=None, var='oof', resid='gauss', inner=5, censored=None):
    """Out-of-fold predictive distribution for the test rows of every (train, test) split: (mu, sd, log score).

    Mean: ridge with the penalty chosen by grouped inner CV (`model=None`), or any sklearn factory `model()`.
    var='oof': homoscedastic SD from grouped inner out-of-fold residuals.
    var='hetero': log-link (quasi-Poisson) regression of those squared residuals, consistent for E[r^2 | x].
    var='insample': SD of training residuals of the final fit (optimistic; kept to demonstrate the failure).
    resid='kde': location-scale model whose standardised-residual density is a Gaussian KDE of the training rows'
    out-of-fold standardised residuals (absorbs skew and unexplained mixtures), mixed with weight DEFENSIVE with a
    wide Gaussian so that a single tail row cannot dominate the mean score.
    censored: boolean mask of left-censored rows (y is an upper bound). Fitting then uses the penalised Tobit
    likelihood (Gaussian, homoscedastic, default ridge path only), and scoring uses log P(D <= y) for those rows.
    """
    if censored is not None:
        if model is not None or var != 'oof' or resid != 'gauss': raise NotImplementedError('censored fitting: Gaussian, homoscedastic, default mean model only')
        return _crossfit_tobit(X, y, splits, groups, np.asarray(censored, bool), inner)
    mu, sd, ls = (np.full(len(y), np.nan) for _ in range(3))
    for tr, te in splits:
        cv = list(GroupKFold(inner).split(X[tr], groups=groups[tr]))
        if model is None:
            P = ridge_oof(X[tr], y[tr], cv)
            k = np.argmin(((y[tr, None] - P) ** 2).mean(0))
            mu[te], oof = _ridge_predict(X, y, tr, te, ALPHAS[k]), P[:, k]
            fit_tr = _ridge_predict(X, y, tr, tr, ALPHAS[k]) if var == 'insample' else None
        else:
            m = model().fit(X[tr], y[tr])
            mu[te], oof, fit_tr = m.predict(X[te]), cross_val_predict(model(), X[tr], y[tr], cv=cv), m.predict(X[tr])
        r = y[tr] - oof
        if var == 'hetero':
            v = make_pipeline(StandardScaler(), PoissonRegressor(alpha=1e-4, max_iter=1000)).fit(X[tr], r ** 2)
            s_tr, sd[te] = np.sqrt(v.predict(X[tr])), np.sqrt(v.predict(X[te]))
        else:
            s_tr = np.std(y[tr] - fit_tr) if var == 'insample' else np.sqrt(np.mean(r ** 2))
            sd[te] = s_tr
        if resid == 'kde':
            z = (y[te] - mu[te]) / sd[te]
            ls[te] = np.logaddexp(np.log1p(-DEFENSIVE) + gaussian_kde(r / s_tr).logpdf(z), np.log(DEFENSIVE) + norm.logpdf(z, 0, 4)) - np.log(sd[te])
        else:
            ls[te] = gauss_ls(y[te], mu[te], sd[te])
    return mu, sd, ls


def crossfit_binned(X, y, splits, groups, edges, Cs=(0.01, 0.1, 1.0, 10.0), inner=5, censored=None, floor=1e-12):
    """Out-of-fold multinomial-logistic predictive distribution over bins B = #(edges < y): (probabilities, B, log score).

    `edges` are fixed in advance (never from the data under evaluation). Left-censored rows are exact as long as their
    bound does not exceed edges[0], because the lowest bin then contains every value they allow. L2 strength is chosen
    by grouped inner CV on log loss.
    """
    edges = np.asarray(edges, float)
    if censored is not None and np.any(y[np.asarray(censored, bool)] > edges[0]): raise ValueError('a censoring bound exceeds the lowest bin edge')
    b, K = np.searchsorted(edges, y), len(edges) + 1
    P, ls = np.full((len(y), K), np.nan), np.full(len(y), np.nan)

    def fit_proba(Xa, ba, Xb, C):
        lr = LogisticRegression(C=C, max_iter=2000).fit(Xa, ba)
        out = np.full((len(Xb), K), floor)
        out[:, lr.classes_] = np.maximum(lr.predict_proba(Xb), floor)
        return out / out.sum(1, keepdims=True)

    for tr, te in splits:
        m, s = _standardise(X, tr)
        Z, bt = (X - m) / s, b[tr]
        Zt = Z[tr]
        loss = []
        for C in Cs:
            oof = np.empty((tr.sum(), K))
            for itr, ite in GroupKFold(inner).split(Zt, groups=groups[tr]):
                oof[ite] = fit_proba(Zt[itr], bt[itr], Zt[ite], C)
            loss.append(-np.log(oof[np.arange(len(bt)), bt]).mean())
        P[te] = fit_proba(Zt, bt, Z[te], Cs[int(np.argmin(loss))])
        ls[te] = np.log(P[te][np.arange(te.sum()), b[te]])
    return P, b, ls


@dataclass
class Contrast:
    d: np.ndarray       # per scored row: log q_VC - log q_C, nats
    groups: np.ndarray  # independent units of the scored rows
    pred_c: tuple       # context model output of crossfit / crossfit_binned (all rows; NaN where unscored)
    pred_vc: tuple      # joint model output
    scored: np.ndarray  # boolean mask of scored rows

    @property
    def mean(self): return self.d.mean()

    def ci(self, level=0.95, n_boot=2000, seed=0):
        a = (1 - level) / 2
        return np.quantile(block_bootstrap(self.d, self.groups, n_boot, seed), [a, 1 - a])


def contrast(Xc, Xvc, y, splits, groups, family='gauss', **kw):
    """Held-out log-score improvement of q(D|V,C) over q(D|C), both fitted identically by the chosen family."""
    fit = crossfit if family == 'gauss' else crossfit_binned
    pc, pv = fit(Xc, y, splits, groups, **kw), fit(Xvc, y, splits, groups, **kw)
    d = pv[2] - pc[2]
    ok = np.isfinite(d)
    return Contrast(d[ok], np.asarray(groups)[ok], pc, pv, ok)
