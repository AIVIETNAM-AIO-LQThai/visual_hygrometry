# M1.4: bounded CRT sampler experiment, declared plan

**Status:** declared 2026-11-01, before any code for the repaired samplers exists and before any of the analyses below has run. It implements discussion 8 (decisions D-080 to D-082). This is the **only** design iteration: after notebook 19 (synthetic validation) and notebook 20 (re-audit on the CPER features), NEON Q0 development either proceeds as defined in §8 or closes for the present phase. Implementation bugs may be fixed. Each fix is recorded in §10 with its date before the affected analysis is re-run, and no fix may change a criterion.

## 1 · What is being tested

Notebook 17 found the CRT sampler unsuitable on the real CPER features (D-077):
- within-day persistence was under-simulated;
- the residual scale depends on hour and temperature;
- the innovations are heavy-tailed and skewed.

M1.4 asks whether **one** repaired generator meets both of the following. If it does, a further question decides whether running the real-data Q0 is worthwhile.
1. Acceptable CRT Type I under several independently generated null mechanisms, judged by empirical confidence intervals.
2. Satisfactory **held-out** diagnostics of the conditional visual distribution, by an audit that is itself shown to detect samplers that inflate Type I.

The M1.3 verdict is not revisited: the notebook 17 sampler stays unsuitable.

## 2 · Common structure of the generators

Every generator draws V* = f̂(C) + E*.
- f̂(C) is the cross-fitted boosted E[V | C] of `inference.project`. It uses the raw context C = (hour, T, day of year, solar elevation, daylight fraction, season), is grouped by week, and never reads labels.
- E* is a residual process fitted per season on E = V − f̂(C).

Two candidates are compared under one validation procedure (§4–§6). Neither is chosen from a real CPER statistic of the image–label relation.

**Scale model (both candidates).** Per season and feature, log E[e² | C] = a + b₁ sin(2πh/24) + b₂ cos(2πh/24) + c·T_z.
- T_z is temperature standardised within the season.
- The model is fitted by log-link (quasi-Poisson) regression of e², which gives 4 parameters per feature and season.
- Z = E / ŝ(C) is the standardised residual.

**Candidate P, parametric.** Z = u_day + w_within, per season.
- **Within-day AR(1), φ_w, simulation-calibrated.** On a grid φ ∈ {0, 0.05, …, 0.95}, unit-variance AR(1) days with the season's actual day lengths and slot order are simulated, 200 sets per grid point. Simulated and observed residuals are both day-demeaned before the lag-1 statistic is computed, so the comparison is like for like. The function E[r̂(φ)] is inverted by linear interpolation. The same simulations give the expected within-day variance of the deviations, g(φ), and the expected variance of a day mean, h(φ), both per unit of σ_w².
- **Variance components.** σ_w² = var(observed deviations) / g(φ̂_w), and σ_u² = max(var(observed day means) − σ_w² h(φ̂_w), 0.05 · var(observed day means)).
- **Day-level AR(1).** ρ_u comes from the Kendall-corrected lag-1 of the day means (`inference._ar1`), corrected for the within-day contribution: ρ_u = ρ_obs · var(day means) / σ_u², clipped to [0, 0.95].
- **Cross-feature dependence.** The correlation matrices of the observed day means and of the within-day innovations ŵ_t − φ̂ ŵ_{t−1} are used, scaled by the calibrated standard deviations.
- **Tails.** Within-day innovations are multivariate Student t, with one shared mixing variable per row so that tails are joint across features. The degrees of freedom are ν = 4 + 6/κ̄, where κ̄ is the mean excess kurtosis of the standardised within-day innovations, clipped to [0.25, 6]. Day-level innovations are Gaussian.

**Candidate R, resampling.** Z = u*_day + w*_donor, per season.
- **Day means.** An AR(1) with the Kendall-corrected coefficient per feature. Its innovation *vectors* are resampled jointly from the observed day-mean innovations û_d − ρ̂ û_{d−1}, which keeps the cross-feature dependence and tails of day means.
- **Within-day deviations.** Each simulated day takes the standardised within-day deviations (from the day mean) of a **donor day**, drawn at random from the same season and the same tercile of daily maximum temperature. The tercile thresholds come from the fitting days. Rows are matched by nearest hour, as in `inference.donor_sampler`. This keeps the within-day dependence, the cross-feature structure and the joint tails of real days.
- **Assumption.** Within-day deviation days are exchangeable given (season, daily-max-T tercile). §6 checks this.

**Deliberately misspecified samplers** (variants of P unless stated):

| id | sampler | expected defect |
|---|---|---|
| M-a | the notebook 17 sampler (`inference.conditional_sampler`, unchanged) | within-day persistence too weak, Gaussian, homoscedastic |
| M-b | P with φ_w = 0 | no within-day persistence |
| M-c | P with Gaussian innovations and no scale model | homoscedastic, light tails |
| M-d | P with identity correlation matrices | independent features |
| M-e | P with ρ_u and φ_w × 1.5 (capped at 0.95) | over-persistent; expected conservative, so *acceptable* for Type I |

## 3 · Worlds and label mechanisms

All worlds use the real CPER 2020–2023 context rows: 4,817 rows on hourly slots, with their seasons, days, hours and temperatures. Synthetic visual residuals are scaled to the real per-feature residual SDs and correlation, and f(C) is the real f̂(C).

**Label mechanisms** are fitted once on the real labels given C only, never with V. They are independent of V by construction.
- **Context-only mean.** M̂(C) is the out-of-fold mean of the protocol's context-only model with context S, leave-one-season-out. ε = D − M̂(C).
- **LR:** candidate R's structure applied to the univariate ε: day-mean AR(1) with resampled innovations, donor days within season and T tercile, and the scale model.
- **LP:** candidate P's structure applied to ε.
- **Label audit.** Each mechanism's persistence and shape are compared with the real ε: within-day lags 1–3, day lags 1 and 7, sd_hour, sd_temp and kurtosis. The audit is reported, not used as a gate, because the label is never related to V here.

**Null worlds** (D* = M̂(C) + ε*, with ε* independent of V given C):

| world | V | label mechanism |
|---|---|---|
| W0R | the real CPER features (fixed) | LR |
| W0P | the real CPER features (fixed) | LP |
| W1 regime | f(C) + σ ⊙ (a 3-state Markov day type (stay probability 0.75) with a type-specific mean shift (fixed draw, SD 0.8σ), scale (0.7 / 1.0 / 1.6) and within-day AR (0.2 / 0.4 / 0.6), plus a day-level AR(0.5) component; Gaussian, real correlation) | LP |
| W2 volatility | f(C) + σ ⊙ (a day-level AR(0.6) plus a within-day AR(0.4) whose innovations follow GARCH(1,1) within the day (α = 0.15, β = 0.75; reset at each day start) with multivariate t₅ shocks; scale × (1 + 0.4 sin(2π(h − 9)/24)) · exp(0.15 T_z)) | LP |
| W3 long memory | f(C) + σ ⊙ (a day-level ARFIMA(0, 0.4, 0), truncated at 200 lags, with 40 % of the variance, plus a within-day AR(0.5) with skewed innovations (standardised exp(0.5 N))) | LP |

None of W1–W3 lies in either candidate's model class: regime mixtures, conditional volatility and long memory are outside it. W0 conditions on the observed images.

**Positive worlds (power)** are W0R and W0P with D* = M̂(C) + ε* + b·z.
- z is the standardised first principal component of the real residuals V − f̂(C).
- b = σ_ε √(e^{2c} − 1), with planted c ∈ {0.03, 0.05} nats.
- **Three quantities are kept apart:**
  - the planted c is a Gaussian approximation;
  - the true conditional mutual information differs, because ε* is heavy-tailed and heteroscedastic;
  - the observed held-out gain G is reported as the mean contrast of the datasets.

## 4 · Type I gate (notebook 19)

**The test.** The CRT statistic of the validated protocol: the leave-one-season-out held-out log-score contrast.
- Robust Gaussian scoring, V clipped to the training range (0.005), common support on (hour, T).
- The context is **fixed at S**, the context chosen in 3 of 4 CPER seasons. The CRT holds D and C fixed, so a label-dependent context choice does not affect its validity given the chosen context.
- 39 draws per test; reject at p ≤ 0.05, which is exact level 2/40 = 0.05.

**Datasets.**
- Candidates: 400 datasets per (candidate, null world), 2 × 5 pairs.
- Misspecified samplers: 200 datasets per (sampler, null world), 5 × 5 pairs.
- In W0, V is fixed, so each sampler is fitted once. In W1–W3, each sampler is refitted on each dataset's V.

**Rules** (95 % one-sided Clopper–Pearson bounds; tolerance 0.10):

| outcome for a (sampler, world) pair | rule | n = 400 | n = 200 |
|---|---|---|---|
| acceptable | upper bound ≤ 0.10 | ≤ 29 rejections | ≤ 12 |
| demonstrated inflation | lower bound > 0.10 | ≥ 51 | ≥ 28 |
| insufficient precision | otherwise | 30–50 | 13–27 |

- A **candidate is eligible** only if it is acceptable in all five null worlds.
- A misspecified sampler is classed *invalid* if it shows demonstrated inflation in any world, and *acceptable* if it is acceptable in all.
- Under exact level 0.05, a valid candidate passes a given world with probability ≈ 0.98.

## 5 · Held-out diagnostic audit

**Blocks.** Each season's days are split into 4 contiguous blocks of about 23 days.
- For held-out block k, the residual process is fitted on the other blocks of that season, minus g days on each side of block k.
- The gap g comes from a label-free dependence analysis of the real residuals (notebook 19 §1): the smallest lag at which the median, over features and seasons, of |ACF of day means| falls below 0.1, bounded to [2, 7] days.
- Alternate weeks are not used.
- f̂(C) is the cross-fitted fit on all rows, as in the sampler, and is out-of-fold by week. Only the residual process (scale, dependence, innovations, donors) is fitted on training blocks. It then simulates the held-out block's residuals from the block's own C.

**Held-out diagnostics.** These are computed on the held-out block's residuals and on 100 simulations; a cell is outside if it lies outside the 95 % band of the simulations.

| family | statistic per feature (or pair) and block |
|---|---|
| H1 | within-day lags 2 and 3 of the day-demeaned residuals |
| H2 | lag-1 autocorrelation of the squared day-demeaned residuals (volatility clustering) |
| H3 | day-level lag-7 autocorrelation of day means |
| H4 | lagged cross-feature correlation corr(w_i(t), w_j(t+1)) within days, for i ≠ j |
| H5 | the share of rows where ≥ 2 features have \|z\| > 2 (z standardised by the block's SDs); one per block |
| H6 | the SD ratio of the upper to the lower temperature tercile within each hour band (< 10 h, 10–14 h, ≥ 14 h), and the SD ratio of hour ≥ 14 to hour ≤ 9 |

**Calibration targets** are matched by construction and are reported only, never as validation evidence. They are the within-day lag 1, the day lag 1, the in-sample sd_hour and sd_temp, and the marginal kurtosis.

**Decision statistic.** A = the maximum over H1–H6 of the share of cells outside, pooled over seasons and blocks.

**Validation of the audit itself (notebook 19), on W1–W3 only**, since these are the worlds where the true V law is known:
1. Each (sampler, world) pair gets 40 V realisations: 20 for calibration and 20 for evaluation.
2. Threshold: τ_A = max(0.10, the 90th percentile of A over the calibration realisations of every pair classed *acceptable* in §4).
3. The audit is **validated** if, on the evaluation realisations:
   - its mean flag rate (A > τ_A) over the pairs classed *invalid* is ≥ 0.80;
   - its flag rate is ≤ 0.20 for every pair classed *acceptable*.
4. If no pair is classed invalid, the audit's sensitivity cannot be tested, and the outcome is *inconclusive*.

## 6 · Exchangeability checks for candidate R

These are label-free and use the real CPER residuals (notebook 19 §1). Each is reported.
1. Donor pool sizes per (season, T tercile).
2. Whether the within-day deviation statistics (SD, lag 1) depend on day of year (first versus second half of the season) or on daily temperature *within* a tercile. Such dependence would violate exchangeability given C.
3. The diversity of draws: the number of distinct donor days per draw, and the share of tied values in the CRT null distribution in W0.

Weather-regime dependence that is not a function of C, such as cloudiness, is part of V's randomness given C and does not by itself violate exchangeability. §6 reports it, but it is not a criterion.

## 7 · Power (notebook 19)

- In W0R and W0P with planted c ∈ {0.03, 0.05}, run 200 datasets per (eligible candidate, world, c).
- Report the rejection rate with a two-sided 95 % Clopper–Pearson interval, the planted c, and the mean observed G.
- **Predeclared scientifically meaningful effect: 0.05 nats per row** (planted, Gaussian approximation). This is the illustrative threshold of [research_scope.md](research_scope.md), and is about twice the mean CPER gain.

## 8 · Decisions

**Choice of candidate.** This is fixed before notebook 20 and uses notebook 19 only.
- If both candidates are eligible, take the one with the higher mean power at 0.05 over W0R and W0P.
- If the two powers are within 0.03 of each other, take the one with the lower maximum Type I upper bound.
- Notebook 20 audits every eligible candidate and reports them all, but only the chosen one can lead to Q0. There is no switching after notebook 20.

**Outcome rules:**

| outcome | condition | action |
|---|---|---|
| **suitable** | the chosen candidate is eligible (§4), the audit is validated (§5), and A ≤ τ_A on the real CPER features (notebook 20) | go to the power check |
| **Q0 authorised (exploratory)** | suitable, and power ≥ 0.80 (point estimate) at 0.05 nats in both W0R and W0P | run the CRT on the real 2020–2023 labels with the notebook 18 protocol (context selection, 199 draws); report one exploratory p-value, with no interval and no confirmatory claim |
| **methods result only** | suitable but power < 0.80 | no Q0; report the minimum detectable effect as a methods limitation; NEON Q0 development closes |
| **closed** | any candidate criterion fails, or is insufficiently precise, or the audit is not validated or inconclusive | NEON Q0 development closes for this phase; no further design iteration |

**Interpretation.**
- A non-significant Q0 from this test is not evidence of absent visual information.
- A significant one is exploratory evidence of dependence beyond C under this design, on a site and years that informed the method.
- In neither case is it evidence of a moisture-optics pathway: the exposure and illumination pathways of notebook 18 remain.

## 9 · Budget and execution

- **Compute** at the measured costs (0.6 s per CRT statistic and 6 s per sampler fit, on CPER-sized data):
  - about 4–5 h on 18 workers for notebook 19's Type I and power runs;
  - well under 1 h for the audit validation;
  - under 1 h for notebook 20.
  - Hard cap: 10 h of wall time for notebook 19 and 3 h for notebook 20. If the cap is reached, the unfinished pairs are reported as insufficient precision.
- **Code.**
  - The generators, worlds and audit go in `src/visual_hygrometry/samplers.py`, with tests.
  - `suite.pipeline` gains a sampler-factory option for notebook 20, and its defaults stay unchanged.
  - The notebooks only run and report.
- **Seeds** are fixed per (sampler, world, dataset) and recorded.

## 10 · Deviations

| date | deviation | reason |
|---|---|---|
| 2026-11-01, before notebook 19 ran | **Implementation details where §2–§5 were silent.** No criterion is changed.<br>• Candidate R: the resampled day-mean innovations are rescaled so the simulated day means keep the observed day-mean variance under the Kendall-corrected coefficient. Without it, that variance is inflated by about 15–20 %.<br>• Candidate R: a tercile pool without fitting days falls back to the season's fitting days.<br>• Candidate P: the calibration simulations share random numbers across the φ grid, and the table of expected lag-1 values is made monotone before it is inverted.<br>• `persist` multiplies the coefficients after the variances are calibrated.<br>• Worlds W1 and W2: the day-level and within-day parts carry variance shares 0.3 and 0.7, and the totals are normalised to the real per-feature SD. In W1 the regime mean shifts are one fixed draw, so the cross-feature correlation is only approximately the real one.<br>• The audit: H3 is computed only for blocks of ≥ 15 days; correlations need ≥ 4 pairs, and SD ratios ≥ 3 rows per group. | The plan fixed the structure, not these details (`samplers.py`, tests). The R rescaling was found in code review, before any result existed. |
| 2026-11-02, after notebook 19 ran | **Compute estimate, not a rule.** Notebook 19 took 9 h 10 min (Type I 536 min, audit 14 min, power not run), against the §9 estimate of 4–5 h. The estimate omitted the per-dataset sampler refits in W1–W3 and the per-chunk overhead. The 10 h cap was not reached, so no pair was truncated. Notebook 20 took seconds, because the outcome was *closed* before any audit. | Recorded for the budget of later designs; no criterion or result is affected. |
