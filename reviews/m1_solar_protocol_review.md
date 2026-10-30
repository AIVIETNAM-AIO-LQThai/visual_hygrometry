# Review 6: the CRT zero-information test passes fresh validation; intervals and the primary auditor do not

## Why this is a review checkpoint

Review 5 asked for escalation when the revised protocol passed fresh acceptance tests, or when another consequential limitation was demonstrated. Both have happened, for different parts of the protocol.
- The zero-information test with a conditional randomisation null passes on 15 fresh, independently seeded worlds, including the notebook 11 catastrophic null and persistence up to 0.97.
- The season-cluster interval and the context-only challenger fail their declared gates.

No NEON test or effect size has been computed with this protocol, and no CPER 2020–2022 imagery has been downloaded.

## Decisions requested

1. **Q0 on CPER.** May CPER plan step 3 (the hourly JPEGs) go ahead, with Q0 reported as exploratory under the CRT? It would carry the repair diagnostic and checks of the CRT sampler against the real images, but no validated primary auditor.
2. **Intervals.** With four seasons, should effect sizes stay descriptive (season-specific G, point estimate)? Or should a corrected procedure be developed and validated in a new suite, for example a variance-corrected resampled t or nested cross-validation?
3. **Primary auditor.** Should the challenger be redesigned (for example, length scales chosen by training-only CV), or should the repair diagnostic, which passed both sides, become primary? Review 5 restricted E[V | C] to a secondary role.
4. **CRT realism.** Which real-image checks must the sampler pass before any conditional-independence statement? Candidates: simulated against observed persistence, tails and cross-feature dependence of V given C, per season and per camera epoch.
5. **Scope.** Is continued NEON E2 work still justified against the field pilot, given that intervals are unavailable at four seasons?

## Changes since review 5 (required deliverables)

Decisions D-067 to D-074 are in [docs/decisions.md](../docs/decisions.md).
1. **Solar/diurnal context** ([notebook 14](../notebooks/14_solar_context_and_dependence_aware_inference.ipynb), `data.solar`, `worlds.add_context_levels`).
   - The candidates are L3 (clock time), L4 (+ regularised hour × season), S (+ solar-elevation spline, elevation × T, signed hour angle × declination, daylight-fraction Fourier) and S4 (S + L4).
   - The context is chosen per split by week-grouped inner CV on training rows.
   - The simulation machinery and the protocol are in `visual_hygrometry.suite`, so the validation ran exactly the developed code.
2. **Independently seeded synthetic validation** ([notebook 16](../notebooks/16_fresh_validation_solar_protocol.ipynb)). It has 15 worlds × 100 replicates, seeds 700 000+, a different solar climate from development, and gates, generator and thresholds declared before execution.
3. **Revised adequacy evaluation.** It measures false alarms on the chosen context and detection under a deliberately misspecified L1, for both a context-only challenger and the repair diagnostic.
4. **Statistical note** ([docs/m1_statistical_note.md](../docs/m1_statistical_note.md)). It covers E2, G and Q0, why G need not be ≤ E2 (E Δ = E2 − KL_VC + KL_C; former G8 withdrawn), generator validity conditions and interval targets.
5. **CPER 2020–2023 plan, frozen** ([docs/cper_2020_2023_plan.md](../docs/cper_2020_2023_plan.md)), with an incremental audit ([notebook 15](../notebooks/15_cper_2020_2023_acquisition_audit.ipynb)). Only tower tables and `.meta` files were downloaded.
6. **Field checklist, draft 3** ([docs/field_pilot_checklist.md](../docs/field_pilot_checklist.md)). It separates the engineering pilot, the extended research collection and reference instrumentation. Nothing was ordered.

## Development (notebook 14; 12 worlds × 40 replicates; not validation)

- **Context.** With the context forced, the season × hour null rejects at 0.975 (L1), 0.70 (L3), 0.175 (S), 0.075 (L4) and 0.05 (S4). Selected per split, it rejects at 0.025. The solar terms alone do not represent a season-dependent diurnal cycle.
- **Generator.**
  - The shift test rejects at 0.175 at persistence 0.95, and at 0.125 with season-specific vegetation and a camera change.
  - The CRT stays ≤ 0.075 everywhere, with power ≥ the shift test in every positive world. The CRT was chosen.
- **Thresholds** (frozen before validation).
  - Challenger τ = 0: any positive τ only reduces its already low detection, 0.55.
  - Repair diagnostic τ = 0.002 nats per row: false alarms fall from 0.275 to ≤ 0.075, and detection stays 1.0.
- **Expected failures.** Development already showed under-coverage of the season-cluster interval (0.70–0.90 in positives) and low challenger power. The gates were not loosened.

## Validation (notebook 16)

| gate | result | outcome |
|---|---|---|
| A1 CRT Type I ≤ 0.085 (10 nulls) | 0.02–0.08; season × hour 0.08, day-length amplitude 0.04, persistence 0.90 / 0.97 0.06 / 0.04, regimes 0.06, camera change 0.03 | pass |
| A2 power ≥ 0.80 (truth ≥ 0.03) | 0.99, 1.00, 0.83 (slow state), 1.00 | pass |
| A3 null mean ≤ +0.01; \|est − G_design\| ≤ 0.01 | nulls −0.024 to +0.001; positives ≤ 0.002 | pass |
| A4 season-cluster 95 % interval covers G_design ≥ 0.92 | 3 of 15 worlds pass; 0.78–0.91 in other nulls, 0.71–0.90 in positives | **fail** |
| A5 1 % deletion q90 ≤ 0.03 / 0.05 | ≤ 0.018 | pass |
| A6 challenger: false alarms ≤ 0.10, detection ≥ 0.80 | false alarms up to 0.19 (5 worlds > 0.10); detection 0.54 / 0.54 | **fail** |
| A7 repair diagnostic: false alarms ≤ 0.10, detection ≥ 0.80 | ≤ 0.05; 1.00 / 1.00 | pass |

**Ungated results.**
- The shift test rejects at 0.15 at persistence 0.90 and 0.97.
- In the shared-regime positive (truth 0.008), CRT power is 0.56 against the shift test's 0.29.
- In every positive world G_design is 0.003–0.007 below E2, and coverage of E2 is lower than coverage of G (0.61–0.83).
- In the day-length null, G_design is +0.0012 with E2 = 0. This is the context repair of the note's §2, and it is small.

## Caveats

- **The synthetic images are low-dimensional** (one or two features), with Gaussian or Markov-regime residuals. The CRT's validity on real images depends on its sampler describing their dependence and tails, and this suite cannot show that.
- **A1's largest rate is borderline.** 0.08 in the season × hour null has a one-sided 95 % upper bound of about 0.14 with 100 replicates.
- **Development and validation worlds belong to the same families.** Shapes, parameters and the solar climate differ, but the structures do not.
- **The A4 threshold differs from the note.** The statistical note asks for ≥ 0.93 coverage, while notebook 16's gate was 0.92. The outcome is identical under either threshold.
- **The HARV investigation is still outstanding.** The 2021 label fault and the 2022 radiation anomaly have not yet been examined, and HARV epochs stay separate.
- **Runtime.** Notebook 16 takes about 9 hours on 16 workers, mostly from the 39 CRT refits per replicate.

## Competing interpretations

- **The interval failure** could be:
  1. positive correlation between leave-one-season-out fold estimates (each pair shares two of three training seasons), so a t interval over four fold means is too narrow;
  2. a target mismatch, in which an in-sample cross-fit describes these seasons, while G_design averages over models fitted on other data.

  The bias is small (≤ 0.002), which favours (1), but neither has been tested.
- **The challenger failure** could be:
  1. fixed length scales that are too fine for the day-of-year axis (weather is memorised, giving false alarms) and too coarse for the hour × season interaction (missed detections);
  2. the limit of any context-only auditor at 4 × 92 days.

  The repair diagnostic succeeds because it targets the specific route (V predicted from C) by which inadequacy creates false discoveries.

## Recommendation

1. **GO for CPER plan step 3**, and run Q0 with the CRT as an exploratory result. Report it with the repair diagnostic, the forced-context sensitivity (L3 / L4 / S / S4) and sampler-fit checks on the real V given C. Make no confirmatory claim.
2. **Report effect sizes descriptively** (season-specific G and the point estimate). Develop a variance-corrected interval for leave-one-season-out on new development worlds, and accept it only after a fresh suite.
3. **Redesign the challenger** with training-only selection of its length scales, and keep the repair diagnostic as a validated secondary check. Do not promote E[V | C] without a decision from this review.
4. **Investigate HARV** (the 2021 label fault and the 2022 radiation anomaly) before any HARV imagery is used.

**Alternative.** Stop NEON E2 work at the Q0 level and move effort to the field pilot (draft 3). Four NEON summers will not give a valid interval with the present procedure, and the field design can include more seasons and reference instruments.

## Ready-to-send discussion prompt

> You reviewed this project five times (latest: MODIFY the statistical protocol; GO for incremental multi-year NEON exploration and field-pilot preparation; confirmatory Exp 2a blocked). The attached report covers the six required deliverables.
>
> The protocol now chooses its context per split, on training rows only, from four candidates: clock time; + hour × season; + solar terms (elevation, elevation × T, hour angle × declination, daylight fraction); and both. Q0 uses a conditional randomisation test: V* is the cross-fitted E[V | raw context, season] plus a simulated residual with day-level and within-day AR(1) per season. The shift test is reported beside it. A context-only challenger (random Fourier features of the raw context) and a repair diagnostic (the gain from a smooth train-only E[V | C]) are evaluated for false alarms and for detection under a misspecified context. Generator and thresholds were chosen on development worlds and frozen before validation.
>
> On 15 fresh worlds (100 independent replicates each, 4 seasons at CPER's location), 5 of 7 predeclared gates pass:
> - CRT Type I is 0.02–0.08 in ten nulls, including the former 0.787 season × hour null (0.08), persistence 0.97 and a camera change; the shift test reaches 0.15.
> - Power is 0.83–1.00; estimates track the design's G within 0.002; 1 % deletions move them by ≤ 0.018 nats.
> - The repair diagnostic has false alarms ≤ 0.05 and detection 1.00.
>
> Two gates fail:
> - The season-cluster 95 % interval covers G in only 3 of 15 worlds at ≥ 0.92 (0.71–0.91 elsewhere).
> - The challenger has false alarms up to 0.19 and detection 0.54.
>
> The CPER 2020–2023 plan is frozen; labels and camera state are audited; no imagery has been downloaded.
>
> Please challenge, specifically:
> 1. Is the CRT result enough to run Q0 on CPER 2020–2023 as an exploratory test, given that the sampler's fit to real multi-feature images is untested? Which sampler checks would you require?
> 2. With four seasons, should effect sizes stay descriptive? Or which interval would you accept for leave-one-season-out, and what is the likely cause of the under-coverage?
> 3. Should the challenger be redesigned, or may the repair diagnostic, which passed both sides, carry the adequacy evidence?
> 4. Is a 0.08 Type I rate in the season × hour null (upper bound ≈ 0.14) acceptable, or does that world need more replicates?
> 5. Should NEON E2 work continue past Q0, or should effort move to the field pilot?
>
> Do not assume the recommendations are correct. Give GO / MODIFY / STOP for (a) CPER imagery download and an exploratory Q0, (b) further interval and auditor development, and (c) the field pilot (draft 3).
