# M2A: engineering pilot design

**Status:** draft 1, 2026-11-01 (D-083). **No equipment is to be ordered.** This design restructures [field_pilot_checklist.md](field_pilot_checklist.md) (draft 3) around named physical pathways: a shared acquisition core plus optional modules. Every requirement of the checklist is kept, and each still traces to a NEON finding. Costs are approximate list-price ranges from general market knowledge. They are unverified, and must be replaced by quotes before any purchase decision. Decisions that need independent review are collected in §14.

## 1 · Purpose and limits

The engineering pilot (purpose **A** of the checklist) runs for weeks to a few months. It must demonstrate:
- that the measurement chain works (shielding, synchronisation, radiometric stability, near-saturation labels);
- that the P1 and P2 signals can be *measured* above camera noise.

It is not a test of E2:
- Its data are development data, and they never become confirmatory blocks (metadata policy, data stages).
- It cannot supply the independent seasons that E2 estimation needs (purpose **B**).
- It cannot support mechanism claims that require reference instruments (purpose **C**).

**Fixed exposure is not an illumination correction.** RAW capture at fixed settings removes the camera's *automatic response* to light: auto-exposure, auto white balance, haze compensation and tone mapping. It does not remove physical illumination confounding. Sun angle, cloud, the diffuse fraction and surface shading change scene radiance, are correlated with D through the diurnal cycle and the weather, and remain in every image. Measured radiation, in-scene panels and solar geometry make these effects *observable* and allow them into C (E2_illum). They are not automatic corrections, and the residual illumination pathway must still be argued for each analysis.

## 2 · Pathways the design serves

| pathway | physics | visual quantity | what must be measured beside the camera | status |
|---|---|---|---|---|
| **P1: atmospheric extinction and hygroscopic aerosol growth** | Aerosol particles take up water as RH rises, so the extinction σ grows (f(RH) = σ(RH)/σ_dry, typically ≈ 1.2–1.5 at 80 % and larger near 95 %). The apparent contrast of a dark target at distance r falls as C/C₀ = exp(−σr), with Koschmieder visibility V = 3.912/σ. | Contrast of dark targets against the horizon sky at several known distances, from linear RAW radiance; σ estimated from contrast against distance | Target distances and bearings; inherent contrast of near references; illumination (direct and diffuse); RH and T along the path (represented by the station); **aerosol loading** (dry), since σ_dry is a confounder of σ | primary |
| **P2: dew, condensation, wet surfaces** | Water condenses where T_surface ≤ T_dew. Wet surfaces change reflectance, specular highlights and texture. | Near-field reflectance and texture of characterised surfaces (plates, grass), especially around dawn | **Surface temperature** of the observed surfaces; leaf wetness beside them; T and Td at their height; radiation (net long-wave cooling drives the surface below air temperature) | primary |
| **P3: vegetation water status** | Water stress changes canopy colour and structure over days to weeks. | Greenness and structure indices | Soil moisture, phenology record | secondary, exploratory; it is confounded with season, as CPER 2022 showed |

**Rules carried into analysis:**
- **P2 has an explicit condition.** Condensation is modelled through T_surface ≤ T_dew, not by treating a wet surface as an RH reading.
- **Wetness is a mediator.** It is caused by humidity, so it is never conditioned on in E2 (metadata policy: `mediator`).
- **P1 claims need dry aerosol.** Stronger claims about the hygroscopic mechanism (E3) need a dry-aerosol measurement; the engineering pilot does not.

## 3 · Station architecture

| layer | contents | needed for |
|---|---|---|
| **Core** (every tier) | RAW camera at fixed settings, heated housing; independent aspirated label unit (RH/T); independent aspirated conditioning thermometer; pyranometer; wind; rain; GNSS-disciplined clock; logger and acquisition computer; in-scene grey/black panels; reference frame and view-shift check | A |
| **P1 module** | ≥ 3 surveyed far-field dark targets; near-field black reference; a sky region that does not clip; diffuse/direct radiation split; optical PM with a dried inlet and logged inlet RH | A (geometry and radiometry), B (σ estimation) |
| **P2 module** | characterised near-field surfaces (painted metal plate, glass plate, grass patch) in focus; contact and infrared surface thermometers; leaf-wetness sensors beside them; a dense dawn frame schedule | A (dew detectability), B |
| **Reference module** | chilled-mirror hygrometer; forward-scatter visibility sensor; reference-grade diffuse/direct radiometry; humidity-controlled aerosol measurement; panel calibration by spectroradiometer | C |

## 4 · Site-admission criteria

**Must** (the site is rejected without these):

| criterion | test before installation | reason |
|---|---|---|
| A rigid fixed mount for ≥ 1 year (a building wall or a guyed mast), permission and access for weekly visits | written permission; mount deflection under wind checked by the view-shift test (notebook 13 method) over 1 week of test frames | HARV and CPER view changes (notebook 13) |
| Mains power or a sized solar supply; network or on-site storage with weekly retrieval | power budget ≥ 1.5 × the measured load | |
| View oriented poleward (north in the northern hemisphere), within ±45°, so the sun never enters the field of view at the site's latitude | sun-path overlay on a test frame for the whole year | flare and clipping |
| Sensor mast within about 50 m of the camera, on the same land cover, not in a local hollow, away from irrigation, ponds, cooling towers and exhausts | site sketch with distances; a 48 h comparison of a portable RH/T unit at the mast and near the near-field targets | the label must represent the air the camera looks through and at |
| The climate gives both frequent near-saturation mornings and dry spells in the pilot months | climatology from a nearby station: share of hours with RH ≥ 90 % and with RH ≤ 40 % per month | regime diversity (checklist B) |
| No burned-in overlay is possible; settings fully manual | camera spec check | D-042 |

**P1 module** (needed if P1 is pursued at this site):

| criterion | test |
|---|---|
| ≥ 3 dark, non-vegetated or stable targets (rock faces, building façades, forest edges as a fallback) at distances spanning about 0.3–10 km, e.g. ≈ 0.5, 2 and 5–10 km, seen against the horizon sky | distances from a DEM or GIS and a laser rangefinder (≤ 1 km); line of sight checked on a test frame |
| Near-horizontal paths over homogeneous land cover, with no large water bodies or towns along them | path elevation profiles; land-cover map |
| No dominant local aerosol source (unpaved road, quarry, chimney) upwind of the near paths, or else documented and logged | site survey and wind rose |

The distance range follows from contrast transmittance exp(−σr):
- In clean air (σ ≈ 0.02–0.05 km⁻¹), a measurable change in σr of ≥ 0.05 needs r of several km.
- In haze (σ ≈ 0.5–1 km⁻¹), targets beyond about 5 km are lost (σr > 3).
- Several distances keep at least one target in range in both conditions.

**P2 module:**

| criterion | test |
|---|---|
| Room for characterised surfaces 2–15 m from a camera, open to the sky (unobstructed long-wave cooling), on the same land cover as the mast | sky-view check; a test frame shows the surfaces in focus |
| Dew occurs: clear calm nights in the pilot months | climatology of clear and calm nights, or a 1-week leaf-wetness test |

## 5 · Camera and acquisition

**Settings that are fixed and recorded per frame:**
- RAW capture (12–14-bit linear) with no in-camera processing: no auto-exposure, auto gain, auto white balance, haze compensation, sharpening, noise reduction or tone mapping.
- Focus and aperture locked mechanically (taped or set-screwed); the IR-cut filter fixed in place.
- No overlay; time and settings in a sidecar.
- The camera serial number in every frame's metadata.

**Camera classes:**

| class | example specification | approximate cost | judgement |
|---|---|---|---|
| single-board RAW camera | 12 MP, 12-bit Bayer RAW (DNG), CS/C-mount lens, single-board computer | USD 150–400 with lens and computer, plus a housing | acceptable for the **minimum** engineering tier. Rolling shutter. Radiometric stability is not documented, so it must be characterised (§11). |
| industrial machine-vision camera | 5–12 MP colour, 12-bit RAW, GigE/PoE, published EMVA 1288 characterisation (linearity, dark noise, saturation) | USD 400–1,500 body, plus 150–800 lens | **recommended**: documented radiometry, stable, no shutter wear |
| mirrorless or DSLR, tethered | 20–24 MP, 14-bit RAW, controlled over USB | USD 700–2,000 with lens | high dynamic range, but consumer firmware, mechanical-shutter wear (≈ 10⁵ actuations is 1–3 years at this schedule) and power management; a fallback only |

**Housing:** IP66/67 with an optical-glass window, a window heater driven to keep the window ≥ 2 K above the dew point (window temperature logged), and a sun and rain hood. Approximate cost USD 150–600.

**Exposure strategy.** The radiometric target is linear radiance L ∝ (DN − dark)/(t·g). The options, all with gain fixed:
- **E-a, fixed single exposure.** It clips the sky at noon or under-exposes dawn. It is inadequate alone, and is kept only as the reference setting.
- **E-b, fixed bracket ladder** (recommended). Every capture takes the same 3–5 exposures, 2 EV apart, chosen once at installation to span dawn to noon. The analysis uses, per region, the longest unclipped exposure, or merges in the linear domain with the known ratios. The ladder never depends on the scene.
- **E-c, solar-scheduled exposure.** A fixed function of solar elevation only, which is therefore a function of C. It is acceptable but less general than E-b. It is rejected if the camera cannot set exposure deterministically.

None of these removes illumination confounding (§1). E-b only guarantees that the image records radiance without a scene-dependent camera response.

**Frame schedule** (preliminary):
- From civil dawn (solar elevation −6°) to civil dusk, one ladder every 10 min.
- In the P2 dawn window (elevation −6° to +15°), one mid-ladder exposure every 2 min.
- Hourly at night, a dark frame or a night-sky frame for the dark-current model.
- Storage per day ≈ frames × RAW size. A 3-exposure ladder over ~15.5 h is ≈ 280 frames; at 7.5 MB (5 MP, 12-bit) that is ≈ 2.1 GB/day, and at 18.5 MB (12 MP) ≈ 5.2 GB/day, or 65–160 GB/month before the dawn burst. A weekly on-site copy plus an off-site copy are kept, with SHA-256 manifests as for NEON.

## 6 · Reference humidity and temperature

| element | requirement | test in the pilot | NEON finding |
|---|---|---|---|
| **Label unit** (`ref_sensor_id`) | RH/T probe in a fan-aspirated radiation shield, fan state or tachometer logged at ≥ 1 min, calibration certificate with uncertainty | probe-minus-PRT difference independent of shortwave at low wind | passive shield +0.9 to +1.3 K (notebook 08) |
| **Conditioning thermometer** (`cond_sensor_id`) | separate aspirated shield; class A 4-wire PRT or precision thermistor; used only as T in C | the two units agree within their uncertainties when both are aspirated | shared unit (notebook 08) |
| **Second RH probe** (recommended tier) | a different make, in its own aspirated shield | separates probe faults from weather | HARV July 2021 (notebook 13) |
| **Near saturation** | raw values, flags and rejection reasons kept per sample; nothing blanked at the source; a heated probe (recommended tier) or a chilled mirror (reference tier) for labels through saturation | every flagged sample traceable to a rule | up to 36 % blanked (notebook 13) |
| **Sampling** | 1 s sampling, 1-min means and SDs stored, raw retained | | |

**Label uncertainty.** D = T − Td error from the RH error alone, computed with `thermo.dewpoint` at T = 20 °C:

| RH | D | σ_RH ±1.5 % | ±2 % | ±3 % |
|---|---|---|---|---|
| 30 % | 18.1 K | ±0.70 K | ±0.94 K | ±1.41 K |
| 50 % | 10.7 K | ±0.45 K | ±0.60 K | ±0.89 K |
| 80 % | 3.6 K | ±0.29 K | ±0.39 K | ±0.59 K |
| 95 % | 0.8 K | ±0.25 K | ±0.34 K | ±0.51 K |

Near saturation the absolute error is smallest but the relative error is largest. At 95 % RH a ±2 % probe leaves D uncertain by about 40 % of its value, and readings above 100 − σ_RH are censored (notebook 00 §5). Temperature radiation error adds to the label through T, and in the shared-sensor case to the context as well. Aspiration brings it to about 0.1–0.2 K, against ≈ 1 K for passive shields in calm sun.

## 7 · Radiation, wind and other meteorology

| quantity | minimum | recommended | reference | role |
|---|---|---|---|---|
| global shortwave | silicon-cell pyranometer, levelled | thermopile pyranometer | the same, ventilated | `met`; the clear-sky index K for E2_illum |
| diffuse/direct split | none | shadow-ring diffuse pyranometer (second unit) | sunshine-pyranometer or tracker-class instrument | `met`; illumination geometry for P1 and P2 |
| wind | cup anemometer and vane at sensor height | 2D ultrasonic | the same plus wind at camera height | `met`; radiation error and dew formation |
| precipitation | tipping bucket | the same, heated if needed | present-weather sensor (QC only) | `met`; QC |
| pressure | logger barometer | the same | the same | `met` |
| upwelling long-wave or surface radiometer | none | infrared surface thermometer on the P2 plate | net radiometer | P2: `met` (an open decision, §14) |

## 8 · Synchronisation

- **Clocks.** A GNSS receiver with PPS disciplines the acquisition computer by NTP (chrony); the logger is synchronised from it. The offsets of every clock are logged hourly.
- **Trigger latency.** The camera is triggered in software. The exposure start is the host timestamp plus a measured trigger latency. The latency is measured at installation and every month by photographing a GNSS-PPS-driven LED or a GNSS-synchronised display. Mean and SD are stored per camera and firmware version.
- **Tolerance.** |frame time − UTC| ≤ 1 s after correction, checked daily. Labels are joined by UTC minute, so 1 s is ample, but the check catches drift and firmware faults (the NEON template overlay, notebook 15).
- **Stored times.** The start and duration of every exposure, in UTC.

## 9 · Dataset schema and metadata roles

Every new field gets an `x-role` from the [metadata policy](metadata_policy.md). The JSON schemas are written when a site is chosen; the field lists are fixed here.

**Frame manifest** (`frame.schema.json`; existing fields kept):

| field | role | note |
|---|---|---|
| `bit_depth`, `black_level`, `bayer_pattern`, `gain_db` | `calib` | |
| `exposure_start_utc`, `exposure_s`, `bracket_index`, `bracket_id` | `time` / `calib` | the ladder position never becomes a feature |
| `trigger_latency_s`, `clock_offset_s`, `time_source` = `gnss_ntp` | `provenance` | |
| `sensor_temp_c` | `calib` | used only for the dark-current model; never a feature (NEON's camera temperature correlates with air temperature at r = +0.90) |
| `window_temp_c`, `window_heater_on`, `hood_installed` | `provenance` | QC; window wetness is impossible while window_temp − Td ≥ 2 K |
| `lens_id`, `focus_locked`, `aperture_locked`, `firmware` | `provenance` | |

**New sensor quantities** (`sensor.schema.json` enum):

| quantity | role |
|---|---|
| `sw_diffuse`, `sw_direct` | `met` |
| `surface_temp` (per surface id), `lw_up` | `met` (an open decision, §14) |
| `fan_rpm` (per shield) | `label_qc` |
| `pm_dry`, `pm_inlet_rh` | `aerosol_dry` |
| `pm_raw` | `forbidden` |
| `leaf_wetness`, `visibility` | `mediator` |
| `window_temp` | `provenance` |

**Site and target table** (new `site.schema.json`):
- site_id, latitude, longitude, elevation;
- camera_id, mount height, azimuth, tilt and field of view;
- reference frame hash;
- per target:
  - target_id and kind (`far_dark`, `near_black`, `panel_grey`, `wet_plate`, `glass_plate`, `grass`, `sky`);
  - distance_m with its uncertainty and method, bearing and elevation angle;
  - material;
  - reflectance with its uncertainty and calibration id;
  - ROI polygon in reference-frame pixels;
  - pathway (P1, P2 or P3);
  - valid_from and valid_to.

**Calibration records:**
- calib_id;
- type (`dark`, `flat`, `linearity`, `panel`, `salt`, `intercomparison`, `latency`, `level`, `ice_point`);
- time, instrument ids, procedure version;
- result, uncertainty, file hash.

**Maintenance log:** time, action (cleaning, panel check, levelling, sensor swap, firmware change, view change), person-independent description, and the frames affected. Every intervention is followed by a new reference frame.

**Visual processing.** Panel-normalised quantities (target DN divided by panel DN in the same frame) are computed from frames only, so they are `visual`. They may enter CO and the SCI visual side. Exposure, gain and ladder index stay `calib`.

## 10 · Hardware tiers and approximate costs

USD, approximate list-price ranges, unverified, excluding labour, tax and shipping:

| function | minimum (engineering chain) | recommended (P1 and P2 research) | reference (adds, mechanism claims) |
|---|---|---|---|
| camera, lens, computer | single-board RAW camera kit, 150–400 | machine-vision camera and lens 600–2,300; industrial PC 500–1,000 | second camera (P2 near field, or stereo) 600–2,300 |
| housing (heated window, hood) | 150–300 | 300–600 | |
| label RH/T and aspirated shield | mid-grade certified probe 500–1,000; fan-aspirated shield 500–1,200 | research-grade probe 1,500–3,000 (heated option); shield 500–1,200 | chilled-mirror hygrometer 8,000–20,000 |
| conditioning thermometer and shield | PRT or precision thermistor 100–300; second shield 500–1,200 | the same | |
| second RH probe (other make) | none | 500–1,500 | |
| radiation | silicon pyranometer 200–400 | thermopile pyranometer 600–2,500; shadow ring and diffuse unit 1,000–3,000 | sunshine pyranometer or tracker 6,000–20,000 |
| wind, rain, pressure | cup and vane 200–600; tipping bucket 150–600 | 2D ultrasonic 800–2,000 | |
| P2 surfaces and sensors | 1 plate, contact thermistor, 1 leaf-wetness sensor: 150–400 | plates and glass, IR thermometer 600–1,000, 2 leaf-wetness sensors 200–600 | |
| reference panels | matte-painted grey/black set, characterised relatively, 100–300 | outdoor diffuse-reflectance panels 1,000–5,000 | spectroradiometer calibration (rent or borrow) 1,000–5,000 |
| P1 targets | GIS and DEM distances; laser rangefinder 300–1,000 | the same plus an RTK survey if needed, 500–2,000 | |
| aerosol | none | optical particle counter 400–1,000 with Nafion dryer and pump 300–1,000 | humidity-controlled nephelometer or equivalent 20,000–80,000 |
| visibility | none | none | forward-scatter sensor 5,000–15,000 |
| logger, clock | microcontroller ADC 100–300; GNSS PPS 30–200 | research datalogger 1,500–3,000 | |
| power, storage, mast | mains and UPS 200–400; SSD 150–300; mast 300–1,500 | solar and battery if needed 800–2,500; 2 × 4 TB 300–600 | |
| **approximate total** | **≈ 3,000–8,000** | **≈ 12,000–30,000** | **≈ +40,000–150,000** |

**What each tier can show:**
- *Minimum:* chain validity, the dew signal detectable or not, radiometric stability.
- *Recommended:* the above plus P1 extinction estimates, aerosol-stratified analyses and label redundancy.
- *Reference:* mechanism claims (labels through saturation, independent extinction, hygroscopic growth).

## 11 · Initial calibration protocol

**Before deployment (bench):**
1. **Dark model.** Dark frames at every ladder exposure across the sensor temperatures reachable in the bench chamber or a fridge test: dark level and noise against (t, T_sensor).
2. **Linearity and saturation.** An exposure series on a stable diffuse LED source. The response is linear within ±1 % up to a declared DN ceiling, which caps usable pixels.
3. **Flat field and vignetting.** A uniform source (LED panel or integrating sphere), per channel.
4. **Geometry.** Checkerboard calibration for distortion, so ROIs can be mapped after small view shifts.
5. **Sensor intercomparison.** All RH/T units side by side in the same aspirated arrangement for ≥ 7 days. Salt checks at 33 % (MgCl₂), 75 % (NaCl) and 97 % (K₂SO₄). An ice-point check of the PRT.
6. **Latency.** The trigger latency is measured against GNSS PPS (§8).

**At installation:**
1. The reference frame, ROI polygons and sun-path overlay.
2. Panel reflectances:
   - *minimum tier:* relative to one panel kept indoors as a standard;
   - *reference tier:* absolute, by spectroradiometer.
3. The pyranometer is levelled and checked against the clear-sky model on the first clear day (K ≈ 1).
4. Fan tachometers are checked.
5. A 48 h representativeness comparison between the mast and the near-field targets (§4).

**During the pilot:**
- weekly cleaning, panel inspection, levelling check and clock-offset review;
- monthly salt check and latency test;
- a reference frame after every intervention;
- at removal, a repeat of the bench intercomparison, with drift between the two comparisons within certificate uncertainty (checklist A).

## 12 · Quality control and selection rules

- **Exclusion by non-image rules only.** Rows are excluded only by pre-declared rules that do not use the image: instrument fault flags, maintenance windows, gauge-detected rain intervals, a missing reference, or failed synchronisation. Every exclusion is counted and its rule recorded.
- **Image-derived QC never removes rows silently.** Lens droplets, blur, fog or dew on the window are caused by humidity. Dropping them would condition the sample on a humidity effect and bias every estimate of E2. Such flags become strata and sensitivity analyses, reported both with and without the flagged rows.
- **Lens wetness is prevented, not filtered.** The window heater holds window_temp − Td ≥ 2 K, and the hood blocks rain. A frame with the heater fault flag is excluded by a hardware rule.
- **Near saturation:** see §6. RH_implied ≥ 100 − σ_RH is a sensitivity stratum and is censored in the likelihood, never blanked (D-066).
- **Physical events.** Fog, dew and rain mornings are kept and stratified. P2 is about exactly these mornings.
- **Other faults.** Spider webs, insects and birds are caught by the daily view-shift and edge-correlation test (notebook 13) and the weekly inspection. Frames are excluded from the logged event time to the cleaning time.

## 13 · Engineering-pilot acceptance tests

The pilot passes when every test below holds over ≥ 4 weeks that include dew mornings and dry days:
1. Every checklist A test: shield, thermometer agreement, certificate drift, near-saturation traceability, clock ≤ 1 s, daily view check, levelled pyranometer.
2. **Radiometric stability.** The panel-normalised reflectance of the grey panels is constant within ±2 % across illumination (clear and cloudy, solar elevation > 15°) at a fixed ladder exposure.
   - *Correction to checklist draft 3:* at fixed exposure the raw DN of a fixed target scales with irradiance by design. It is the panel-normalised quantity that must be stable.
3. **P1 detectability.** The contrast–distance relation of the far targets gives a σ estimate whose day-to-day precision on stable clear days is ≤ 25 % of the expected σ_dry. Otherwise the P1 geometry is insufficient at this site.
4. **P2 detectability.** On dew mornings (leaf wetness on, T_surface ≤ T_dew from the sensors), the near-field plate reflectance or texture changes beyond its dry-morning range. This is a measurement check, not a test of E2.
5. **Data completeness.** ≥ 95 % of scheduled frames and ≥ 98 % of sensor minutes are present, and every gap is explained in the maintenance log.

## 14 · Decisions that need independent review (escalation candidates)

1. **One camera or two.** P1 wants infinity focus, a narrow field and long paths. P2 wants near focus on small surfaces. One wide camera compromises both, and two cameras double the radiometric calibration. Recommendation: **two cameras at the recommended tier, one at the minimum tier**, with P2 surfaces placed at the far edge of depth of field.
2. **Site.** The pathways pull in different directions. P1 needs long homogeneous sightlines, and P2 needs dew-prone open ground. Both need permission, power and weekly access. The choice depends on sites available to the project, which this document cannot know. The admission criteria (§4) are the screening tool.
3. **Surface temperature in C.** Conditioning on T_surface in a P2-specific estimand (E2_P2 = I(D; V | C, T_surface)) asks whether the image says more than the surface-cooling state. Leaving it out lets the image act as a surface thermometer. It is not a mediator of humidity, because it is driven mainly by radiation and wind, though latent heat of condensation couples them slightly. The proposal is to treat it as `met`, allowed in a declared E2_P2 context only.
4. **The near-saturation label.** A heated probe in the recommended tier or a chilled mirror in the reference tier. This is open from checklist draft 3 and decides whether P2 labels are valid on the mornings P2 needs.
5. **Budget tier.** A minimum-tier pilot first, then upgrade; or the recommended tier from the start, which avoids a second commissioning.
6. **How the null will be calibrated (D-085).** M1.4 could not certify a simulated CRT sampler on single-site data at the 0.10 tolerance, and the shift null fails under CPER-like persistence. The options:
   - (a) replication across independent seasons and sites, which favours a second site over a longer single-site record;
   - (b) a sampler fitted on far more independent data than CPER gives;
   - (c) negative controls: visual features of a target that cannot respond to moisture (for example, a sealed or indoor reference panel in frame) passed through the same test, giving an empirical false-positive rate on real data. They are only as good as the target's immunity to moisture and to the illumination pathways shared with the scene.

   This choice affects site count and duration, so it belongs before the budget tier.

## 15 · Assumptions and limitations

- Path-averaged humidity (P1) is represented by a point measurement. This holds only over homogeneous terrain, and the representativeness error is not quantified until a second humidity point (reference tier) or a visibility sensor exists.
- Low-cost optical particle counters undercount small particles and respond to RH. Even dried, they characterise aerosol loading only coarsely.
- The panels weather. Their reflectance drift must be tracked, and an unreported drift would mimic a slow visual trend.
- Development data from this pilot never enter confirmatory evaluation (metadata policy, data stages).
- The costs are approximate and unverified. Nothing is ordered until the site, tier and camera decisions (§14) are made.
