# Review 7: on real CPER images the CRT sampler fails its declared audit; no zero-information test was run

## Why this is a review checkpoint

M1.3 asked for escalation once the real-data diagnostics had established whether the conditional sampler is suitable for exploratory testing. They have. By the rule declared before the audit was run, it is **not suitable**: it under-simulates within-day persistence, and it reproduces neither the hour- and temperature-dependent residual scale nor the heavy tails of the real features. As declared, no zero-information p-value has been computed on the real labels. Per-season predictive gains are reported descriptively.

## Decisions requested

1. **Sampler.** Should the CRT sampler be corrected and re-validated? The candidate corrections are a bias-corrected within-day AR, an hour- and temperature-dependent scale, and heavy-tailed or resampled innovations, for example a bootstrap of standardised residual days within season. The re-validation would be synthetic first, then a re-audit on these features with the same criteria. Or should real-data Q0 be abandoned for NEON?
2. **The audit rule.** Was it right to make F1 (persistence) decisive alongside F5? F5 passed (0.026), but on 39 strongly dependent datasets. Or would you accept F5 with more, less dependent semi-synthetic nulls?
3. **Per-season gains.** Do the gains (+0.020, +0.022, −0.025, +0.073 nats/row) justify any further NEON E2 work, given that they are fragile to refitting, partly reproduced by auto-exposure alone, and concentrated in low-sun rows in 2023?
4. **Scope.** Should NEON E2 work stop at this descriptive level, with effort moving to the field pilot (draft 3), where acquisition state, illumination and reference humidity can be controlled?

## What was done (M1.3)

The plan deviations of 2026-11-01 were recorded in [docs/cper_2020_2023_plan.md](../docs/cper_2020_2023_plan.md) §9 before the analyses they govern. Decisions D-075 to D-079 are in [docs/decisions.md](../docs/decisions.md).
1. **Verification** ([notebook 17](../notebooks/17_cper_image_verification_and_sampler_audit.ipynb) §1–6).
   - All 3,792 hourly 2020–2022 JPEGs decode, with a SHA-256 manifest and no duplicates. The 2023 hashes are unchanged.
   - Configuration and camera unit are identical in all four years, with no view shift.
   - The clock was read from the burned-in overlay on every frame by a pixel-font reader validated on 2023 frames (99.88 % frame accuracy, held out). Every readable frame agrees within 1 s, except one at 6 s and one confident misread, which excluded its day.
   - The exposure–clear-sky-index correlation peaks at lag 0 in every year.
   - Usable rows: 1,225 / 1,166 / 1,220 / 1,206.
   - The recomputed 2023 features equal notebook 09's exactly.
2. **Sampler audit** (notebook 17 §7; criteria declared in the notebook before execution). The audit compares 200 sampler draws with the observed residuals of the nine features, per season, and adds 39 semi-synthetic real-image nulls plus a positive control.
3. **Per-season gains** ([notebook 18](../notebooks/18_cper_per_season_predictive_gains.ipynb)). This is the notebook 16 protocol without tests: no p-value and no interval.

## Sampler audit

| family | share of cells outside the 95 % band of the draws | outcome | main discrepancy |
|---|---|---|---|
| F1 persistence | 0.37 | **fail** | within-day lag-1 outside in 36 of 36 cells (observed 0.22, simulated 0.09); day-level lag 1 inside everywhere; lag 7 outside in 4 of 36 |
| F2 cross-feature | 0.00 | pass | |
| F3 conditional variation | 0.80 | fail | residual SD 1.4× higher after 14 h than before 10 h; temperature-dependent scale |
| F4 shape and tails | 0.88 | fail | excess kurtosis median 3.8 (up to 25), skew, 1.5 % beyond 3 SD (simulated 0.2 %) |
| F5 real-image null (CRT rejection ≤ 0.10) | 0.026 (1 of 39) | pass | the shift test rejects 0.077 |

- **Mechanism of the F1 failure.** The sampler estimates the within-day AR(1) from deviations from each day's mean, over about 13 rows, without a small-sample correction. It then simulates with that downward-biased value, so the simulated within-day dependence is too weak. The day-level AR does have Kendall's correction.
- **The synthetic suite missed it.** Notebook 16 never compared simulated with observed within-day statistics, and its synthetic residuals were Gaussian and homoscedastic.
- **Positive control.** An injected visual component of about 0.03 nats (Gaussian approximation) was detected in 0.28 of datasets by the CRT and 0.44 by the shift test. The mean estimated contrast rose by only 0.005 nats, so power on real images is low.

## Per-season gains (descriptive; nats/row, held out by year)

| | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|
| primary (context chosen: S, S, S, S4) | +0.020 | +0.022 | −0.025 | +0.073 |
| context forced to L3 / L4 / S / S4 | within 0.004 | within 0.004 | within 0.004 | within 0.004 |
| label D_probe | +0.018 | +0.019 | −0.022 | +0.073 |
| 20 rows with RH_implied ≥ 98.3 % removed, refit | +0.013 | +0.003 | −0.056 | +0.071 |
| same rows, frozen deletion | +0.020 | +0.022 | −0.026 | +0.071 |
| acquisition-only control (log exposure) | −0.004 | +0.012 | +0.011 | +0.017 |
| E2, solar elevation > 10° | +0.022 | +0.020 | −0.021 | +0.030 |
| E2_illum (K in C), same rows | +0.026 | +0.019 | −0.018 | +0.056 |

- The repair diagnostic does not flag (lower bound −0.024).
- The 2023 chronological gain (+0.073) is the same split as the held-out 2023 fold, and 2023 informed the method.

## Caveats

- The audit's 95 % bands come from the sampler fitted to the same data, so the lag-1 statistics are partly matched by construction. Lag 7 and the shape statistics are the informative parts.
- The 39 semi-synthetic nulls share V and recombine the same four years of label residuals, so they are far from independent. Their rejection rate cannot show nominal Type I.
- The semi-synthetic nulls assume that seasons are independent. Year-to-year coupling (for example a drought year) would leave some dependence between the label residuals of one year and the images of another.
- The positive control's "≈ 0.03 nats" is a Gaussian approximation and is not the true information.
- The overlay reader made one confident misread among about 3,700 readable 2020–2022 frames. Its error rate is therefore not zero, although every other reading agreed with the file-name time.
- All gains are for processed, auto-exposed RGB at one grassland site and four summers.

## Competing interpretations of the gains

- **Visual information about D beyond C.** Gains in three of four seasons, robust to the context choice and the label, with no repair flag.
- **An acquisition or illumination pathway.** Auto-exposure alone gains in three seasons. The 2023 gain sits largely in low-sun rows, where illumination geometry dominates the image.
- **Instability and between-season heterogeneity.** The sign differs in 2022 (a year with different phenology), and refits after removing 20 rows move season gains by up to 0.03 nats.

These cannot be separated without a valid null and a valid interval.

## Recommendation

1. **MODIFY the sampler before any real-data Q0.** Correct the within-day AR bias; model the scale by hour and temperature; replace Gaussian innovations by resampled standardised residuals within season. Validate on the notebook 16 worlds plus new heteroscedastic and heavy-tailed worlds, then re-audit on these features under the same declared rule. Use more, and less dependent, semi-synthetic nulls, for example nulls that also resample whole days.
2. **Keep NEON results descriptive.** Add no further NEON year until (1) passes. 2024–2025 stay reserved.
3. **Prioritise the field pilot** (draft 3) in parallel. Exposure and illumination are confounded with the image features at CPER, and a fixed-exposure camera with reference humidity removes that pathway by design.

**Alternative.** Stop real-data Q0 on NEON: report notebook 18 as the final NEON result, and move to the field pilot.

## Ready-to-send discussion prompt

> You reviewed this project six times (latest: run the CRT zero-information test on CPER 2020–2023 as exploratory only, after checking its sampler on the real images). The attached report covers M1.3.
>
> **Verification.** All 3,792 hourly 2020–2022 JPEGs were verified: hashes, decoding, one camera unit and configuration, no view shift. The clock was read from the burned-in overlay by a pixel-font reader validated on 2023 frames (99.88 %); every readable frame agrees within 1 s, apart from one confident misread whose day was excluded.
>
> **Sampler audit.** Declared before execution: the sampler is suitable if persistence (F1) and a semi-synthetic real-image null (F5) pass. F1 fails. Within-day lag-1 is under-simulated in 36 of 36 feature × season cells (0.22 observed, 0.09 simulated), because the within-day AR is estimated from day-demeaned residuals without correction. F3 (hour- and temperature-dependent scale) and F4 (excess kurtosis 3.8) fail too. F5 passes: 1 of 39 dependent semi-synthetic nulls rejects. An injected ≈ 0.03-nat signal is detected in only 0.28. No Q0 p-value was computed on the real labels.
>
> **Per-season gains** (descriptive): +0.020, +0.022, −0.025, +0.073 nats/row for 2020–2023.
> - They are robust to the context choice and the label, with no repair flag.
> - They are fragile to refitting: removing 20 near-saturated rows moves 2022 by −0.030.
> - Auto-exposure alone gains up to +0.017.
> - 2023's gain is concentrated in low-sun rows.
>
> Please challenge, specifically:
> 1. Was making F1 decisive correct, when F5 passed? Would you accept a corrected sampler (bias-corrected within-day AR, hour- and temperature-dependent scale, resampled innovations) after synthetic validation and a re-audit, or is real-data Q0 at NEON not worth pursuing?
> 2. How should the semi-synthetic real-image null be made informative: more and less dependent datasets, whole-day resampling?
> 3. Do the per-season gains, given their fragility, the exposure-only control and the low-sun concentration, justify further NEON E2 work?
> 4. Should effort now move to the field pilot?
>
> Do not assume the recommendations are correct. Give GO / MODIFY / STOP for (a) correcting and re-validating the sampler, (b) further NEON E2 analysis, and (c) the field pilot.
