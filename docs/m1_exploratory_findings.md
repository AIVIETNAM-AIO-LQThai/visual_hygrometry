# M1 exploratory findings (after review 3)

Scope: the five deliverables requested in review 3. Evidence is in notebooks 08–10, and the decisions are D-044 to D-053 in [decisions.md](decisions.md). Everything here is exploratory. Nothing is confirmatory Exp 2a.

## 1 · HMP155 shielding and label definition (notebook 08)

- **Shielding.** Both ATBD revisions (NEON.DOC.000851 rev A 2015 and rev C 2022, §6.1.1.2) describe a passive radiation shield. The published RH product has no radiation or wind QC flag: its tests are Alpha, Beta, Gap, Null, Persistence, Range, SensorError, Spike and ValidCal (D-045). The tower-top sensor positions used are the current records for HARV and CPER.
- **Radiation error.** The probe–PRT temperature difference grows with shortwave and falls with wind. Under high sun it is +0.90 K (HARV) and +1.26 K (CPER) below 1 m s⁻¹ of wind, and +0.30 / +0.26 K above 5 m s⁻¹. SW/(u + 0.5) explains about 20 % of its variance. A 1-min transient test of whether probe heating also biases Td was inconclusive.
- **Label.** The hybrid label `D_h = T_asp − Td_probe` leads; the probe-temperature label `D_probe` is a mandatory sensitivity (D-046). Earlier text in notebook 07 and in addendum 2 said the hybrid label breaks D↔RH invariance. That was wrong and has been corrected: at fixed T_asp, D_h and RH_h are exact inverses. The real cost of D_h is that the label shares the aspirated unit with the conditioning temperature, and this is declared through `allow_shared_sensor=True`.
- **Uncertainty.** σ(D_h) ≈ 0.17 K (HARV) and 0.20 K (CPER) from the NEON expanded uncertainties. Negative D_h occurs in 0.1 % (HARV) and 1.5 % (CPER) of minutes. Minutes with D_h < −2σ are excluded as inconsistent; the values are not clipped.

## 2 · High-RH measurement model (notebook 08)

- HARV shows no hard clip. The probe plateaus near 98.5–99 %, and NEON's persistence test blanks RH on the plateau, so 26 % of minutes with implied RH ≥ 97 % have no RH value (all of them fail persistence in July). Dew point is still reported for 3.4 % of RH-blank minutes. High-RH labels are therefore missing-not-at-random if RH is used, and D_h (from Td) avoids most of this.
- CPER has 43 wetting episodes above 100 % RH (3062 minutes, maximum 112.7 %), and 52 % of them pass QC.
- Decision: no censoring and no censored likelihood for NEON labels. RH ≥ 98.3 % is a sensitivity stratum only, and no fog or dew mechanism is claimed (D-046).

## 3 · Coverage and temporal dependence (notebook 09)

- HARV and CPER, June–August 2023, hourly frames 06–19 LST: 2574 frames, 1.22 GB, SHA-256 manifest in `data/manifests/phenocam_hourly_2023JJA.csv`. The clock agrees with the overlay to 0 s, and the camera configuration is constant (auto-haze, AGC and auto-exposure on throughout).
- Usable rows: 1197 (HARV) and 1206 (CPER), each over 92 days.
- Daily context residual of D_h: lag-1 autocorrelation 0.50 at HARV; at CPER 0.95, with 0.62 at lag 7. Visual residuals: lag 1 of 0.30–0.55 at HARV and 0.68–0.98 at CPER, the greenness residual reaching 0.98.
- **Independent evaluation blocks.** The chronological hold-out leaves 35 evaluation days in 6 calendar weeks per site, and at CPER those weeks are themselves dependent.

## 4 · Real-image feature feasibility (notebooks 09–10)

Nine predefined, overlay-masked features are used (D-049). The predeclared sky-clip rule drops the two sky features at HARV (sky clipped on 99 % of frames) and keeps them at CPER. The features correlate with incoming shortwave up to |r| = 0.65 and with auto-exposure up to |r| = 0.40.

| | HARV | CPER |
|---|---|---|
| cyclic-shift test (79 shifts, min p 0.0125) | p = 0.90 | p = 0.59 |
| cross-fitted contrast (nats/row) | −0.51 | +0.13 |
| chronological G (indicative 95 % week-cluster interval) | −3.52 (−6.42, −0.63) | +0.07 (−0.23, +0.37) |
| evaluation days / weeks | 35 / 6 | 35 / 6 |
| lag-1 autocorrelation of daily contrast | 0.89 | 0.48 |
| acquisition-only control (auto-exposure): p, G | 0.0375, +0.13 | 0.025, +0.04 |

**The estimator is not stable on these data.**
- HARV G changes from −3.5 to +1.0 when 13 high-RH rows are excluded.
- HARV G ranges from −9.7 to +1.5 across three choices of the nuisance visual projection.
- Dropping a single frame moved the CPER cross-fit between runs from 0.04 to 0.13.

**Mechanism.**
- The train-only projection E[V | hour, T, doy] interpolates between neighbouring days in its own inner folds. On CPER fit rows it explains 63 % of the daily-mean image variation; on evaluation rows it explains none.
- The full-sample version of the same projection sits inside the null generator. It leaves real slow information in the shifted draws, which explains null medians of +0.14 nats.
- At HARV the projection carries almost nothing, and the joint model itself fails out of time.

No moisture-information claim is made.

## 5 · Limitations before confirmatory Exp 2a

1. **Visual projection.** The D-035 projection is not reliable when V and D share slow (multi-day) structure within one season. It must be redesigned and re-validated on synthetic worlds that include regime-scale persistence shared by V and D, before any real-data estimate.
2. **Illumination pathway.** Cloudiness and illumination reach the images directly and correlate with humidity, but they are not in C. The estimand needs a decision on whether C includes an illumination state (for example a clear-sky index from tower SW), and whether acquisition state is conditioned on.
3. **Slow vegetation state.** Phenology (greenness, darkness) is a moisture pathway through soil water, not through atmospheric optics. With one season it cannot be separated from regime-scale weather.
4. **Sample size.** One summer gives 6 evaluation weeks, and at CPER those are dependent. Confirmatory work needs several seasons, so that season is learned across years rather than interpolated within one.
5. **Processed RGB.** Auto-haze, AGC and JPEG stay uncontrolled confounders (D-043). The field pilot needs RAW capture with fixed exposure ([field_pilot_checklist.md](field_pilot_checklist.md)).
6. **Label.** The radiation error is characterised but not corrected. Only the hybrid label avoids it, at the cost of sharing a sensor with C. The Td-heating question is unresolved.
7. **Multiplicity.** Notebook 10 §3 and the single-feature table are post-hoc. No variant chosen from them can serve as the declared analysis of a confirmatory study.
