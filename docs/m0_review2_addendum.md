# Addendum after independent review 2: estimands, inference limits, NEON feasibility

Review decision: **GO for exploratory NEON feasibility; MODIFY for confirmatory Exp 2a.** Evidence:
- [notebooks/06](../notebooks/06_permutation_null_and_chronological_gain.ipynb): permutation null under dependence and non-stationarity, chronological predictive gain, support and robust-score sensitivity, fresh validation;
- [notebooks/07](../notebooks/07_neon_feasibility_HARV_2023-07.ipynb): NEON HARV July 2023.

## Agreed estimands

| quantity | definition | status |
|---|---|---|
| **E2** | I(D; V \\| C), C = clock, season, independent air temperature | the scientific quantity; no interval for it is claimed |
| **G(n_fit)** | expected held-out log-score gain, per row, of an explicitly defined model pair (spline context + train-only visual projection, robust Gaussian, ridge with day-grouped tuning) fitted on the first n_fit days, evaluated on future rows of the same process inside the fit-period support box | the operational effect size for M1; always reported with n_fit, the test period and the excluded share |
| **zero-information test** | refitting conditional permutation test of H0: V ⊥ D \\| C | exploratory, valid only under its exchangeability assumption; its p-value is not a confidence bound on E2 |

G ≤ E2 is not guaranteed in either direction. Context misspecification can make G > 0 when E2 = 0 (notebooks 03–04); an over-simple visual model makes G ≪ E2 (notebook 06 §4: 25–60 % of E2 captured when information varies with T). A positive G is evidence of information only together with an adequate context model. A small G is not evidence of small E2.

## Corrections made in this stage

- **Train-only projection.** Notebooks 04–05 called `inference.project()` on all simulated days, including evaluation and population days, before splitting. Labels were never used, but evaluation-period (C, V) entered a learned context feature: a transductive design. `inference.project_splits` now fits the projection per outer split on that split's training days only (out of fold within them) and predicts test rows. A unit test corrupts test-row visuals and checks that nothing changes. The permutation *null generator* still uses analysis-sample (C, V), never D, to construct surrogate V; this is declared in `perm_test`.
- **Permutation generator.** It supports nearest-slot donors for incomplete day/slot grids, permutation within strata (declared regime breaks, seasons), multi-day units, and an enumerated **cyclic-shift null** that preserves serial dependence.
- **Synthetic worlds** gain multi-day persistence (`Node.persist`), which leaves marginal truths unchanged.
- **Chronological hold-out** (`splits.chrono`): fit on the first 60 % of days, purge 2 days, evaluate the rest. A Newey–West interval (`inference.hac_interval`) was added and is *not* recommended (below).
- **Robust score** (`gauss_ls(robust=(eps, scale))`) is parameterised for the sensitivity analysis. Its log loss is unbounded, only logarithmically growing.

## What the synthetic evidence shows (notebook 06)

| finding | evidence |
|---|---|
| Day-unit permutation absorbs heteroscedastic visual noise, missing frames (nearest-slot donors), a season with a day-of-year context, and a regime break when stratified | development Type I 0.05–0.07 |
| **Multi-day persistence breaks day-unit permutation**: 0.07 / 0.07 / 0.18 / 0.38 at ρ = 0 / 0.3 / 0.6 / 0.85; interleaved day folds also bias the null estimate (+0.012 at ρ = 0.85) | persistence sweep |
| **Cyclic-shift null** (every shift ≥ 7 days, contiguous 16-day folds, 3-day purge): 0.05 / 0.06 / 0.06 / 0.10; valid up to ρ = 0.6 | persistence sweep |
| Chronological G interval: **week-cluster t** covers 0.93–0.96 for ρ ≤ 0.6 (0.85 at ρ = 0.85). Day clusters fail (0.51) and so does Newey–West (0.59), since 30 evaluation days cannot estimate a long-run variance | development |
| Support threshold changes the estimand when information sits at the context tails: cold-end E2 0.023 → 0.021 (q = 0.5 %) → 0.012 (q = 2.5 %) | §4 |
| Over-simple visual models capture only 25–60 % of E2 when information varies with T (G ≪ E2) | §4 |
| Robust mixture weight 0.5–2 % and scale 2–8σ: no effect beyond the 4th decimal once support is restricted | §4 |
| **Fresh validation, all six criteria pass**: shift Type I 0.033–0.067 in six new nulls; power 0.99–1.00; week-cluster coverage of G 0.913–0.960; \|chronological − G\| ≤ 0.002; cross-fit bias vs E2 −0.001; off-support ≤ 2.3 %. At ρ = 0.6 the shift test holds 0.047 and day units reach 0.147 | §5 |

**Adopted procedure** (decision D-036, D-037):
- **Q0:** the cyclic-shift refitting permutation test, stratified at declared regime breaks, with contiguous 16-day folds and a 3-day purge.
- **G:** a chronological hold-out (60 % fit / 2-day purge / 40 % evaluate) with week-cluster t intervals.
- **Declared validity region:** day-to-day persistence ρ ≤ 0.6.
- The percentile bootstrap, the frozen interleaved hold-out and Newey–West with < 60 evaluation days are not used.

## NEON feasibility, HARV July 2023 (notebook 07)

Downloaded through the authenticated API (token in `.env`, never written to outputs): tower-top 1-min RH/T (HMP155), triple-aspirated PRT and radiation (20.9 MB), plus all 1082 PhenoCam `.meta` files and 97 sample JPEGs (56 MB), all under `data/raw/` (ignored by Git).

| item | finding |
|---|---|
| clock | filename time (UTC−5) equals the burned-in UTC stamp to 0 s in 1082 / 1082 frames; capture 4–7 s into the minute |
| join | 96.7 % of frames matched; 842 frames (77.8 %) usable and daylit; 96.5 % of minutes have usable label + aspirated T |
| label formula | Magnus Td − NEON `dewTempMean` = +0.046 K |
| **probe radiation error** | HMP155 − aspirated PRT: +0.06 K at night, +0.55 K by day, median +0.82 K and 95th percentile +2.0 K above 900 W m⁻² (slope +0.077 K per 100 W m⁻²). The label D from the probe's own temperature is therefore biased high by the same amount, correlated with sunshine (r = +0.42). Shield type undocumented. |
| **near-saturation plateau** | RH ≥ 97 % in 13 % of minutes but never above 99.02 %, although fog is visible in frames. The per-minute instrument censor rule fires on 5 minutes; the 90–100 % specification would censor 3.3 %. |
| inter-sensor consistency | aspirated T below the probe dew point in 0.3 % of minutes (min −0.88 K) |
| pixel leakage | the overlay burns in UTC time, camera temperature (r = +0.90 with air T) and exposure; fixed position, fixed 3.1 % mask |
| acquisition leakage | auto-exposure value r = −0.64 with incoming SW |
| **camera processing** | auto-exposure, AGC and in-camera haze compensation (`auto_haze=1`) in every frame; JPEG only |
| persistence | daytime daily-mean D lag-1 autocorrelation +0.03 (one month; crude) |

## Issues that remain before confirmatory Exp 2a

1. **Label definition at NEON (consequential, review requested).** The probe-temperature label carries a sunshine-correlated error of ~+0.5 K by day (up to +2 K). The hybrid label (aspirated T with the probe's dew point) removes the heating term but couples label and conditioning temperature through one unit. *(Corrected after review 3: it does not break D ↔ RH invariance. At fixed aspirated temperature D_h and RH_h are exact inverses; only consistency with NEON's probe-referenced RH changes.)* Synthetic results (notebook 01 §9) put the spurious E2 from such an error at 0.01–0.03 nats.
2. **Near-saturation label plateau (consequential, review requested).** The probe never reports above 99.02 % RH although fog is visible, and NEON's per-minute uncertainty barely triggers the instrument-derived censor rule (5 minutes). The fog/dew regime, where visual evidence is strongest, is where labels are least trustworthy. A censoring rule from the 90–100 % specification (3.3 % censored), or an independent saturation indicator, must be chosen before any fog analysis.
3. **In-camera processing.** `auto_haze=1`, auto-exposure and AGC are on in every NEON frame, and only JPEG is available. Any extinction or haze pathway estimated on these cameras is confounded by in-camera compensation. NEON can test the pipeline and an overall E2, but not an extinction mechanism.
4. **Persistence per site and season.** The validity region is ρ ≤ 0.6. HARV July 2023 shows daily-D lag-1 autocorrelation +0.03, from one month only; it must be estimated per site and season before analysis, and longer records are needed if it is high.
5. **Estimand gap.** Exp 2a reports G(n_fit) with n_fit and the test period stated; no interval for E2 exists. G ≪ E2 is possible for simple visual models (25–60 % captured in notebook 06 §4), so a small G is not a negative result about E2.
6. **Seasonal folds.** Contiguous folds extrapolate across seasons (bias −0.013, conservative). A confirmatory design spanning seasons needs season-blocked evaluation or within-season strata.
7. **Not yet simulated:** the ≤ 10-feature Exp 2a-A and frozen-encoder Exp 2a-B visual designs (D-021, D-022). Every validation used a single visual column.
8. **NEON licence** for redistributing derived tables is still to be confirmed. The camera's position relative to the probes is not documented in the downloaded files.
