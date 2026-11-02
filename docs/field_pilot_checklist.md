# Field pilot: checklist by purpose (draft 3)

**Status:** draft after review 5. **No equipment is to be ordered yet.** Superseded in structure by [m2a_pilot_design.md](m2a_pilot_design.md) (D-083), which keeps every requirement below. The A-tier camera test "image statistics of a fixed target are constant across illumination" is corrected there (§13): it is the panel-normalised quantity that must be stable.

Each requirement traces to a NEON finding (notebooks 07–15) or to the synthetic validations (notebooks 11 and 14). The checklist separates three purposes that need different durations and different hardware:
- **A — engineering pilot (weeks to a few months):** prove that the camera and measurement chain work and are synchronised. It needs neither several seasons nor any statistical power.
- **B — extended research collection (several seasons):** enough independent meteorological regimes to estimate and test E2, under the protocol that passes validation.
- **C — reference instrumentation:** supports optical, aerosol and condensation *mechanism* claims, which neither A nor B can.

A requirement listed under A is also required for B and C; one listed under B is also required for C.

## A · Engineering pilot: the minimum chain

| requirement | test that the pilot must pass | reason |
|---|---|---|
| Fan-aspirated radiation shield for the RH/T probe, with fan state or flow logged at ≥ 1 min | the probe–PRT difference is independent of shortwave and wind over the pilot (no growth with SW at low wind) | NEON's passive shield: +0.9 to +1.3 K in calm, high sun; it varies by year and is unflagged (nb08, nb13) |
| Independent aspirated PRT on its own channel, used only as conditioning temperature | the two temperature units agree within their stated uncertainties when both are aspirated | NEON's leading label shares a unit with the context (nb08) |
| Calibration certificate with uncertainty for every RH and T unit; intercomparison at install and removal | the drift between the two comparisons is within the certificate's uncertainty | NEON's uncertainty changed by year, and swaps are not logged (nb13) |
| Near-saturation QC kept per sample: raw values, sensor flags and the reason for any rejection; nothing blanked at the source | every blanked or flagged sample is traceable to a rule | NEON's persistence test blanked up to 36 % of high-RH minutes (nb13) |
| RAW (or linear 16-bit) capture with fixed exposure, gain, white balance and aperture; no auto-haze, dehaze, sharpening or local tone mapping; settings in the metadata | the image statistics of a fixed target are constant across illumination at a fixed exposure | auto-exposure alone passed the zero-information test at NEON (nb10) |
| No burned-in overlay; time and settings in a sidecar | none needed | NEON needs a 3.1 % overlay mask (D-042) |
| NTP- or GNSS-disciplined clocks on camera and logger; offset logged; exposure start and duration in UTC | the logged offset stays ≤ 1 s | the label is joined by UTC minute (nb09) |
| Camera unit identity (serial or MAC) in every frame; a reference frame after every intervention; rigid mount | the automated shift and edge-correlation check (nb13) against the install frame passes daily | HARV unit swap and CPER view change (nb13) |
| Levelled pyranometer at the site, with the level checked at each visit | the clear-sky index is ≈ 1 on clear days | E2_illum needs K (D-060); NEON levelling faults (nb13) |
| Wind at the probe height | none needed | the radiation error depends on wind (nb08) |

## B · Extended research collection: what E2 estimation needs

| requirement | reason |
|---|---|
| **Several seasons** at one site, so that season and the diurnal cycle are learned across years (the planned design is leave one season out with ≥ 4 seasons) | 1-season effect sizes are unusable (nb11: power 0.56 at 0.03 nats, instability up to 0.15 nats). Week-cluster intervals failed when information persisted for weeks (coverage 0.49); intervals need between-season replication and validated coverage, and more seasons alone do not guarantee it (statistical note §5) |
| A climate with frequent near-saturation mornings, dry spells and varied weather regimes | regime diversity is what gives independent information; persistent regimes defeat the shift test (nb11: 0.100 at AR 0.9) |
| Second RH probe of a different make in its own aspirated shield | separates probe faults from weather (cf. HARV July 2021, nb13) |
| Leaf-wetness sensor near the near-field target; tipping-bucket precipitation | wet surfaces and wet lenses must be identifiable without the image |
| A sky region that does not clip (exposure for the sky, or HDR bracketing) | HARV's sky band is clipped in 99 % of frames (nb09) |
| Non-vegetated near and far targets (rock, building, painted panel) | phenology persists for weeks and competes with optics as the pathway (nb09, nb14) |
| Lens heater or hood, and a cleaning log | lens fog and dirt mimic haze |
| Power, network and storage for RAW at ≤ 10 min (~0.1–0.5 TB per site-season) | |
| A second, contrasting climate | transfer test |

## C · Reference instrumentation: mechanism claims

| requirement | claim it supports |
|---|---|
| Chilled-mirror dew-point hygrometer | labels valid through saturation; fog and dew |
| Forward-scatter visibility or present-weather sensor | an optical extinction reference independent of the camera |
| Surveyed distances and bearings to ≥ 3 far-field targets (e.g. 0.2, 1 and 5 km) | contrast-versus-distance and extinction estimates |
| Dark frames, flat field and a grey/colour target in the far field | a radiometric response model |
| Dried-aerosol (PM) measurement with a logged inlet RH | E3, hygroscopic growth |
| Upwelling shortwave or a surface-temperature radiometer | separating surface heating from probe heating |

## Open before the design is final

- The number of seasons B needs, from the power and coverage of whichever protocol passes validation (notebook 14 onward), stated in independent seasons, not days.
- Whether a heated RH probe plus the B-tier wetting indicators is an acceptable substitute for the C-tier chilled mirror for the confirmatory label.
- The primary visual quantity for confirmatory Exp 2a (predefined features or a frozen encoder), and whether RAW changes it.
