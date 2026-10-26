# Field pilot: site and instrumentation checklist (draft 2)

**Status:** draft after review 4. **No instrument is to be ordered yet.**

Every requirement traces to a failure or ambiguity found in the NEON audits (notebooks 07–13), not to a general sensor wish-list. Each item is tiered:
- **M — minimum viable.** Without it the pilot cannot estimate E2 at all, or repeats a NEON failure.
- **R — recommended.** Closes a known NEON ambiguity, or makes the pilot robust.
- **X — reference tier.** Needed only for mechanism claims (extinction, fog/dew) or for a confirmatory study.

The priorities set by review 4 are the M items:
- high-quality, radiation-shielded RH/T;
- an independent conditioning temperature;
- RAW capture;
- synchronised timestamps;
- stable site geometry;
- near-saturation QC.

## 1 · Reference humidity and temperature (label)

| tier | requirement | reason (NEON evidence) |
|---|---|---|
| M | Fan-aspirated radiation shield for the RH/T probe; fan state or flow logged at ≥ 1 min | The NEON HMP155 sits in a passive shield (ATBD, D-045). With high sun and calm air it reads up to +0.9 K (HARV) and +1.3 K (CPER) warmer than the aspirated thermometer, and no published flag marks this (nb08 §2). The error also varies by year (HARV 0.1–1.2 K, nb13 §3). |
| M | Independent aspirated temperature unit (PRT) on its own channel, used only as conditioning temperature | The leading NEON label `D_h = T_asp − Td` shares its unit with the conditioning temperature (nb08 §3). Separate units make label and context errors independent. |
| M | Near-saturation QC kept per sample: raw values, the sensor's own flags and the reason for any rejection, with nothing blanked at the source | NEON's persistence test blanked up to 36 % of the minutes with implied RH ≥ 97 % in a July (nb13 §3), so high-RH labels are missing-not-at-random (nb08 §4). |
| M | Calibration certificate with uncertainty for every RH and T unit, plus an on-site intercomparison at install and removal | NEON gave uncertainty only as expanded values, which changed by year (RH 1.2–3.1 %, nb13 §3), and sensor swaps are not in its public logs. |
| R | Second RH probe of a different make, in its own aspirated shield | Lets a probe fault be distinguished from weather (cf. HARV July 2021: RH up to 558 %, 25 % of minutes invalid, nb13 §3). |
| R | 1 Hz (≥ 0.1 Hz) raw record kept alongside the 1-min aggregates | Finer data were needed to tell the plateau from QC blanking (nb08 §4). |
| X | Chilled-mirror dew-point hygrometer | The only reference that stays valid through saturation. It is needed for fog/dew mechanism claims, which NEON could not support. |

## 2 · Saturation and wetting indicators (independent of the label probe)

| tier | requirement | reason |
|---|---|---|
| R | Leaf-wetness sensor near the near-field target | Separates wet surfaces from probe saturation. NEON has none, so no dew claim was possible (review 3). |
| R | Tipping-bucket precipitation | Rain and wet-lens frames must be identifiable without using the image. |
| X | Forward-scatter visibility or present-weather sensor | An optical fog/haze reference independent of the camera; a prerequisite for any extinction interpretation. |

## 3 · Radiation, illumination and wind at probe height

| tier | requirement | reason |
|---|---|---|
| M | Incoming shortwave pyranometer at the site, levelled, with the levelling checked at every visit | E2_illum needs a quality-controlled clear-sky index (review 4, item 4). NEON's radiometers had levelling faults lasting months (nb13 §2). |
| M | Wind at the label-probe height | The radiation error falls with wind (nb08 §2). NEON wind is on another boom level, and its boom positions changed (nb13 §3). |
| R | Upwelling shortwave or a surface-temperature radiometer | Separates ground heating from probe heating on calm, clear days. |

## 4 · Camera and acquisition

| tier | requirement | reason (NEON PhenoCam evidence) |
|---|---|---|
| M | RAW (or linear 16-bit) capture; JPEG only as a by-product | NEON frames are 8-bit JPEG with an unknown tone curve (D-043). |
| M | Fixed exposure, gain, white balance and aperture (or fixed bracketing); every setting in the image metadata; no auto-haze, dehaze, sharpening or local tone mapping | Auto-exposure alone passed the zero-information test at both NEON sites (nb10 §2). The automatic processing acts on exactly the contrast that would carry the signal. |
| M | No burned-in overlay; time and settings in a sidecar | NEON needs an overlay mask covering 3.1 % of each frame (D-042). |
| M | Camera unit identity (serial or MAC address) logged with every frame, and a reference frame saved after any intervention | The HARV camera unit was replaced between 2021 and 2022, with a change of view (nb13 §4). Camera epochs must be declared strata. |
| R | Exposure chosen so the sky does not clip, or HDR bracketing | At HARV the sky band is clipped in 99 % of frames, so the sky features were dropped (nb09 §4). |
| R | Non-vegetated near and far targets (rock, building, painted panel) | Both NEON scenes are vegetation, and phenology persists over weeks (CPER greenness residual lag-1 0.98, nb09 §5). It competes with atmospheric optics as the moisture pathway. |
| R | Lens heater or hood, and a lens-cleaning log | Lens fog and dirt mimic haze. |
| X | Dark frames, flat field and a grey/colour target in the far field | A radiometric response model, needed for extinction claims. |

## 5 · Timing and geometry

| tier | requirement | reason |
|---|---|---|
| M | NTP- or GNSS-disciplined clocks on the camera and the logger; offset logged daily; exposure start and duration in UTC | NEON's clocks agreed to 0 s (nb07, nb09 §1), but they are separate systems. The label is joined by the frame's UTC minute. |
| M | Rigid mount and a monthly field-of-view check against the reference frame (an automated shift and edge-correlation check as in nb13 §4) | CPER's view changed between 2019 and 2020 (44 px), and HARV's with its 2022 unit swap (nb13 §4). Fixed image regions assume a fixed view. |
| R | Surveyed distances and bearings to at least three far-field targets (e.g. 0.2, 1 and 5 km) | Any contrast-versus-distance analysis needs target ranges; NEON regions are image bands with no ranges. |

## 6 · Site and record design

- **M:** at least three seasons at one site, so that season is learned across years rather than interpolated within one.
  - In the synthetic validation (nb11), the 1-season design gave power 0.56 at a truth of 0.03 nats and 90th-percentile instability up to 0.15 nats. With one of three seasons held out, power was 0.93 at 0.03 nats and the estimate was stable within 0.03 nats.
  - Even three seasons gave intervals that covered the truth in only 0.49 of replicates when the information sits in a state persisting for weeks. More seasons, not more days, are what buys independent replication.
- **M:** a humidity climate with frequent near-saturation mornings and dry spells.
- **R:** a second, contrasting climate (semi-arid), to test transfer.
- **R:** power and network for the aspirated shields and RAW storage (~0.1–0.5 TB per site-season at 10 min).
- **R:** a far-field line of sight across uniform terrain.

## 7 · Open before the pilot design is final

- Which visual quantity is primary in confirmatory Exp 2a (frozen encoder or the predefined low-dimensional features), and whether RAW changes that choice.
- Sample size in independent seasons and weeks, from the variance of the multi-year NEON G estimates once available.
- Whether the X-tier chilled mirror is affordable, or whether a heated probe plus the R-tier wetting and visibility indicators is the accepted compromise.
