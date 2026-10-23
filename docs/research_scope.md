# Research scope

## Question

Under which physical and meteorological regimes can near-surface moisture be inferred from passive RGB observations of a fixed scene, and how much information do the images carry **beyond** clock, season, air temperature, aerosol state and camera effects?

The project began as image → relative-humidity regression with a heatmap of contributing scene regions. Two problems ended that framing. Attribution shows what a model used, not what physically carries moisture information: a flower can be "important" because it encodes time of day, season or site. And RH is mostly invisible to RGB; a camera receives indirect optical consequences of the atmospheric state (haze, condensation, wetness, cloud, illumination), many of which are also produced by things other than humidity. The question is therefore an inverse problem under partial observability, and the first deliverable is a measurement of identifiability, not a predictor.

## What results can and cannot support

| evidence | can support | cannot support |
|---|---|---|
| synthetic worlds (notebooks 00–01) | correctness of estimators, splits, leakage guards; failure modes and their diagnostics | any statement about real weather |
| public camera + station data | pipeline function; exploratory context-conditioned skill; join quality | calibrated extinction, hygroscopic mechanisms (JPEG, unsurveyed depth, distant stations) |
| development field pilot | measurement-chain validity (shielding, lag, sync, radiometry) | confirmatory claims (pilot data must not become test weeks) |
| confirmatory field data | conditional visual information E2 with uncertainty; mediator tests | generality beyond the sites and seasons sampled |

Three levels must not be conflated: *visually predictable* (a model scores well), *physically identifiable* (information survives conditioning on legitimate non-visual context), *causally mediated* (a specific optical pathway carries it, shown by intervention or independent mediator measurement).

## Targets

- **Label quantities** come from an independent reference unit: `temp_ref_c`, `rh_ref_pct` (over liquid water) → `td_ref_c`, `d_ref_k = T − Td` (Magnus, WMO-No. 8 coefficients; [mathematical_formulation.md](mathematical_formulation.md)).
- **`D` is the primary latent target** for scientific contrasts. Notebook 00 establishes that, for a fixed temperature, `D` and RH are bijective (`ln(RH/100) = −BCD/((C+T)(C+T−D))`), so information conditioned on that temperature is target-invariant. The choice matters for unconditioned questions (E1, camera-only) and for which predictive family is well specified. `D` is not water content: at fixed vapour pressure it rises one-for-one with temperature. `Td` (or vapour pressure) is the absolute-moisture quantity.
- **Near saturation, labels are censored**: with a ±σ %RH probe, readings above `100 − σ` %RH bound `D` from above but do not resolve it (notebook 00 §5).

## Settings

| setting | inputs at inference | purpose | a positive result means |
|---|---|---|---|
| **SCI-E1** | — (evaluator conditions on clock/season) | `I(D; V | hour, season)` | images add to clock/season; may be visual thermometry |
| **SCI-E2** (primary) | — (evaluator conditions on clock/season + independent T, T history) | `I(D; V | hour, season, T)` | images carry moisture information beyond temperature and clock |
| **SCI-E3** (diagnostic) | — (+ dried-aerosol reference) | `I(D; V | hour, season, T, A_dry)` | information beyond dry aerosol loading; not proof of hygroscopic mediation |
| **CO** camera-only | frames, relative frame times, static camera/site calibration | deployable camera product | usable camera-only skill against a declared baseline |
| **TA** temperature-assisted | CO + live thermometer (and its history) | practical product, benchmark | skill of camera + thermometer; **not** camera-only |
| **CTX** contextual | TA + clock/season + non-humidity meteorology | performance ceiling | practical ceiling; not evidence of visual identifiability |
| **TEACHER** | CTX + dried aerosol + measured mediators, **training only** | privileged supervision for a CO student | nothing by itself; judged through the student |

SCI settings are statistical contrasts, not products: the evaluator sees the conditioning variables, the camera-only model does not.

### Field-role matrix

✓ = may be a model input; – = never. Roles are declared per field in [`schemas/sample.schema.json`](../schemas/sample.schema.json) and enforced by `visual_hygrometry.policy` ([metadata_policy.md](metadata_policy.md)).

| role | examples | CO | TA | CTX | TEACHER | SCI context | SCI visual side |
|---|---|---|---|---|---|---|---|
| `visual` | frames, `vis_*` image features | ✓ | ✓ | ✓ | ✓ | – | ✓ |
| `acq` | visual look-back `window_s`, relative frame times | ✓ | ✓ | ✓ | ✓ | – | ✓ |
| `clock` | local hour, day of year, Fourier bases, solar elevation | – | – | ✓ | ✓ | ✓ | – |
| `temp_cond` | `temp_cond_c` (conditioning unit) | – | ✓ | ✓ | ✓ | E2, E3 | – |
| `temp_hist` | causal statistics of `temp_cond_c` | – | ✓ | ✓ | ✓ | E2, E3 | – |
| `met` | wind, rain, shortwave, pressure | – | – | ✓ | ✓ | – | – |
| `aerosol_dry` | PM after a verified dryer | – | – | – | ✓ | E3 | – |
| `mediator` | visibility, leaf wetness, road state | – | – | – | ✓ | – | – |
| `label`, `label_qc` | `rh_ref_pct`, `temp_ref_c`, `td_ref_c`, `d_ref_k`, censor flags | – | – | – | – | – | – |
| `forbidden` | undried PM, present-weather codes, NWP/reanalysis RH | – | – | – | – | – | – |
| `id`, `time`, `provenance`, `calib` | ids, raw timestamps, sensor ids, hashes, exposure/gain | – | – | – | – | – | – |

Mediators are excluded from SCI conditioning because conditioning on a variable that humidity causes blocks the pathway being measured. Exposure, gain and white balance (`calib`) are used to normalise radiance, never as features: an auto-exposure ladder encodes solar time.

## What counts as a camera-only RH prediction

A **CO-RH** prediction is a predictive distribution `p(RH | frames, Δt, static calibration)` whose inference inputs pass the `co` policy. Its internal structure is free: a direct RH head, or a joint `p(T, D | V)` pushed through `RH = g(T, D)` with the temperature *also predicted from the images*, are both camera-only. A visually predicted `D` combined with a measured temperature is **TA**, whatever it is called.

Site calibration from historical measured data is allowed and must be disclosed; calibration periods must be disjoint from evaluation blocks. CO skill is reported against an unconditional site-climatology baseline **and** a clock-only reference, so that the share of CO skill attributable to the image acting as a clock is visible. Which CO-RH construction to adopt is open and will be decided by Exp 2a/2b evidence; until then the scientific student is `p(D | V)` and CO-RH is reported as pending.

## Outcomes after Exp 2a

- **GO**: E2 lower confidence bound above the pre-declared practical threshold on confirmatory blocks, positive controls recovered, measurement chain validated.
- **MODIFY**: E1 > 0 but E2 ≈ 0 (images act as thermometer/clock), or labels/sensors inadequate for the regime.
- **STOP / negative bound**: E2 upper bound below the threshold with demonstrated power and passing positive controls.

The threshold (0.05 nats per sample was used illustratively) is not fixed; it needs a power analysis on the real dependence structure (notebook 01 §10 gives the synthetic version).

## Open assumptions

1. A fixed camera with stable optics and radiometry is available or can be built; mobile/handheld imagery is out of scope.
2. An independent, aspirated reference unit can be co-located within the camera's air volume; shared-sensor public data carry a documented coupling (notebook 01 §9).
3. Day (or week) blocks are close enough to independent units for bootstrap inference; synoptic persistence may require longer blocks.
4. The conditional distribution of `D` is adequately modelled by a heteroscedastic Gaussian away from saturation; censoring is handled by the likelihood, not by dropping rows.
5. A dried-aerosol reference is feasible at the chosen site (unverified; E3 is diagnostic only until it is).
6. Clock/season context is sufficient to absorb solar-geometry effects; residual-by-context diagnostics must show it.
