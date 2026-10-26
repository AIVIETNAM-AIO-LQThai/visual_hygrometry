# Review 3: revised inference protocol passes validation; NEON exposes label problems

## Why this is a review checkpoint

Review 2 asked for escalation when either the revised inference/estimation protocol passed its acceptance tests or real NEON data exposed a consequential scientific discrepancy. Both have happened.
- **Protocol:** all six pre-declared criteria pass on fresh synthetic worlds.
- **NEON (HARV, July 2023):** two label problems and one camera problem bear directly on what E2 can mean at NEON sites.

## Decisions requested

1. Accept the M1 exploratory protocol:
   - **Q0:** cyclic-shift refitting permutation test, contiguous purged folds, strata at declared breaks;
   - **G:** chronological hold-out with week-cluster t intervals;
   - **validity region:** ρ ≤ 0.6.

   Or modify it.
2. **NEON label definition:**
   - probe-temperature D, which carries a sunshine-correlated heating error; or
   - hybrid D (aspirated T with the probe's dew point), whose label and conditioning temperature share one unit; or
   - both, one primary and one sensitivity.
3. **Near-saturation handling** for a probe that never reports above 99 % RH.
4. Whether NEON PhenoCam imagery (in-camera haze compensation, AGC, JPEG) can serve for any E2 analysis beyond pipeline feasibility, and which claims it excludes.

## Changes since review 2

- **Train-only projection (the transductivity review 2 identified).** The visual projection is fitted per outer split on training days only (`inference.project_splits`, unit-tested by corrupting test-row visuals). The permutation null generator uses analysis-sample (C, V), never D, and is declared as such.
- **Permutation generator:**
  - nearest-slot donors (incomplete grids);
  - strata;
  - multi-day units;
  - an enumerated cyclic-shift null that preserves serial dependence.
- **Synthetic worlds** gain multi-day persistence.
- **Chronological hold-out** for G: fit on 60 % of days, purge 2, evaluate the rest. The target is the frozen models' gain on 300 future days.
- **No nested or repeated CV variance formulas** were implemented, per review 2. The estimand of each procedure is stated in `docs/m0_review2_addendum.md`.

## Synthetic evidence (notebook 06)

Development (100 replicates, seeds 8000+):

| stress (null) | day-unit permutation Type I |
|---|---|
| none / heteroscedastic V / missing frames | 0.07 / 0.07 / 0.05 |
| camera break unstratified / stratified | 0.09 / 0.07 |
| season with day-of-year context, unstratified / stratified | 0.07 / 0.06 |
| persistence ρ = 0 / 0.3 / 0.6 / 0.85 | 0.07 / 0.07 / **0.18 / 0.38** |
| same, cyclic shift (≥ 7 days, 16-day contiguous folds, 3-day purge) | 0.05 / 0.06 / 0.06 / 0.10 |
| same, cyclic shift with a 7-day purge | 0.04 / 0.06 / 0.07 / 0.13 |

Chronological G interval coverage for ρ = 0 / 0.3 / 0.6 / 0.85:

| interval | coverage |
|---|---|
| week clusters | 0.94 / 0.93 / 0.96 / 0.85 |
| day clusters | 0.92 / 0.93 / 0.84 / 0.51 |
| Newey–West | 0.90 / 0.90 / 0.86 / 0.59 |

**Sensitivity:**
- **Support restriction** removes 0.2 / 1.0 / 8.8 % of rows at q = 0.1 / 0.5 / 2.5 %. It halves a cold-tail E2 at q = 2.5 % (0.023 → 0.012), and costs 9 % at the adopted 0.5 %.
- **Simple visual models** capture only 25–60 % of E2 when information varies with T.
- **Robust-mixture settings** (ε 0.5–2 %, scale 2–8σ) change nothing beyond the 4th decimal once support is restricted.

**Fresh validation** (seeds 130 000+, 150 replicates, worlds new in sampling, dependence, break, season, missing pattern and mixed cue; criteria declared first):

| id | criterion | result |
|---|---|---|
| V1 | cyclic-shift Type I ≤ 0.085 in six nulls | 0.060, 0.033, 0.060 (ρ = 0.3), 0.047 (stratified break), 0.067 (season), 0.053 (missing) — pass |
| V2 | power ≥ 0.80 at 0.05 nats | 0.993 (plain), 1.000 (mixed hinge cue) — pass |
| V3 | week-cluster interval covers G ≥ 0.90 | 0.913–0.960 — pass |
| V4 | \|chronological − G\| ≤ 0.005 | ≤ 0.002 — pass |
| V5 | \|cross-fit − E2\| ≤ 0.01, plain cues | −0.001 — pass |
| V6 | off-support share ≤ 0.05 | ≤ 0.023 — pass |
| — | ρ = 0.6 edge world | shift 0.047; day units 0.147 |

## NEON evidence (notebook 07; HARV, tower top, July 2023)

- **Verified:**
  - **Clock:** frame filename time (UTC−5) equals the burned-in UTC stamp to 0 s in 1082 / 1082 frames; capture lands 4–7 s into the 1-min record.
  - **Join and completeness:** 842 usable daylit frames in the month; 96.5 % of minutes carry a usable label plus the aspirated temperature.
  - **Label formula:** the Magnus dew point matches NEON's to +0.046 K.
  - **Geometry:** probes 6.5 m apart on the tower top.
- **Probe radiation error.** HMP155 minus aspirated PRT is +0.06 K at night and +0.55 K by day, with median +0.82 K and 95th percentile +2.0 K above 900 W m⁻² (slope +0.077 K per 100 W m⁻²). The probe-T label D inherits this exactly (heated probe: correct dew point, D too high by the heating), correlated with sunshine (r = +0.42). The shield type is not documented in the readme. In 0.3 % of minutes the aspirated T is below the probe dew point (min −0.88 K).
- **Near-saturation plateau.** RH ≥ 97 % in 13 % of minutes, never above 99.02 %, while frames show ridge fog (10 July 05:30) and valley fog (24 July 19:30). NEON's per-minute uncertainty (σ_RH ≈ 1.14 %) makes the instrument-derived censor rule fire on 5 minutes; the 90–100 % specification (σ = 1.7 %) would censor 3.3 %.
- **Camera:**
  - **Overlay leakage:** every frame burns in UTC time, camera temperature (r = +0.90 with air T) and exposure (r = −0.64 with SW). A fixed mask covers 3.1 % of the frame.
  - **In-camera processing:** `auto_haze=1`, auto-exposure and AGC are on throughout, and only JPEG is available.
- **Persistence:** daytime daily-mean D lag-1 autocorrelation +0.03 (one month).

## Caveats

- All validation is synthetic, with a single visual column per world. The ≤ 10-feature (Exp 2a-A) and frozen-encoder (Exp 2a-B) designs are not yet simulated.
- Validity holds for ρ ≤ 0.6 only. Seasonal contiguous folds give a −0.013 bias (conservative). The shift-test p-value resolution is 1/(G − 13).
- The test's exchangeability assumption (stationary residual series within strata) is argued, not testable from one record.
- One NEON site-month. The HMP155 shield type is inferred from behaviour, not documented. The camera's position relative to the probes is not in the files.

## Competing interpretations

- **The day-time warm bias** could be:
  1. radiative heating of a passively ventilated HMP155 shield;
  2. a spatial temperature difference between two points 6.5 m apart on the tower (canopy-top heterogeneity);
  3. an aspirated-PRT cold bias.

  Its rise with SW, and its near-zero value at night, favour (1); (2) is not excluded.
- **The 99 % plateau** could be sensor saturation or wetting during fog/dew, a NEON processing cap, or a genuine absence of RH > 99 % at 38 m height while fog sits lower (the valley fog in the 24 July frame is below the tower).

## Recommendation

1. **Accept the M1 protocol** for exploratory work.
2. **Label:** use the hybrid D (aspirated T, probe dew point) as primary at NEON and the probe-T D as sensitivity. Report both.
3. **Censoring:** censor at the HMP155 90–100 % specification (RH ≥ 98.3 %). Treat fog/dew analyses as out of scope at NEON until an independent saturation indicator exists.
4. **Camera:** restrict NEON image analyses to pipeline and overall-E2 feasibility, explicitly excluding extinction-mechanism claims.

**Next:** extend to 3 summer months at HARV and one contrasting site (a dry site such as CPER or ONAQ) to estimate persistence and the radiation bias across conditions, before the first exploratory G and Q0 runs with masked, ≤ 10 predefined features.

**Alternative.** Use the probe-T label as primary. This keeps exact D ↔ RH invariance with independent label and conditioning units, at the cost of adding a radiation-error-sensitivity analysis that uses the measured HMP155 − PRT difference as a nuisance covariate in the context.

## Ready-to-send discussion prompt

> You reviewed this project twice (second decision: GO for NEON feasibility, MODIFY for confirmatory Exp 2a). The attached report covers the follow-up. The visual projection is now fitted on training folds only. The permutation null was tested against heteroscedastic visual noise, multi-day persistence, regime breaks, seasons and incomplete grids. Day-unit permutation failed under persistence (Type I 0.18 at ρ = 0.6, 0.38 at ρ = 0.85); a cyclic-shift null with contiguous purged folds held 0.05–0.06 up to ρ = 0.6. The adopted protocol (cyclic-shift Q0; chronological hold-out with week-cluster intervals for the operational gain G) passed all six pre-declared criteria on fresh synthetic worlds. A NEON feasibility audit (HARV, July 2023) verified the camera–sensor clock to 0 s. It also found that the HMP155 label probe reads +0.55 K warmer than the aspirated thermometer by day (up to +2 K at high sun), that RH never exceeds 99.02 % although fog is visible, and that the cameras run in-camera haze compensation.
>
> Please challenge, specifically:
> 1. Is the cyclic-shift null defensible as the default zero-information test? What failure modes of the shift construction (non-stationarity, wrap-around, few effective units) could the synthetic suite be missing?
> 2. Is "G = held-out gain of models fitted on the first 60 % of days, with week-cluster intervals" an adequate operational estimand for M1, and what should be reported beside it so it is not read as E2?
> 3. For NEON labels: probe-temperature D (sunshine-correlated error, independent conditioning unit) vs hybrid D (aspirated T with probe dew point; shared unit, approximate D ↔ RH invariance). Which should be primary, and what sensitivity analysis would you require?
> 4. How should the RH plateau below 99 % be handled: censoring threshold, exclusion of fog/dew regimes, or an independent saturation indicator?
> 5. Given auto-haze, AGC and JPEG, which visual claims are impossible with NEON PhenoCam imagery, and is it still worth using NEON for exploratory E2 before an own field pilot?
>
> Do not assume the recommendations are correct. Give GO / MODIFY / STOP for (a) exploratory M1 analyses on NEON with the adopted protocol and (b) designing the own-field pilot around these findings.
