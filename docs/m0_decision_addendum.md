# M0 decision addendum: response to the independent estimator review

Review decision: **M0 accepted as an exploratory milestone; the estimator is not approved for confirmatory Exp 2a. MODIFY.** This addendum records what the revision changed, what it established, and what remains open. Evidence: [notebooks/03](../notebooks/03_inference_and_density_revision.ipynb) (new), [notebooks/01](../notebooks/01_information_estimator.ipynb) (unchanged record of the first validation, including its failures), unit tests.

**Status after revision: not yet acceptable for confirmatory use.** 7 of 8 pre-declared validation criteria pass. A5 fails: a temperature non-linearity that the context model cannot represent but the image encodes produces false positives that neither the test nor the adequacy diagnostic catches reliably.

## What kind of evidence each statement rests on

| category | examples in this revision |
|---|---|
| **implementation behaviour** (unit tests, exact) | η² independent of row order with ties kept together; Tobit recovers parameters under 25–50 % censoring where least squares is biased; censored rows scored by the CDF; binned family exact for censored rows below its lowest edge; oracle conditionals reproduce the analytic CMI; day-cluster SE formula; permutation test rejects a strong signal, accepts a null, refuses an incomplete day × slot grid; `.env` ignored by Git |
| **synthetic statistical evidence** | Type I, power, coverage and bias tables of notebook 03 (development suite, seeds 2000–4039; validation suite, seeds 90 000–93 039, worlds not used in development) |
| **unverified assumptions** | that real `D | C` resembles any synthetic world; day-level exchangeability of real days; adequacy of a ~10-feature visual set; NEON probe shielding, timestamp pairing, camera geometry |
| **meteorological evidence** | none yet |

## Review items

| # | item | status | evidence |
|---|---|---|---|
| 1 | separate evidence (Q0) from effect size (Q1) and from the threshold question (Q2) | **done** | `inference.py`; notebook 03 intro and §1 |
| 1 | dependence-aware inference calibrated under misspecification, multimodal errors, serial dependence, sensor-correlated error | **done, with one failure** | dev §2–3, validation §6 |
| 2 | flexible predictive density; binned vs continuous information | **done**; no single family is safe | §4, V-F1/V-F2 |
| 3 | censored training likelihood | **fixed** (penalised Tobit fit; binned alternative) | §5, V-F3, unit tests |
| 4 | aspirated independent conditioning thermometer for confirmatory claims | **adopted as policy** (D-020) | `docs/metadata_policy.md`; V-S |
| 5 | ≤ ~10 predefined features first; a second frozen-encoder experiment predeclared | **plan declared** (D-021, D-022) | below |
| 6 | η² row-order dependence | **fixed** | `policy.eta2`; `test_eta2_ignores_row_order_and_keeps_ties_together` |
| 7 | preserve failures, mark post-hoc changes, separate validation suite | **done** | notebook 01 untouched; §6 criteria declared before its first run |

## Inference: what was compared and what is adopted

Procedures: cross-fitted scores with a percentile day bootstrap (M0 baseline); cross-fitted scores with a day-cluster t; **frozen hold-out** (fit on half of the days, score the other half once, day-cluster t); a **refitting day-block permutation test** (V residuals given the context permuted between whole days, rows matched by time of day, re-projected on the context's orthogonal complement, joint model refitted per draw). Each test is one-sided at α = 0.05.

| finding | development | validation |
|---|---|---|
| bootstrap / cluster-t on cross-fitted scores: Type I (adequate context) | 0.000–0.010 (over-conservative) | 0.000–0.007 |
| ... coverage of a 0.05-nat effect | 0.83 / 0.86 at 60 days | 0.89 (cluster-t) at 90 days |
| frozen: Type I (adequate context) | 0.020–0.040 | 0.040–0.047 |
| frozen: coverage of its target / of the truth | 0.88–0.95 / 0.93 (P1) | 0.93–0.95 / 0.93–0.94 |
| permutation: Type I (adequate context; hour-misspecified) | 0.060–0.090; 0.000 | 0.047–0.060; 0.000 |
| permutation: power at 0.05 nats | 0.99 (60 d) | 0.97 (90 d) |
| any procedure, context misspecified in a variable the image encodes | 100 % rejection (N3b) | 83–100 % (V-N4) |
| any procedure, sensor-correlated error (atmospheric null true) | 30–70 % | 45–99 % |

**Adopted (D-019):** Q0 is answered by the permutation test. Q1 is answered by the frozen hold-out interval, reported as *information captured by the frozen models*, never as `I(D;V|C)`. Q2 compares the frozen interval's lower bound with a threshold δ fixed before the confirmatory data. The percentile bootstrap is retired for both questions.

**Failed attempts kept on record.**
- The first permutation implementation reused the simulation seed for its permutation stream.
- Its residualisation without re-projection was suspected of anti-conservatism (0.14 / 0.095 in one null world). A 600-replicate check found raw permutation exact (0.040) and the re-projected version slightly conservative (0.035). The notebook's 0.090 for N2 at 39 draws is still unexplained.
- A single dependent 2000-day sample used as the Monte-Carlo truth was off by ~0.02 nats; truths now come from iid copies of each world.

## Predictive families

| family | strength | failure |
|---|---|---|
| Gaussian (+ transform rule) | most efficient on Gaussian data; with the rule, unbiased on skewed worlds (+0.004 dev, −0.003 val) | misses spread-only information entirely (−0.24 dev, −0.20 val) |
| location-scale + KDE residual, 1 % defensive component (+ rule) | recovers most spread information (−0.039 dev, −0.032 val); Gaussian-level efficiency on Gaussian data | without the defensive component, catastrophic tail rows (−637 nats); on raw skewed scale −0.096 |
| binned (fixed edges, lowest edge at the censoring bound) | exact under censoring; unbiased for `I(B;V|C)` | blind to spread changes around a context-dependent centre (0.010 vs 0.208 dev; 0.000 vs 0.163 val); binning costs 3–12 % of the continuous information |

The **transform rule** never sees V: model log D when D > 0 and the context-only model's held-out score (Jacobian-corrected) prefers it. The contrast is invariant to a shared monotone map. It chose log in 100 % of skewed samples and 0 % elsewhere.

**Adopted (D-014 resolved → D-023):** Exp 2a reports a family panel with matched context. A GO requires the effect under `ls-kde+T`. `gauss+T` is the efficiency reference. The binned family is used wherever censoring is non-negligible and is always labelled as information about binned D. A V × context interaction variant of the binned family was tried and rejected: null bias −0.034, Gaussian-world estimate 0.015 vs 0.040.

## Censoring

The M0 code fitted censored bounds as exact targets. The fit now maximises a penalised left-censored Gaussian likelihood (penalty by day-grouped CV) with an out-of-fold censored-likelihood SD. In a 13.5 %-censored world, Tobit is +0.011 against the observation-level truth (dev) and +0.001 (validation, 10.4 % censored); naive fitting happened to be close in these worlds. Dropping censored rows changes the estimand to a selected-population contrast (0.172 vs 0.188 observation-level vs 0.199 latent) and is not acceptable for confirmatory work. The KDE family does not support censoring yet; censored regimes use Tobit or binned.

## What remains open (blocks confirmatory Exp 2a)

1. **Context capacity vs what the image encodes about context (A5).** If V encodes a function of T or hour that the context model cannot represent, every procedure reports information. The squares/products adequacy diagnostic caught a quadratic (100 %) but not a localised bump (39 %). Proposed remedy, not yet implemented: a flexible context basis in T and hour × T (splines or trees) given identically to both models, and a non-parametric adequacy diagnostic. Develop on development worlds and validate on a third fresh suite. This is the next focused task; no new review is needed until it passes.
2. Permutation Type I of 0.09 in one strongly dependent development world at 39 draws (unexplained; validation was 0.047–0.060).
3. Censored support for the KDE family.
4. Real-data dependence structure, which sets power and the threshold δ (D-018).

## Plans declared now

- **D-020, sensor roles.** Confirmatory physical claims require the conditioning temperature from an independent aspirated unit, and the label from a separately shielded unit. Conditioning on the label unit's own temperature is a mandatory *sensitivity* analysis (exact D ↔ RH invariance, coupled errors), never the sole evaluation. **NEON is approved for public-data feasibility only** until probe shielding, image–sensor geometry, timestamp pairing and radiation bias are verified.
- **D-021, Exp 2a-A (interpretable).** At most 10 visual features, defined before any label is inspected: far/mid/near region contrast and its ratio (apparent extinction proxy), sky-band luminance and blue/red ratio, horizon-band saturation, ground-region darkness/gloss (wetness proxy), vegetation colour index, and image-wide sharpness. All are computed on radiometrically normalised images with masks fixed per site. A null result here does **not** end the identifiability study.
- **D-022, Exp 2a-B (frozen encoder).** A pretrained image encoder kept frozen. Its embedding is reduced to k ∈ {4, 8, 16, 32} dimensions by PCA fitted on non-evaluation days only, with day-grouped tuning and the same family panel and inference. k is reported as a dimension-vs-days curve; no k is chosen on evaluation data. Notebook 01 §6 shows why the budget matters.

## Reproducibility note on notebook 01

Notebook 01's stored outputs are the pre-revision record. Re-executed against the revised modules it runs without error, and 8 of its 11 result tables reproduce exactly. The three that change involve the KDE family, which now carries the 1 % defensive component (regime case: −0.029 → −0.046 against truth). The Gaussian ridge path was re-implemented in numpy with identical numerics.

## NEON

The API token in `.env` works (HARV 2023-07 file listings: 60.9 MB RH, 21.5 MB aspirated temperature). `.env` was not ignored by Git and now is. No NEON data were downloaded in this revision.
