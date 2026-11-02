# Continued NEON statistics or a controlled field station: decision analysis

**Status:** written for review 7 item 4 and discussion 8 (D-084). It compares where the next research effort has the higher expected scientific value. It does not stop the bounded M1.4 experiment, which was authorised separately (D-081).

## 1 · The question

The research aim is a defensible test of E2 = I(D; V | C), with D = T − Td and C the clock, season and temperature context, and eventually a camera-only estimator. Which of these moves the project closer?

- **A.** More statistical work on NEON CPER: further sampler, interval and context repairs on the 2020–2023 record, then the reserved 2024–2025.
- **B.** An independent, controlled field station (M2A design, then an engineering pilot, then multi-season collection).

The options are not exclusive. The question is where the next units of effort go.

## 2 · What NEON CPER can and cannot identify

| limitation | evidence | consequence for E2 |
|---|---|---|
| **Automatic camera processing.** Auto-exposure, auto white balance, in-camera haze compensation, JPEG compression, a burned-in overlay; no RAW. | D-042, notebook 07; exposure alone gains −0.004 to +0.017 nats/row (notebook 18) | Image features mix scene radiance with an acquisition state that tracks cloud and illumination. A positive gain cannot be attributed to moisture optics, and a null cannot exclude it, because processing may destroy contrast (the haze compensation). |
| **Four seasons.** | the season-cluster interval under-covers (notebook 16, A4: 0.71–0.91); per-season gains +0.020, +0.022, −0.025, +0.073 | There is no valid interval for G. Between-season heterogeneity cannot be separated from estimation noise. |
| **Heterogeneous phenology.** | 2022's greenness hardly declines (notebook 17 §5), and 2022 is the only negative season | Vegetation state competes with optics as a pathway, and changes between years in ways C does not describe. |
| **Reference-sensor uncertainty.** | passive shield radiation error +0.9 to +1.3 K in calm, high sun (notebook 08); HMP155 RH uncertainty changes by year (1.18–3.09 %, D-073); near-saturation blanking up to 36 % (notebook 13); label and context share a unit (D-020 exception) | The label carries a radiation-coupled error that the image can predict, which produces positive E2 in a world without visual moisture information (notebook 01 §9). |
| **Repeated method development on one site.** | 2023 informed features, regions, context and protocol (notebooks 07–12); 2020–2023 informed the sampler audit and M1.4 | Any later CPER test is a same-site temporal check of a method tuned there. It is not independent replication (D-080). |
| **Power.** | a planted ≈ 0.03-nat component was detected in 0.28 of datasets (notebook 17) | Even with a valid sampler, effects of the size observed are unlikely to be detected. A non-detection would be uninformative (D-082). |
| **Fixed scene geometry.** | one oblique grassland view, no surveyed targets, unknown distances | Extinction cannot be estimated, so the most physically grounded pathway (P1) is not testable. |

**What NEON still provides:**
- a realistic, free, multi-year record of image–weather dependence on which inference methods can be stress-tested;
- the real-image null worlds of M1.4;
- reserved seasons for a frozen same-site temporal check of an estimator developed elsewhere.

## 3 · What a controlled station changes, and what it does not

| problem at NEON | at a controlled station | still unresolved |
|---|---|---|
| automatic exposure and processing | RAW, fixed exposure ladder, no in-camera processing (M2A §4) | physical illumination confounding: sun angle, cloud, diffuse fraction. Fixed exposure removes only the camera's response to them. |
| no extinction geometry | surveyed dark targets at known distances, in-scene reference panels (P1 module) | path-average humidity is not point humidity, so representativeness error remains |
| shared, passively shielded label | independent aspirated label and conditioning units, salt checks and intercomparison (M2A §5) | near-saturation accuracy needs a heated probe or a chilled mirror (reference tier) |
| no wetness or surface reference | leaf-wetness and surface-temperature sensors, with T_surface ≤ T_dew modelled (P2 module) | wetness is a mediator, not a label; it must not enter C |
| no aerosol information | optical PM with a dried inlet (recommended tier) | low-cost optical sensors are RH-sensitive and size-limited. Hygroscopic claims need the reference tier. |
| one site, tuned on | a new site and camera, with development weeks fire-walled from confirmatory blocks (metadata policy, data stages) | one site is still one climate. External validity needs a second site. |
| four seasons, no interval | a design sized by the power of whichever protocol is validated | E2 estimation still needs several independent seasons. The engineering pilot (weeks) cannot provide them. |

## 4 · Comparison

| criterion | A: continued NEON statistics | B: controlled station |
|---|---|---|
| Can it identify E2 against the exposure and illumination pathways? | **No.** Acquisition state is entangled with scene radiance by design, and there is no radiometric reference. | **Partly.** Acquisition state is removed. Illumination is measured (pyranometer, diffuse split, panels) and can enter C (E2_illum), although it is not removed. |
| Can it test a named physical mechanism? | No: no distances and no wetness reference. | Yes, for P1 (extinction vs distance) and P2 (dew where T_surface ≤ T_dew), at the module tiers. |
| Validity of inference | Blocked unless M1.4 passes. Even then, low power and no valid interval. | The same inference problems recur (persistence, seasons), but with known dependence sources and a design sized for them. |
| Independence of evidence | Eroded by repeated development on CPER. | A new site and camera; development and confirmatory periods are separated from the start. |
| Relevance to a camera-only estimator | Domain: processed JPEG, auto-exposed, oblique grassland. The domain shift to a RAW station is unquantified. | The deployment camera and the research camera can be specified together; site calibration is allowed and disclosed. |
| Time to the first informative result | Immediate, but the information is bounded (descriptive gains). | Weeks for measurement-chain validity (engineering pilot); seasons to years for E2. |
| Cost | Compute and analyst time only. | Hardware from roughly USD 3k (minimum) to 15–30k (recommended), plus installation and maintenance (M2A §10). |
| Main risk | Overfitting the statistics to one dataset: the failure mode review 7 warned about. | Site access, maintenance, instrument faults, and a slow accumulation of seasons. |

## 5 · Expected value

**For A**, each further NEON repair can at best produce a valid but underpowered exploratory test on a site that has informed the method.
- A positive result would still be confounded with exposure and illumination (notebook 18).
- A negative result would be uninformative at the achievable power.
- The posterior on E2 barely moves either way, so the value of the information is low, and it falls with each iteration as the remaining CPER data lose independence.

**For B**, the engineering pilot produces information that is needed under every hypothesis:
- whether the measurement chain (shielding, synchronisation, radiometric stability, near-saturation labels) works;
- whether the P1 contrast–distance signal and the P2 dew signal are measurable above camera noise.

These are preconditions for any confirmatory E2 test and for a camera-only estimator, and NEON cannot supply them.

**Decision (D-084):**
1. Effort moves to B (M2A design, then the engineering pilot once equipment is approved).
2. NEON statistical development is limited to the single bounded M1.4 experiment. If M1.4 fails or is underpowered, NEON Q0 development closes for this phase.
3. CPER 2024–2025 stay reserved for a frozen same-site temporal check of an estimator developed on station data, described as such. A separate camera and site are needed for external-site evaluation.

## 6 · What would change this decision

- **M1.4 is suitable and reaches ≥ 0.80 power at 0.05 nats.** An exploratory CPER Q0 then runs (D-082). Even a positive result would not resolve the exposure and illumination pathways, so B stays primary.
- **No suitable site, or no funding for at least the minimum tier, within the M2A horizon.**
  - Reconsider public sources with RAW or fixed-exposure cameras and co-located aspirated references, if any exist.
  - This is a search task, not further NEON statistics.
- **The engineering pilot shows camera noise exceeding the expected P1 and P2 signals.** The design or the pathway must change before multi-season collection.
