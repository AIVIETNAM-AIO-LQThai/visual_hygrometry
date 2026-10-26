# M1 inference redesign after review 4

Scope: the mathematical and statistical decisions behind the projection-free contrast, the evidence for each, and what is still open. Evidence is in notebooks 11 (synthetic validation), 12 (why the declared notebook 10 analysis failed) and 13 (multi-year NEON audit). Decisions D-054 to D-064 are in [decisions.md](decisions.md).

## 1 · Estimands

- **Primary, E2 = I(D; V | C)**, with C the declared clock, season and conditioning temperature. Nothing visual is derived into C.
- **Secondary, E2_illum = I(D; V | C, K)**, with K a quality-controlled illumination state (a clear-sky index from tower shortwave; contract field `clearsky_k`, role `illum`, SCI level `e2_illum`).
  - Adding K changes the question: E2_illum excludes information the image carries *through* cloudiness. Neither estimand is a pure causal RH-optics effect.
  - In the synthetic illumination world, E2 = 0.021 nats while E2_illum = 0 exactly. The redesigned contrast recovers both (notebook 11).
- **Acquisition-only controls** exist for both contexts (`e2_acq_control`, `e2_illum_acq_control`). The exposure-only p-values of notebook 10 are not humidity findings.
- **Operational gain G(n_fit):** the held-out log-score gain of the defined model pair fitted on the first n_fit days or seasons. It is not E2.
- **Zero-information test Q0:** an exploratory test of H0: V ⊥ D | C.
- **Slow visual information** (review 4, item 5) is preserved. Greenness and phenology features stay in V. Splitting E2 into a slow part I(D; V̄ | C), with V̄ a causal trailing visual history, and a fast part I(D; V | C, V̄) defines *new* estimands. These are declared as future work and are not used in any result here.

## 2 · Why the visual projection is removed from the primary contrast

E[V | C] is a function of C, so in the population q(D | C, E[V|C]) = q(D | C): the projection is redundant.

In finite samples it is not. The train-only boosted projection is cross-fitted over days on training rows but extrapolated on test rows.
- On CPER fit rows it explains 63 % of the daily-mean image variation, and none on evaluation rows (notebook 10 §3).
- Its full-sample version also leaked slow information into the null generator.

Notebook 12 shows that the declared HARV loss had a second, independent cause: an extrapolating seasonal basis.
- One day-of-year spline column moved the joint prediction by −9.8 K, because the joint model's ridge penalty was 30× smaller than the context model's.
- The declared estimates moved by more than a nat under different inner fold assignments.

Decision: **the primary contrast has no visual-derived context column.** The projection and its variants are kept only to reproduce notebook 10 (`ctx_proj` role; D-035 superseded for new analyses).

## 3 · The projection-free contrast

| component | definition | reason |
|---|---|---|
| context bases | nested fixed levels: L1 (hour Fourier, T spline, T × hour, day-of-year spline), L2 (+ third hour harmonic, T × season, finer day-of-year spline), L3 (+ T-spline × hour tensor) | test adequacy for non-linear T, hour, season and interaction structure (review 4, item 1) |
| season beyond the record | day of year clamped to each split's training range (`worlds.split_levels`) | removes the extrapolation that caused the HARV failure (notebook 12 §2) and a 0.31-nat instability in development (notebook 11 §2) |
| capacity | level chosen per split by week-grouped inner CV of the context-only log score on training rows only (`inference.select_capacity`); the same level enters both models | training-only capacity choice that never reads visual columns or test labels |
| penalty | ridge, chosen by week-grouped inner CV | days within a week are dependent |
| joint model | chosen context design + V, with V clipped to its training rows' 0.5–99.5 % range (`inference.clip_to_training`) | a fitted visual coefficient is never extrapolated |
| predictive | homoscedastic robust Gaussian (1 % Cauchy(μ, 4σ)), common support on (hour, T) | D-031, D-038, D-039 |
| numerics | SVD falls back from divide-and-conquer to QR iteration on rank-deficient designs (`scoring._svd`) | one clamped design was exactly singular |

**Captured information, not E2.** E Δ̂ = I − KL_VC + KL_C, so the contrast is the information captured by this model pair.
- Information that acts only through the variance, or in rare rows, is largely missed. In the near-saturation world the contrast captures nothing of a true 0.018 nats (notebook 11).
- A context the levels cannot represent leaves a small positive KL_C. The hour-varying T curvature and season × T worlds give +0.004 to +0.006 nats with 3 seasons.

## 4 · Zero-information test

- **Construction.** The cyclic-shift refitting test (D-036, D-044), with:
  - shifts of at least 7 days within seasons (strata), one shift for every stratum;
  - V = V̂ + R, where V̂ is the in-sample linear projection on the label-free L3 context basis, not a boosted projection;
  - R shifted cyclically and re-orthogonalised;
  - every refit following the same training-only rules, with clipping applied to observed and null V alike.
- **Assumptions.** The residual series must be stationary within strata, and the wrap-around must be acceptable. Camera epochs (notebook 13: HARV unit change 2021–2022, CPER view change 2019–2020) must be declared strata.
- **Restricted shifts.** The shifts {7, …, n − 7} are not a group, so exactness under exchangeability is not guaranteed. In the base null, the declared test and the test over every non-identity shift both rejected at 0.056 (160 replicates, notebook 11 §2).
- **A positive null median is not by itself invalidity** (review 4, item 3). In the context-nonlinearity worlds the null median is positive because V̂ keeps the context repair, and the test stays calibrated.
- **Persistence beyond the validated range.** CPER's ρ ≈ 0.95 lies outside the range validated before review 4. The AR 0.9–0.95 nulls of notebook 11 test it directly, and CPER's 2023 p-value is not confirmatory evidence.

## 5 · Operational gain and intervals

- **Design.** 3 seasons: fit on seasons 1–2, evaluate season 3. 1 season: 60 % / 2-day purge / 40 %.
- **Interval.** Week-cluster t over one evaluation season. It is conditional on that season, and between-season variation of G is not in it.
- **Frozen target.** The same fitted models scored on 5 further simulated seasons, inside the evaluation day-of-year window.

## 6 · Validation

**Suite.**
- 15 development worlds (40 replicates, shared seeds) and 16 untouched validation worlds (150 replicates, one seed range per world, seeds 300 000+).
- Both designs; gates declared before the validation run, for the 3-season design only.
- No NEON data used.

**Outcome: the protocol fails validation (D-064).**

| gate | 3-season result | outcome |
|---|---|---|
| G1 Type I ≤ 0.085, every null | 0.047–0.080 in seven nulls; 0.100 at AR 0.9; 0.107 (tanh T × sin hour); **0.787 (season × hour)** | fail |
| G2 power ≥ 0.80, linear positives with truth ≥ 0.03 | 0.93, 1.00, **0.79** (slow state), 1.00 | fail, narrowly |
| G3 \|bias\| ≤ 0.01, nulls and linear positives | ≤ 0.009 | pass |
| G4 cross-fit interval covers truth ≥ 0.85 | 0.86–0.90 in adequate nulls; 0.71 (AR 0.9), 0.79, 0.79, **0.49** (slow state) | fail |
| G5 chronological interval covers its target ≥ 0.85 | 0.89–0.94, except **0.74** (slow state) | fail |
| G6 / G7 stability under 1 % deletions (random / lowest D) | ≤ 0.027 / ≤ 0.024 nats | pass |
| G8 captured ≤ truth + 0.005, non-Gaussian positives | 0.005 of 0.025; 0.001 of 0.015 | pass |
| G9 adequacy flags ≤ 0.10 | 0 everywhere, including the world where G1 fails at 0.79 | pass, uninformative |

**Post-hoc (notebook 11 §6, new seeds, not a re-validation).**
- An extra level L4, hour basis × day-of-year spline, makes the test calibrated in the season × hour world (0.767 → 0.050).
- Its estimate still carries +0.005 nats of context repair.
- The boosted adequacy model scores 0.10 nats worse than the ridge context everywhere, so it can never flag.

**1-season design.** Its test holds except in the season × hour world, but its effect sizes are not usable: power 0.56 at 0.03 nats, bias −0.008 to −0.030, 90th-percentile instability up to 0.15 nats (D-061).

**What the redesign achieved.**
- No visual-derived context; seasonal extrapolation and coefficient extrapolation removed.
- An unbiased, stable point estimate across persistence, seasons, onsets, camera services, heteroscedastic D and illumination.
- E2 and E2_illum separate exactly as designed.

**What remains open.**
1. Context capacity for a diurnal cycle that changes with season, i.e. solar time against clock time.
2. Intervals when information or residuals persist for weeks.
3. The shift test at AR ≥ 0.9.
4. A working adequacy diagnostic.

## 7 · Consequences for the next NEON stage (not run)

None of the following has been done; each needs review first.
1. **No NEON effect size or test** from the current protocol (D-064).
2. **Context.**
   - Add an hour × season level (L4), or a solar-time hour basis from solar geometry (`solar_elev_deg` is already in the contract).
   - Develop on new worlds whose diurnal cycle follows sunrise and day length, then validate on a fresh suite.
3. **Adequacy diagnostic.** It must be at least as strong as the audited context. Candidates:
   - the richest level plus boosted residual terms, scored on the same inner splits;
   - or, as a diagnostic only, never in the primary contrast, the context model plus a training-only E[V | C], whose gain measures the context repair V could perform (the `proj` diagnostic of notebook 04, which was the sensitive one).
4. **Intervals.**
   - With week clusters, intervals are valid only when the information does not persist for weeks.
   - Options: report Q0 and the point estimate only, with the interval left open (as D-033); or use season-level replication (≥ 5 seasons per site, so several independent seasonal units).
5. **Persistence.** The shift test is anti-conservative at AR 0.9 (0.100). CPER's residual (ρ ≈ 0.95) lies beyond the validated range, so CPER test results remain exploratory unless regime-level strata or longer records restore calibration.
6. **NEON data (notebook 13).**
   - Declare camera epochs as strata before any extraction: HARV 2019–2021 / 2022–2023, CPER 2019 / 2020–2023.
   - The first homogeneous block is CPER 2020–2023 (four seasons).
   - HARV's July 2021 label fault and its 2022 radiation-error anomaly must be explained before HARV years are pooled.
   - Image regions must be re-defined per epoch.
