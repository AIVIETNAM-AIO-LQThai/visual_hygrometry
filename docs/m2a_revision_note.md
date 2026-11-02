# M2A revision note: draft 1 → draft 2 (after review 8)

**Status:** 2026-11-02 (D-086 to D-088). It accompanies [m2a_pilot_design.md](m2a_pilot_design.md) draft 2. **No equipment is to be ordered.** The next independent review is when the specification meets an actual site and budget.

## Corrected requirements

| topic | draft 1 | draft 2 | where |
|---|---|---|---|
| Near-saturation labels | readings ≥ 100 − σ_RH treated as censored (following D-004) | Five cases are kept apart: noisy observation, verified clipping, response lag, condensation fault, documented reporting limit. A censored likelihood is used only at a demonstrated limit. Every sample is kept with its flags. A bench test at saturation establishes which cases apply. | §6, §11 item 7, §12; D-087 |
| Sun in the field of view | a poleward view, within ±45°, assumed to keep the sun out | An annual sun-path analysis at the actual latitude, azimuth, tilt and field of view, with a flare margin. Any remaining minutes are excluded by a declared geometric rule. It must hold for tropical sites. | §4 |
| P1 optics | C/C₀ = exp(−σr), with distances treated as sufficient | Target intrinsic radiance, path transmission, path radiance and camera response are separated. σ is identified only through known, equal, or commonly changing intrinsic contrasts. The uncertainty budget includes path heterogeneity, atmospheric variability and the σ_dry baseline. | §2.1 |
| P1 target admission | ≥ 3 dark targets at known distances | Targets must satisfy one identification route, span ≥ 10 px, and have the horizon sky behind them. Paths must not cross fog-pooling valleys. The site's predicted Δσ precision must meet test 3. | §4 |
| P1 acceptance | σ precision ≤ 25 % of σ_dry | Δσ̂ day-to-day SD ≤ Δσ_RH / 3 (provisional), with Δσ_RH = σ_dry·[f(RH_humid) − f(RH_dry)] at the low end of σ_dry; P2 only if it fails | §13 test 3 |
| Radiometric stability | panel-normalised reflectance within ±2 % | Judged against a declared budget (noise, calibration residuals, panel angular and diffuse/direct terms, spectral term, drift). It passes if observed SD ≤ 1.5 × predicted and the budget is ≤ 1/3 of the smallest pathway signal. Panel ratios are not treated as illumination-invariant. | §13 test 2, §11 item 8 |
| Window heater | "window wetness is impossible" while the margin holds | The margin is a reduction of condensation risk, not proof. Image-derived window-wetness flags remain strata. | §5, §9, §12 |
| Cameras | two at the recommended tier | One RAW camera by default at every tier. A second only if one of four stated geometric conditions holds, with a worked single-camera example. | §5, §10, §14 item 1 |
| Sites | open | One engineering site by default; staged screening (desk, visit, one-week test) | §4, §14 item 2 |
| P1 status | primary with P2 | conditional on far-field geometry; P2 stands alone | §2 |

## Still needs a physical site or a budget

- **Site.** The screening of §4 decides it: sun-path table, path profiles, target identification route, representativeness, dew climatology. Whether P1 is pursued at all follows from it.
- **Camera and lens.** The final focal length and aperture, the one-or-two-camera test (§5) and the target pixel spans all need the site's geometry.
- **Budget tier** (§14 item 5). Minimum first, or recommended from the start. The costs are unverified list-price ranges, and quotes are needed.
- **Near-saturation label** (§14 item 4). A heated probe or a chilled mirror. The bench test (§11 item 7) on the chosen probe decides how much of the saturation range it covers.
- **T_surface in a P2 context** (§14 item 3), still open.
- **Provisional numbers:** the 1.5 × budget factor, the 1/3 of the signal, and the 10° flare margin. They are fixed with the site and lens, before installation.
- **Null calibration for the research collection** (§14 item 6, D-085). It affects site count and duration for purpose B, not the engineering pilot.

## What the first engineering pilot will validate

The pilot runs for ≥ 4 weeks, including dew mornings and dry days (§13). It validates:
1. **The measurement chain:** aspirated shields, agreement of the two temperature units, certificate drift, clocks ≤ 1 s, daily view checks, a levelled pyranometer, and ≥ 95 % frame and ≥ 98 % sensor completeness.
2. **Radiometric stability** of the panel-normalised reflectance within a declared budget.
3. **Near-saturation behaviour** of the chosen probe in the field: which of the five cases occur, and how often, on dew mornings.
4. **P2 detectability:** whether the near-field surfaces change measurably beyond their dry-morning range when T_surface ≤ T_dew.
5. **P1 detectability,** only at a site that passed P1 admission: whether Δσ̂ is precise enough to see the expected humidity-driven change.

It will **not** test E2, estimate visual moisture information, or support any mechanism claim. Its data are development data and never become confirmatory (§1).
