# Review 5: the projection-free protocol fails its new validation gates; the failures are specific

## Why this is a review checkpoint

Review 4 asked for escalation when the revised inference protocol passed its new validation gates, or when a genuinely consequential measurement or statistical issue appeared. The second has happened. The protocol fails four of nine gates declared before the validation run, and the main failure is a realistic structure (a diurnal cycle that changes over the season) that produces false discoveries at a rate of 0.79. No NEON analysis has been run with the new protocol.

## Decisions requested

1. **Context for the diurnal cycle.** An hour × season level (L4), or a solar-time hour basis from solar geometry, or both? And which development worlds must the next fresh suite contain?
2. **Effect-size intervals under persistent information.** Should the interval stay open and only Q0 plus the point estimate be reported, as with D-033? Or should more seasons per site be required, with season-level replication? What else would you accept?
3. **Adequacy diagnostic.** Should the training-only E[V | C] projection return, as a *diagnostic* of context repair only? Or should the auditor be made stronger than the audited context?
4. **Persistence.** At AR 0.9 the shift test rejects at 0.100. Is CPER (ρ ≈ 0.95) out of scope for Q0 until longer records exist, or should regime-level strata be developed?
5. **Multi-year NEON.** Should the incremental extension start with CPER 2020–2023 (four homogeneous seasons) once a protocol passes, with HARV split into camera epochs?

## Changes since review 4 (required outputs)

The full account is in [docs/m1_inference_redesign.md](../docs/m1_inference_redesign.md); decisions D-054 to D-066.
- **Redesigned contrast** ([notebook 11](../notebooks/11_projection_free_inference.ipynb)):
  - no visual-derived context;
  - nested fixed context levels with training-only, week-grouped capacity selection;
  - day of year clamped to each split's training range, and V clipped to its training range;
  - a shift-test generator that projects linearly on the label-free richest context basis.
- **Estimands:** E2 is primary and E2_illum (clear-sky index in C) secondary, with acquisition-only controls under both. Slow and fast visual decompositions are declared future estimands.
- **Reproducible diagnostics of the notebook 10 failure** ([notebook 12](../notebooks/12_declared_analysis_failure_diagnostics.ipynb)). Notebook 10 itself is unchanged.
- **Multi-year NEON availability audit** ([notebook 13](../notebooks/13_neon_multiyear_availability_audit.ipynb)). No bulk download was made.
- **Field-pilot checklist** tiered into minimum / recommended / reference ([docs/field_pilot_checklist.md](../docs/field_pilot_checklist.md)).

## Why notebook 10 failed (notebook 12)

- **The HARV chronological loss (−3.52 nats) reproduces exactly.** The joint model's RMSE is 9.1 K against 3.4 K, with a *smaller* predictive SD.
  - Of the −9.6 K shift in the joint prediction, −9.8 K comes from one day-of-year spline column supported mainly by unseen August days. The joint model's penalty was 3.16, against 100 for the context model.
  - The image blocks contribute +2.4 K, mainly through near-field greenness and darkness.
- **High-RH rows.** Frozen deletion leaves G at −3.54. Only a full refit gives +1.04, by moving the joint penalty to 0.03.
- **Fold assignment.** Across seven inner fold maps, the HARV cross-fit ranges from −0.75 to +0.56 nats and HARV G from −3.5 to +0.9.
- **The CPER frame without `.meta`** changes the estimate by 0.1–0.2 nats even with the fold map fixed.

## Validation (notebook 11; 3-season design; 150 replicates per world, independent seeds)

| gate | result | outcome |
|---|---|---|
| G1 Type I ≤ 0.085 | 0.047–0.080 in seven nulls; 0.100 (AR 0.9); 0.107 (tanh T × sin hour); **0.787 (season × hour)** | fail |
| G2 power ≥ 0.80 | 0.93 (truth 0.03), 1.00 (0.08), **0.79** (slow state, 0.046), 1.00 (illumination, 0.045) | fail, narrowly |
| G3 \|bias\| ≤ 0.01 | ≤ 0.009 in every null and linear positive | pass |
| G4 cross-fit interval covers truth ≥ 0.85 | 0.86–0.90 in adequate nulls; 0.71, 0.79, 0.79, **0.49** | fail |
| G5 chronological interval covers its target ≥ 0.85 | 0.89–0.94 except **0.74** (slow state) | fail |
| G6, G7 stability under 1 % deletions | ≤ 0.027 / ≤ 0.024 nats | pass |
| G8 never more than the truth (non-Gaussian positives) | 0.005 of 0.025; 0.001 of 0.015 | pass |
| G9 adequacy false alarms ≤ 0.10 | 0 everywhere | pass, but the diagnostic has no power |

**Post-hoc** (§6, new seeds, not a re-validation):
- With an hour × season level, the season × hour world rejects at 0.050, but its estimate keeps +0.005 nats of context repair.
- The boosted adequacy model is 0.10 nats worse than the ridge context in every world, so it can never flag.

The **1-season design** keeps a usable test, except in the season × hour world (0.447), but no usable effect sizes: power 0.56 at 0.03 nats and instability up to 0.15 nats.

## Multi-year NEON audit (notebook 13)

- **Data and logs.** All five products are published for June–August 2019–2023 at both sites. There are no site-specific instrument issues in any summer.
- **Camera units and views.**
  - HARV's camera unit was replaced between July 2021 and July 2022, and its view changed; the PhenoCam evergreen masks were redrawn in February–March 2022.
  - CPER's view changed between 2019 and 2020: 44 px, with a different horizon and scale.
  - The configuration (auto-haze, AGC, auto-exposure, white balance, JPEG settings) is identical in every sampled frame.
- **Label quality by July.**
  - HARV 2021: only 75 % of minutes are valid, with RH reported up to 558 %.
  - CPER 2019: 58 % valid.
  - HARV 2022: the radiation error is 0.12 K against 0.6–1.2 K in other years.
- **Network-wide.** COVID-19 delayed calibrations in 2020–2021.

## Caveats

- All validation is synthetic, with single-feature images. The multi-feature, frozen-encoder case is not simulated.
- Development seeds were shared across worlds. The rejection rates that looked inflated in development were checked with 160 independent seeds (0.056).
- The validation gates were fixed after a development run on related world families. The validation shapes and parameters differ, but the families are the same.
- In the non-Gaussian worlds the contrast captures little of the true information (regime 20 %, near saturation ≈ 0 %). This is the cost of a linear mean in V.

## Competing interpretations

- **The season × hour failure** could be:
  1. a real capacity gap that NEON data will hit, because clock time is not solar time;
  2. an artefact of an implausibly strong synthetic interaction, of 0.8 K amplitude at the season's ends.

  NEON's diurnal D cycle by month would decide this, and it can be checked without images.
- **The slow-state coverage failure** could be:
  1. an interval problem, where week clusters are not independent;
  2. a mis-stated target: the frozen target averages over future seasons, while the interval describes one evaluation season.

  Both readings imply that intervals need more seasons.

## Recommendation

1. Add the hour × season level, a solar-time hour basis and a sensitive adequacy diagnostic: the training-only E[V | C] gain as a diagnostic only.
2. Develop on new worlds that include sunrise-driven diurnal shifts, then validate on a fresh suite with the same gates.
3. Treat intervals as indicative unless ≥ 5 seasons are available, reporting Q0 and the point estimate.
4. Restrict Q0 to residual persistence ≤ 0.6 per season, as measured (D-036). CPER would be excluded or stratified by regime.
5. Then extend NEON incrementally, starting with CPER 2020–2023.

**Alternative.** Stop investing in NEON E2 effect sizes and move straight to the field pilot. NEON's vegetation scenes, camera epochs and processed RGB already limit any result to the exploratory level.

## Ready-to-send discussion prompt

> You reviewed this project four times (latest: MODIFY the inference design; GO for multi-year NEON preparation and field-pilot planning). The attached report covers the required outputs.
>
> The redesign removed every visual-derived column from the context. It selects the context capacity on training rows only, from nested fixed bases, with week-grouped inner CV. It clamps day of year to the training range, clips images to their training range, and generates the shift-test null by linear projection on the label-free richest basis. Notebook 12 traced the notebook 10 HARV failure to one extrapolating day-of-year basis column (−9.8 K) in a weakly penalised joint model; the declared estimates moved by more than a nat across inner fold maps.
>
> On 16 untouched synthetic worlds (150 independent replicates each, 3-season design), the point estimate is unbiased (≤ 0.009 nats) and stable under 1 % deletions. E2 and E2_illum separate as designed. But four of nine predeclared gates fail:
> - Type I is 0.787 when the diurnal cycle changes over the season and the image encodes it, 0.100 at AR 0.9, and 0.107 for a tanh(T) × hour interaction.
> - Power is 0.79 in a slow-state world.
> - Interval coverage is 0.49 (cross-fit) and 0.74 (chronological) when the information persists for weeks.
> - The boosted adequacy diagnostic never flags, because it is 0.10 nats weaker than the ridge context.
>
> Post-hoc, an hour × season level restores Type I to 0.050 in the failing world. The multi-year audit found camera epochs (HARV unit replaced 2021–2022; CPER view changed 2019–2020) and label fault periods.
>
> Please challenge, specifically:
> 1. Is the season × hour failure a capacity gap NEON will really hit (clock time vs solar time), and is an hour × season level, a solar-time basis or both the right fix? Which worlds must the next suite add?
> 2. With week clusters failing under persistent information, should effect-size intervals stay open, with only Q0 and point estimates reported, until ≥ 5 seasons per site exist? Or is there an interval you would accept with three seasons?
> 3. May the training-only E[V | C] gain return as an adequacy *diagnostic* (never in the primary contrast), or is there a better auditor?
> 4. Should Q0 be restricted to residual persistence ≤ 0.6, which excludes CPER as it stands?
> 5. Given camera epochs and label faults, is CPER 2020–2023 the right first multi-year block, or should NEON E2 work stop in favour of the field pilot?
>
> Do not assume the recommendations are correct. Give GO / MODIFY / STOP for (a) another redesign-and-validate cycle, (b) the incremental multi-year NEON extension once a protocol passes, and (c) the tiered field-pilot checklist.
