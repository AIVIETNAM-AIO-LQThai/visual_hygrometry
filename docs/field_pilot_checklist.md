# Field pilot: site and instrumentation checklist (draft)

**Status:** draft for review 4. Every requirement below comes from a specific failure or ambiguity in the NEON audit (notebooks 07–09), not from a general sensor wish-list. The checklist is to be applied before a site is chosen or any instrument is ordered. Nothing has been bought or installed.

## 1 · Reference temperature and humidity (label)

| requirement | reason (NEON evidence) |
|---|---|
| Fan-aspirated radiation shield for the RH/T probe; fan state logged at ≥ 1 min | The HMP155 at NEON sits in a passive shield. With high sun and calm air the probe reads up to +0.9 K (HARV) and +1.26 K (CPER) warmer than the aspirated thermometer (nb08 §2), and no published QC flag marks this. |
| Second, independent aspirated temperature sensor (PRT) on a separate logger channel | The leading label `D_h = T_asp − Td_probe` shares the aspirated unit with the conditioning temperature (nb08 §3). An independent sensor lets the context use one unit and the label use the other, so their errors are not common-mode. |
| Humidity reference that stays valid at saturation: chilled-mirror hygrometer, or a heated-probe RH sensor with a documented heating cycle | Near 100 % RH the HMP155 plateaus at ~98.5–99 % (HARV) or reads up to 112.7 % during wetting (CPER), and NEON's persistence test blanks RH on the plateau (26 % of minutes with implied RH ≥ 97 at HARV). High-RH labels are therefore missing-not-at-random (nb08 §4). |
| Raw 1 Hz (or ≥ 0.1 Hz) record kept with the 1-min aggregates; every QC test logged per sample, nothing blanked at the source | The NEON 1-min product removes values silently, and finer data were needed to tell a plateau from QC blanking (nb08 §4). |
| Calibration certificates with uncertainty for each humidity and temperature unit, and an on-site comparison at install and removal | The NEON expanded uncertainties (σ(D_h) ≈ 0.17–0.20 K) were the only error model available, and drift across a season could not be checked. |

## 2 · Saturation and wetting indicators (independent of the label probe)

| requirement | reason |
|---|---|
| Leaf-wetness sensor near the camera's near-field target | Distinguishes dew or wet surfaces from a saturated-probe artefact. NEON has no co-located indicator, so no fog or dew claim was possible (review 3, item 3). |
| Present-weather or forward-scatter visibility sensor | Gives an optical reference for fog and haze that does not depend on the camera, and is needed before any extinction-type interpretation. |
| Precipitation (tipping bucket) at the site | Wet-lens and rain frames must be identifiable without using the image itself. |

## 3 · Radiation and wind at probe height

| requirement | reason |
|---|---|
| Incoming shortwave pyranometer and 2D sonic or cup wind at the label-probe height | The radiation error grows with SW and falls with wind (nb08 §2: SW/(u+0.5) explains ~20 % of the variance of the probe–PRT difference). NEON's wind is measured at a different boom level from the probe at both sites. |
| Upwelling shortwave or a surface-temperature radiometer (optional) | Separates ground heating from probe heating on calm, clear days. |

## 4 · Camera and acquisition

| requirement | reason (NEON PhenoCam evidence) |
|---|---|
| RAW (or linear 16-bit) output; JPEG only as a secondary product | NEON frames are 8-bit JPEG with an unknown tone curve, so contrast and luminance are not radiometric (D-043). |
| Fixed exposure, gain (ISO), white balance and aperture; or bracketed fixed exposures. Every setting written to the image metadata | The PhenoCam runs auto-exposure, AGC and auto-haze. Exposure tracks illumination, which tracks humidity through cloud and season, so it must be modelled as a confounder (nb10 acquisition-only control). |
| No burned-in overlay; time and settings in a sidecar file | NEON frames need a fixed overlay mask covering 3.1 % of the image (D-042). |
| No auto-haze, dehaze, sharpening or local tone mapping | These operate on exactly the contrast that would carry the signal. |
| A sky region that does not clip: exposure chosen for the sky, or HDR bracketing | At HARV the sky band is overexposed on most overcast frames, and the predeclared QC rule drops both sky features (nb09 §4). |
| Lens heater or hood, and a scheduled lens-cleaning log | Fog on the lens and dirt look like haze. |
| Non-vegetated targets (rock, building, painted panel) in the near and far field | At both NEON sites the scene is vegetation, and the visual residuals persist over weeks (CPER greenness residual lag-1 0.98, nb09 §5). Phenology then competes with atmospheric optics as the pathway from moisture to the image. |
| Dark frames and flat field at install; a colour/grey target in the far field if possible | Needed for a radiometric response model. |

## 5 · Timing and geometry

| requirement | reason |
|---|---|
| NTP- or GNSS-disciplined clocks on the camera and the logger; offset logged daily | NEON image times come from file names and agree with the overlay clock, but the logger and camera clocks are separate systems (nb07, nb09 §1). |
| Exposure start and duration stamped in UTC | The 1-min label record is joined by the frame's UTC minute. |
| Surveyed distances and bearings to at least three far-field targets (e.g. 0.2, 1 and 5 km) with known orientation | Any contrast-versus-distance analysis needs target ranges. NEON region masks are horizontal image bands with no ranges, so no extinction estimate is possible. |
| Fixed camera mount with a monthly check of the field of view against a reference frame | Region masks assume a fixed view. |

## 6 · Site selection

- Seasonal range of humidity with frequent near-saturation mornings, but also dry periods, so that D is not almost constant within an hour of day.
- A far-field line of sight across uniform terrain (no tree line within the first kilometre in the far band).
- A second, contrasting climate (a semi-arid site like CPER), which is needed to test whether a visual effect transfers.
- Power and network for a fan-aspirated shield and for RAW storage (~0.1–0.5 TB per site-season at 10 min).
- At least 90 consecutive days per season. A NEON summer gives 92 days but only 35 evaluation days in 6 calendar weeks per site in the chronological hold-out (nb10). At CPER the daily context residual of D keeps a lag-7 autocorrelation of 0.62 (nb09 §5), so even those weeks are not independent. The pilot should plan for **≥ 2 seasons**, so that season can be learned from another year rather than interpolated within one.

## 7 · Open before the pilot design is final

- Which visual quantity is primary in confirmatory Exp 2a (frozen encoder vs the predefined low-dimensional features), and whether RAW changes that choice.
- Target sample size, expressed in independent weeks, from the variance of the NEON G estimates.
- Whether a chilled mirror is affordable, or a heated probe plus a leaf-wetness and visibility sensor is the accepted compromise.
