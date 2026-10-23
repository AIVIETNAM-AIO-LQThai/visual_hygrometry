# M0 review: conditional-information estimator, sensor coupling and first public source

## Why this is a review checkpoint

The estimator is the instrument that will decide GO / MODIFY / STOP after Exp 2a. Synthetic validation passed the bias and false-positive criteria, but failed the interval-coverage criterion and exposed two failure modes (regime mixtures, high-dimensional visual inputs) whose fixes trade bias against variance. It also showed quantitatively that a visually predictable thermometer error can manufacture an E2 signal of the size of the planned threshold. Each of these changes what a future positive or null result would mean, so they meet the escalation rule (estimator validity, unresolved discrepancy, design commitments for data collection).

## Decisions requested

1. **Predictive family** for Exp 1/2a contrasts on real `D`: Gaussian (efficient, biased under regime mixtures), location-scale with a KDE residual density (robust to unexplained mixtures, ~30 % more SD), or another family (binned/ordinal categorical, mixture density, conditional quantiles → CRPS-based contrast).
2. **Inference procedure**: keep the percentile day-block bootstrap with a documented correction, replace it (nested/repeated CV variance, corrected resampled t, simulation-calibrated intervals), or separate a one-sided GO test from an estimation interval.
3. **Sensor configuration rule**: is "distinct, both aspirated units for label and conditioning T" a hard requirement for any E2 claim, and is NEON's tower-top HMP155 (label) + triple-aspirated PRT (conditioning) acceptable as a public dry run?
4. **Dimension budget**: should Exp 2a be restricted to a small, pre-specified set of visual features (region contrast/colour statistics) before any learned embedding is allowed?

## Hypotheses tested (synthetic only)

- H1: with matched, well-specified models the held-out log-score contrast recovers `I(D; V | C)` with small bias, and its interval covers the truth at the nominal rate.
- H2: the identity `E Δ̂ = I(D;V|C) − E KL(p‖q_VC) + E KL(p‖q_C)` predicts the sign of every failure: under-fitted context inflates, over-fitted or miscalibrated joint deflates.
- H3: E1 and E2 are not ordered; conditioning on T can remove (thermometer) or create (synergy) visual information.
- H4: label noise independent of `V` attenuates the observation-level contrast (data processing); noise correlated with `V` can create it.

## Methods

- **Estimand.** `E2 = I(D; V | hour, T)` (season constant in the synthetic world), nats per sample. `D = T − Td`.
- **Estimator.** `Δ̂ = mean_i[log q_VC(d_i|v_i,c_i) − log q_C(d_i|c_i)]` on held-out rows. Matched pair: identical context columns (4-term Fourier basis of local hour + T), the joint model adds visual columns only; inputs pass a role/lineage policy before reaching either model. Default family: Gaussian, ridge mean with penalty chosen by day-grouped inner CV, homoscedastic SD from grouped inner out-of-fold residuals. Variants: log-link variance model of squared OOF residuals; location-scale model with a Gaussian KDE density of standardised OOF residuals.
- **Splits.** 5 outer folds of whole days (interleaved). Purging of dependency intervals implemented and tested; not needed in these worlds (no history features).
- **Interval.** Percentile bootstrap over days (2 000 or 1 000 draws), conditional on the fitted models.
- **Synthetic worlds.** Linear-Gaussian SEM conditional on hour, 48 daylight samples/day (15 min), noise split into a day-level share and a within-day AR(1) part (lag-1 autocorrelation 0.93; 69 % of the moisture residual's variance between days). T: diurnal mean 20 ± 5 °C, anomaly SD 3 K (70 % day-level). `D = mean(h) + 0.4·T + r`, `r` SD 2 K. Visual cue `vis_moist = γ r + noise`; γ = 0.162 gives E2 = 0.0499 nats. Exact CMI from the covariance (Schur complements); a non-Gaussian regime world uses quadrature.
- **Code.** `src/visual_hygrometry/{scoring,synthetic,policy,splits,data,thermo}.py`; notebooks `00_thermodynamics_and_synthetic_data.ipynb`, `01_information_estimator.ipynb` (executed, outputs in the files); 64 pytest tests passing.

## Results

### Controls and sweep (60 days)

| case | truth | estimate | note |
|---|---|---|---|
| sun-elevation cue (function of hour) | 0 | 0.0001 [−0.0006, 0.0007] | one sample |
| visual thermometer under E2 | 0 | −0.0002 [−0.0017, 0.0012] | one sample |
| γ sweep, 7 points 0–0.54 nats | — | slope 1.053, intercept −0.009 | one sample per point |
| thermometer, E1 / E2 | 0.119 / 0 | 0.110 ± 0.014 / 0.000 | mean ± SE, 10 samples |
| dew-point (vapour) cue, E1 / E2 | 0.039 / 0.805 | 0.039 ± 0.009 / 0.822 ± 0.024 | 10 samples; E2 ≫ E1 |

### Repeated sampling (100 replicates per cell; Gaussian default unless stated)

| truth | days | bias | SD of estimate | bootstrap SE | coverage (day blocks) | coverage (rows) | P(lower bound > 0) |
|---|---|---|---|---|---|---|---|
| 0 | 20 | −0.0087 | 0.0167 | 0.0125 | 0.74 | 0.25 | 0.02 |
| 0 | 60 | −0.0026 | 0.0045 | 0.0038 | 0.78 | 0.22 | 0.00 |
| 0 | 180 | −0.0007 | 0.0014 | 0.0013 | 0.79 | 0.38 | 0.00 |
| 0.05 | 20 | −0.0087 | 0.0389 | 0.0307 | 0.75 | 0.37 | 0.25 |
| 0.05 | 60 | −0.0007 | 0.0214 | 0.0186 | 0.84 | 0.42 | 0.80 |
| 0.05 | 180 | +0.0011 | 0.0116 | 0.0112 | 0.94 | 0.46 | 1.00 |
| 0 (location-scale KDE) | 60 | −0.0060 | 0.0102 | 0.0071 | 0.74 | 0.35 | 0.01 |
| 0.05 (location-scale KDE) | 60 | −0.0015 | 0.0276 | 0.0228 | 0.84 | 0.42 | 0.66 |

80 %-power detectable effect (2.8 × SD): 0.11 / 0.06 / 0.033 nats at 20 / 60 / 180 days (Gaussian).

### Failure modes

| mode | configuration | truth | estimate |
|---|---|---|---|
| A under-fitted context (linear hour) | sun cue, 10 samples | 0 | 0.0168 ± 0.0025 (6.6 SE); Fourier context −0.0002 |
| B over-dimensioned joint, 30 days, 200 noise features + cue (5 samples) | OLS, in-sample SD | 0.0499 | −0.120 (joint 90 % coverage 0.79) |
| | OLS, OOF SD | | −0.041 (coverage 0.89) |
| | ridge, row-LOO tuned / day-grouped tuned | | −0.028 / −0.026 |
| | cue only (1 dimension) | | 0.042 |
| C variance-only information (regime SD 0.7 vs 2.5 K), one 120-day sample | Gaussian homoscedastic | 0.227 | −0.002 |
| | Gaussian, log-link variance | | 0.291 (decomposition predicts 0.328 = truth + KL(mixture‖best Gaussian) 0.100) |
| | location-scale + KDE residual | | 0.199 [0.147, 0.252] |
| | *(first run)* `log r²` variance regression | | 0.437, rejected: geometric-mean variance under unexplained heteroscedasticity |
| D visually predictable radiation error (10 × 120 days), atmospheric truth 0 | shared unit, error SD 1 / 2 K | 0.035 / 0.097 (measured) | 0.031 ± 0.005 / 0.096 ± 0.008 |
| | aspirated label, biased conditioning unit, 1 / 2 K | 0.016 / 0.046 | 0.014 ± 0.003 / 0.042 ± 0.005 |
| label noise ν ⊥ V, SD 0 / 0.6 / 1.2 / 2.0 K | observation-level | 0.199 / 0.180 / 0.138 / 0.090 | 0.193 / 0.173 / 0.131 / 0.082; Gaussian deconvolution with known σ_ν 0.192–0.196; with σ_ν misstated ×1.5 → 0.49 / −0.30 |

Analytic version of D: with `d = βt + r`, a probe error `e` that the image reveals and `v_e = σ_e²σ_t²/(σ_t²+σ_e²)`, spurious E2 = ½ log(1 + (1−β)² v_e/σ_r²) for a shared unit and ½ log(1 + β² v_e/σ_r²) for an aspirated label with a biased conditioning unit.

### Pre-declared checks

Tolerances were set after a 60-replicate pilot of one positive case (so not blind). First run: T1 pass, T2 pass, T3 fail, T4a fail (single-sample lower bound −0.0001), T4b fix fail, T4c fix fail, T4d pass. Revisions after the first run (marked post hoc): day-grouped tuning, log-link variance, location-scale KDE family, replicated failure-mode estimates. Second run: T1 pass, T2 pass, **T3 fail** (0.78 null / 0.84 positive at 60 days; 0.79 / 0.94 at 180), T4a* pass, **T4b* ridge fix fail** (−0.076), T4b* dimension budget pass (−0.008), **T4c* KDE fix fail** (−0.029 > 0.02, single sample, CI covers truth), T4d pass.

### Thermodynamic and policy results that feed the decisions

- Given the label unit's own T, `D` and RH are bijective (`ln(RH/100) = −BCD/((C+T)(C+T−D))`, Magnus), so E2 is target-invariant; with an independent conditioning thermometer this holds only approximately.
- Label SNR near saturation `D/σ_D ≈ (100 − RH)/σ_RH`; with ±2 %RH, rows above ~98 %RH are censored by an instrument-derived rule.
- Leakage policy: closed-world registration, roles, lineage, shared-sensor flag, training-only phase and a correlation-ratio audit; a label canary is refused under every deployment setting, including when it is mis-declared as a visual feature.

### Public source (stage 1, metadata only)

NEON: the HMP155 RH/T probe (DP1.00098.001), a triple fan-aspirated PRT (DP1.00003.001) and the phenology camera (DP1.00033.001; RGB every 15 min) sit at the top of the same tower at 47 terrestrial sites, with a median of 116 months where all three are available (5 260 site-months). All 47 cameras resolve in the PhenoCam API (40 north-facing; PhenoCam archive CC BY 4.0). The NEON data-file endpoint returned HTTP 403 to unauthenticated requests on 2026-10-23 (UTC); stage 2 (join quality) awaits an API token. The HMP155 shield type (aspirated or passive) is not yet verified.

## Caveats

- All estimator results are synthetic. The worlds are linear-Gaussian apart from one regime case; real `D` is skewed, bounded below, censored near saturation and probably regime-mixed.
- Dependence parameters (day-level shares, AR coefficients) drive power and coverage numbers; they are assumptions until measured on real data.
- Several failure-mode results rest on one sample (regime case, label-noise table). Replicated estimates exist for A, B, D and the E1/E2 table.
- The bootstrap interval does not resample the model-fitting step.

## Competing interpretations

- T3: (a) small-cluster bias of the percentile bootstrap; (b) correlation of cross-validated scores across folds (variance of K-fold estimates has no unbiased estimator, Bengio & Grandvalet 2004); (c) the null is a boundary case where `Δ̂` is a non-normal, negatively biased statistic and no symmetric interval is calibrated. In the pilot, a bootstrap of the *oracle* score difference (true models, no fitting, no cross-fitting) already underestimated the SD by ~16 % at 60 days (0.0179 vs 0.0212, the latter itself ±9 % from 60 replicates). That points to (a), few and heavy-tailed day clusters, as a main cause on the positive side; (b) is not needed to explain it but is not excluded. (c) explains the null side.
- Mode C: the KDE family's residual bias (−0.029) could be single-sample noise, KDE smoothing of the narrow regime component, or the variance model's imperfect regime separation.
- Mode D: a positive E2 on real data with a passive-shield label could be genuine moisture signal, radiation-error leakage, or both; sensor configuration, not the estimator, distinguishes them.

## Unresolved

Family choice; interval method; whether to require the conditioning thermometer to be the label unit's own T (exact target invariance, but common-mode error) or an independent aspirated one (independent errors, approximate invariance); the practical threshold; Tobit fitting for censored labels; a conditional permutation test for E2.

## Recommended next step

Keep the Gaussian family as the efficient primary estimator **with mandatory diagnostics** (context-residual structure, PIT, residual mixture tests) and the location-scale KDE contrast as a pre-declared robustness estimate. Replace the GO criterion "CI lower bound > threshold" by a one-sided test calibrated by simulation from a world fitted to the real context model and dependence structure (parametric bootstrap), and report the estimation interval separately. Require ≥ 120 independent days for confirmatory claims. Restrict Exp 2a to ≤ ~10 pre-specified visual features. Obtain a NEON token and run stage 2 at one site, checking the HMP155–PRT temperature difference against shortwave radiation before any E2 estimate.

**Alternative.** Adopt a binned (ordinal-categorical) predictive family with shared bins for both models. Bin widths cancel in the contrast, censoring maps onto the lowest bin, and mixtures and heteroscedasticity are represented without a variance model. Estimate the intervals with nested cross-validation (Bates, Hastie & Tibshirani, JASA 2024) instead of simulation calibration. This costs more parameters per visual feature, so it would need more days.

## Ready-to-send discussion prompt

> You are reviewing a research method, not code style. A project asks whether passive RGB images of a fixed outdoor scene carry information about near-surface moisture beyond clock, season and independently measured air temperature. The primary estimand is E2 = I(D; V | hour, season, T), with D the dew-point depression, estimated as the held-out log-score difference between matched probabilistic models q(D|V,C) and q(D|C) fitted by day-blocked cross-fitting. The attached report gives the synthetic validation: exact-CMI linear-Gaussian worlds with day-level dependence, a regime-mixture world, label-noise and radiation-error worlds, 100-replicate coverage and power studies, and the first-run failures and post-hoc revisions.
>
> Please challenge, specifically:
> 1. Is `E Δ̂ = I − E KL(p‖q_VC) + E KL(p‖q_C)` being used correctly, and is it sufficient to argue that a positive contrast with a residual-diagnosed context model is evidence of visual information? What loopholes remain (e.g. capacity asymmetry hidden by regularisation, distribution shift between folds)?
> 2. Interval failure (coverage 0.84 at 60 days for a 0.05-nat effect; null-side coverage ≈ 0.78 at all n, but 0–2 % false positives): which of the proposed fixes (simulation-calibrated one-sided test, nested CV, corrected resampled t, more days) is statistically sound here, and is a percentile bootstrap acceptable at all?
> 3. Predictive family: Gaussian vs location-scale KDE vs binned categorical for a skewed, censored, regime-mixed D. Which minimises the risk of a false GO and of a false STOP, given that the context model's misspecification inflates the contrast?
> 4. Sensor coupling: given the analytic spurious-E2 formulas for shared and partly aspirated sensors, what configuration is required before any E2 > 0 can be read as moisture? Is conditioning on the label unit's own temperature (exact D↔RH invariance, coupled errors) or on an independent aspirated thermometer (independent errors, approximate invariance) the right primary choice?
> 5. Is NEON (HMP155 label, triple-aspirated PRT, PhenoCam RGB at the same tower top, JPEG, auto-exposure) a sound public dry run for the pipeline, and what would make its results misleading?
>
> Do not assume the proposed recommendations are correct. For each point say what you would change, what evidence would settle it, and give an overall GO / MODIFY / STOP for proceeding from M0 to M1 with this estimator.
