# Review 4: first real-image comparison supports no claim; the estimator is unstable on single-season data

## Why this is a review checkpoint

Review 3 asked for escalation when the exploratory visual-information results were ready or a consequential scientific question arose. Both have happened.
- **Results.** The declared exploratory comparison (HARV and CPER, June–August 2023) has run. It supports no moisture-information claim.
- **Consequential question.** The estimates move by several nats per row under nuisance choices. The cause is traced to the train-only visual projection (D-035) and to a pathway, illumination, that the context omits. Both are design decisions for the reviewer, not tuning choices for me.

## Decisions requested

1. **Visual projection** (D-052). Choose one of:
   - (a) a projection on (hour, T) only, with season left to the linear day-of-year spline;
   - (b) blocked inner folds;
   - (c) dropping the projection;
   - another design.

   State which synthetic world must be passed before it is used on NEON again.
2. **Illumination pathway** (D-053). Should C include an illumination state (for example a clear-sky index from tower shortwave), giving `E2_illum = I(D; V | C, k_t)`? If so, is that the primary estimand or a second one?
3. **Slow vegetation and weather regimes.** Should the visual information be restricted to within-week variation? For example, the context could include a label-free, causal 7-day mean of each feature. Alternatively, should greenness-type features be excluded from V?
4. **Data before the next run.** Should several NEON summers (for example 2019–2023, HARV and CPER) be used, so that season is learned across years rather than interpolated within one?

## Changes since review 3 (deliverables 1–5)

The full account is in [docs/m1_exploratory_findings.md](../docs/m1_exploratory_findings.md).
- **Shielding and label** (notebook 08):
  - passive shield confirmed in ATBD rev A and rev C, with no radiation or wind flag;
  - radiation error up to +0.9 K (HARV) and +1.26 K (CPER) in high sun and calm air, falling to about +0.3 K above 5 m s⁻¹;
  - hybrid label `D_h` adopted, with `D_probe` and a dew-point target as sensitivities;
  - the earlier invariance claim corrected.
- **High RH** (notebook 08):
  - HARV plateaus at 98.5–99 %, and the persistence test blanks 26 % of minutes with implied RH ≥ 97 %;
  - CPER has wetting episodes up to 112.7 %;
  - no censoring; RH ≥ 98.3 % is a sensitivity stratum only.
- **Coverage and dependence** (notebook 09):
  - 2574 verified hourly frames, clock agreement 0 s, constant camera configuration, SHA-256 manifest;
  - 1197 and 1206 usable rows over 92 days per site;
  - daily context-residual lag-1 autocorrelation 0.50 (HARV) and 0.95 (CPER, 0.62 at lag 7).
- **Features** (notebooks 09–10):
  - nine predefined overlay-masked features, with the predeclared sky-clip rule dropping the sky features at HARV;
  - the features correlate with shortwave up to |r| = 0.65.
- **Shift test:** `shift_configs` enumerates the shifts and reports the minimum p (79 shifts, min p 0.0125, for 92 days).
- **Field pilot:** checklist drafted ([docs/field_pilot_checklist.md](../docs/field_pilot_checklist.md)).

## Exploratory results (notebook 10, declared plan)

| | HARV | CPER |
|---|---|---|
| shift test p (79 shifts, min 0.0125) | 0.90 | 0.59 |
| null median (nats) | +0.14 | +0.15 |
| cross-fit contrast | −0.51 | +0.13 |
| chronological G (indicative interval; 35 days, 6 weeks) | −3.52 (−6.42, −0.63) | +0.07 (−0.23, +0.37) |
| lag-1 of daily contrast | 0.89 | 0.48 |
| auto-exposure only: p / G | 0.0375 / +0.13 | 0.025 / +0.04 |

Sensitivities at HARV (G): `D_probe` +0.28, Td target +0.04, RH ≥ 98.3 % excluded **+1.04**. The last differs from the main analysis by 13 rows out of 1110.

## Diagnosis (notebook 10 §3, post-hoc)

1. **Fit/evaluation asymmetry of the projection.**
   - The boosted E[V | hour, T, doy] is cross-fitted by day on training rows, so a training day is predicted partly from its neighbours.
   - On CPER fit rows it explains 63 % of the daily-mean image variation; on evaluation rows, 0 %.
   - The joint model learns a projection–image split that does not transfer.
   - The same artefact gives the projection residual a negative lag-1 autocorrelation (−0.06 to −0.46, notebook 09).
2. **Contaminated null.**
   - `Cnull` uses the full-sample version of that projection, so the linear part `V̂` carries day-scale information, and the shifted draws keep it.
   - Hence null medians of +0.14 nats, where a valid null should sit at or below zero.
   - With a projection on (hour, T) only, the null medians fall to +0.01 (HARV) and +0.07 (CPER).
3. **Joint-model failure at HARV.**
   - The projection carries almost nothing at HARV (R² 0.02), yet G is −3.5.
   - Its daily losses fall in three consecutive weeks of the evaluation period (notebook 10 §3a).
   - Over the whole evaluation period the joint model's RMSE is 9.1 K against 3.4 K for the context model. This comes from a scratch diagnostic on the same models and is not shown in the notebook.
   - Which visual direction drives this has not been isolated.
4. **Projection variants.**
   - At HARV, G is −3.5 (declared), −9.7 (8-day inner folds) and +1.49 (hour, T only; shift p = 0.025).
   - At CPER, the cross-fit is 0.13, 1.37 and 0.12.
   - These variants are diagnostics. Picking the favourable one would be a forking path, and none of them is put forward as a result.

## Caveats

- One summer per site. CPER's context residual and most of its visual residuals persist over weeks, so the shift test's stationarity assumption is doubtful there (monsoon onset, phenology).
- Every visual result here is in processed RGB (auto-haze, AGC, JPEG) of vegetated scenes.
- The synthetic suite of M0 had no slow component shared by V and D outside C. That is why the asymmetry was not caught.

## Competing interpretations

- **The HARV loss** could come from:
  1. a seasonal drift in the features (sun geometry, canopy state) that the joint model maps onto D;
  2. a single regime in August that the fit period never showed;
  3. the projection asymmetry, which item 3 of the diagnosis makes less likely.
- **The positive acquisition-only result** could reflect:
  1. illumination (cloudiness) correlating with humidity;
  2. auto-exposure reacting to haze or wet surfaces;
  3. the same contaminated-null problem, which is less likely: null medians are ≤ 0.005 for the one-column exposure control.

## Recommendation

1. **Projection:** adopt (a), (hour, T) only, with season only in the linear spline. Before any further real-data run, validate on a new synthetic family in which V and D share a regime-scale component outside C, with and without seasonal drift of V. The family must meet the same six M0 criteria and an additional stability criterion: |ΔG| < 0.05 nats when 1 % of rows are dropped.
2. **Illumination:** report two estimands, E2 as defined and `E2_illum` with a clear-sky index in C. Repeat the acquisition-only control under both.
3. **Slow pathway:** for exploratory M1, also report the within-week estimand, with the causal 7-day mean of each feature in C. Keep greenness features in V, but report their single-feature contrast separately.
4. **Data:** extend to NEON summers 2019–2023 at both sites (about 5 × 92 days each) and fit season across years with leave-one-year-out folds. This replaces 6 dependent evaluation weeks with five independent years.

**Alternative.** Stop NEON E2 work after the projection fix and move all resources to the field pilot (RAW, fixed exposure, non-vegetated targets, visibility and leaf-wetness references). The argument for this: processed RGB of vegetation conflates illumination, phenology and camera automation with any optical moisture signal.

## Ready-to-send discussion prompt

> You reviewed this project three times (latest decision: GO for exploratory M1 and field-pilot design, MODIFY before confirmatory Exp 2a). The attached report covers the requested deliverables and the first exploratory real-image comparison: NEON HARV and CPER, June–August 2023, 2574 verified hourly PhenoCam frames, nine predefined overlay-masked features, hybrid label D_h = T_asp − Td.
>
> Results of the declared analysis:
> - the cyclic-shift test does not reject (p = 0.90 and 0.59, 79 shifts);
> - the chronological gain is −3.5 nats per row at HARV and +0.07 at CPER, on 6 evaluation weeks.
>
> The estimates are unstable: excluding 13 high-RH rows moves HARV G to +1.04, and three projection variants give −9.7 to +1.5. Post-hoc diagnostics trace this to the train-only projection E[V | hour, T, doy]. It interpolates across neighbouring days on training rows (it explains 63 % of the daily-mean visual variation on fit rows and 0 % on evaluation rows at CPER), and it contaminates the null generator (null medians +0.14 and +0.15 nats). Auto-exposure alone passes the shift test at both sites (p = 0.0375 and 0.025), and the features correlate with shortwave up to |r| = 0.65.
>
> Please challenge, specifically:
> 1. Is the diagnosis of the projection asymmetry correct and complete? Which redesign (projection on hour and T only, blocked inner folds, no projection, something else) would you accept, and which synthetic world must it pass first?
> 2. Should illumination (a clear-sky index) be part of C, as a second estimand or as the primary one? What does the acquisition-only result imply for E2 as currently defined?
> 3. Slow vegetation and weather regimes within one season: should E2 be restricted to within-week variation, and should phenology-type features be excluded from V?
> 4. Is multi-year NEON with leave-one-year-out folds the right next data step, or should NEON E2 work stop in favour of the field pilot?
> 5. Is anything in the post-hoc section being over-read? Is the HARV G = +1.49 variant correctly treated as non-evidence?
>
> Do not assume the recommendations are correct. Give GO / MODIFY / STOP for (a) continuing exploratory NEON E2 work after the projection redesign, (b) the multi-year NEON extension and (c) the field-pilot checklist as drafted.
