# visual_hygrometry

Can a fixed camera observe near-surface moisture, and how much does it see **beyond** what clock, season, air temperature, aerosol state and camera effects already explain?

The project treats this as an identifiability problem, not as image-to-humidity regression. The primary estimand is the conditional mutual information `E2 = I(D; V | hour, season, T)` between images `V` and the dew-point depression `D = T − Td`, estimated by the held-out log-score contrast of matched probabilistic models. Camera-only (CO), temperature-assisted (TA) and contextual (CTX) predictors are separate products with separate input contracts ([docs/research_scope.md](docs/research_scope.md)).

## Current stage: M2A field-pilot design (M1.4 closed NEON Q0)

| piece | where | status |
|---|---|---|
| scope, settings, field-role matrix | [docs/research_scope.md](docs/research_scope.md) | drafted |
| leakage policy | [docs/metadata_policy.md](docs/metadata_policy.md), `src/visual_hygrometry/policy.py`, [configs/inference_settings.yaml](configs/inference_settings.yaml) | enforced, tested |
| data contracts | [schemas/](schemas/) (`sample`, `frame`, `sensor`) | drafted; site/calibration schemas pending |
| thermodynamics | `thermo.py`, [notebooks/00](notebooks/00_thermodynamics_and_synthetic_data.ipynb) | validated against steam tables |
| blocked splits, purging | `splits.py` | tested |
| information estimator | `scoring.py`, `synthetic.py`, [notebooks/01](notebooks/01_information_estimator.ipynb) | first validation (kept as record, including failures) |
| revised inference, families, censoring | `inference.py`, `scoring.py`, [notebooks/03](notebooks/03_inference_and_density_revision.ipynb), [addendum](docs/m0_decision_addendum.md) | 7/8 held-out criteria pass; A5 (context capacity) failed |
| context capacity, tail-robust scoring | [notebooks/04](notebooks/04_context_capacity.ipynb), [notebooks/05](notebooks/05_tail_robust_scoring.ipynb), `worlds.py` | zero-information test and point estimate pass fresh validation; effect-size interval open ([review](reviews/m0_revision2_review.md)) |
| public data | [notebooks/02](notebooks/02_public_data_audit.ipynb), [notebooks/07](notebooks/07_neon_feasibility_HARV_2023-07.ipynb), `neon.py` | NEON HARV July 2023 joined (clock verified to 0 s); label radiation error and near-saturation plateau found; feasibility use only |
| permutation null under dependence, chronological gain | [notebooks/06](notebooks/06_permutation_null_and_chronological_gain.ipynb), [addendum 2](docs/m0_review2_addendum.md) | cyclic-shift test and chronological G interval pass fresh validation (ρ ≤ 0.6) |
| NEON label measurement model | [notebooks/08](notebooks/08_neon_label_measurement_model.ipynb), `neon.py` | passive shield verified; hybrid label `D_h = T_asp − Td`; high-RH stratum, no censoring (D-046) |
| coverage, image set, features, dependence | [notebooks/09](notebooks/09_neon_coverage_features_dependence.ipynb), `features.py`, [manifest](data/manifests/phenocam_hourly_2023JJA.csv) | HARV + CPER JJA 2023, 2574 hourly frames verified; strong persistence at CPER |
| exploratory visual comparison | [notebooks/10](notebooks/10_exploratory_visual_information.ipynb), [findings](docs/m1_exploratory_findings.md) | no claim; estimator unstable on real single-season data; visual projection reopened ([review](reviews/m1_exploratory_review.md)) |
| why the declared analysis failed | [notebooks/12](notebooks/12_declared_analysis_failure_diagnostics.ipynb) | HARV loss from one extrapolating seasonal basis column; declared estimates dominated by fold assignment |
| projection-free inference, synthetic validation | [notebooks/11](notebooks/11_projection_free_inference.ipynb), [decision note](docs/m1_inference_redesign.md) | **fails 4 of 9 gates** (hour × season context, persistent-information intervals, AR 0.9); point estimate unbiased and stable ([review](reviews/m1_redesign_review.md)) |
| multi-year NEON availability | [notebooks/13](notebooks/13_neon_multiyear_availability_audit.ipynb) | 2019–2023 published; camera epochs and label faults identified; nothing bulk-downloaded |
| solar context, dependence-aware null, adequacy auditors | [notebooks/14](notebooks/14_solar_context_and_dependence_aware_inference.ipynb), `suite.py`, [statistical note](docs/m1_statistical_note.md) | development only: CRT null controls Type I in every development world, the shift test does not under persistence; intervals under-cover |
| CPER 2020–2023 acquisition and QC | [notebooks/15](notebooks/15_cper_2020_2023_acquisition_audit.ipynb), [plan](docs/cper_2020_2023_plan.md) | plan frozen; labels and camera state audited; imagery not downloaded |
| fresh validation of the solar protocol | [notebooks/16](notebooks/16_fresh_validation_solar_protocol.ipynb) | **5 of 7 gates pass**: CRT Type I 0.02–0.08 in ten nulls, power ≥ 0.83, unbiased and stable estimates, repair diagnostic valid; season-cluster interval under-covers (0.71–0.91) and the context-only challenger fails ([review](reviews/m1_solar_protocol_review.md)) |
| CPER 2020–2023 image verification, CRT sampler audit | [notebooks/17](notebooks/17_cper_image_verification_and_sampler_audit.ipynb), [manifest](data/manifests/phenocam_hourly_CPER_2020-2022JJA.csv) | images complete, clocks verified from the burned-in overlay; **sampler not suitable** on real features (within-day persistence, hour-dependent scale, heavy tails); no real-data Q0 ([review](reviews/m1_real_sampler_review.md)) |
| CPER per-season predictive gains | [notebooks/18](notebooks/18_cper_per_season_predictive_gains.ipynb) | descriptive only: +0.020 / +0.022 / −0.025 / +0.073 nats/row (2020–2023); fragile to refitting, partly shared with auto-exposure |
| M1.4 bounded CRT sampler experiment | [plan](docs/m14_sampler_experiment_plan.md), [notebooks/19](notebooks/19_m14_sampler_synthetic_validation.ipynb), [notebooks/20](notebooks/20_m14_cper_sampler_reaudit.ipynb), `samplers.py` | **closed** (D-085): no candidate held level within the 0.10 tolerance at the required precision (P pooled 0.065, R 0.079); no misspecified sampler showed demonstrated inflation, so the audit is unvalidated; real labels not read; NEON Q0 development ends for this phase |
| NEON or a controlled station | [docs/neon_vs_field_decision.md](docs/neon_vs_field_decision.md) | effort moves to the field station; NEON stays a methods dataset (D-084) |
| field pilot (M2A, primary) | [docs/m2a_pilot_design.md](docs/m2a_pilot_design.md), [checklist](docs/field_pilot_checklist.md) | design draft 1: shared acquisition core + P1 (extinction) and P2 (dew) modules, three tiers, calibration and QC; nothing ordered |
| maths | [docs/mathematical_formulation.md](docs/mathematical_formulation.md) | |

Nothing here is evidence that RGB imagery carries moisture information. The estimator was validated on synthetic data with known truth only, and the first real-image comparison (notebook 10) supports no claim.

## Setup

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -e ".[dev]"
```

On Linux/macOS use `.venv/bin/python`. Notebooks use the environment's `python3` kernel.

## Run

```bash
.venv/Scripts/python.exe -m pytest -q
```

```bash
cd notebooks && PYTHONUTF8=1 ../.venv/Scripts/jupyter-execute.exe --inplace 00_thermodynamics_and_synthetic_data.ipynb 01_information_estimator.ipynb 02_public_data_audit.ipynb 03_inference_and_density_revision.ipynb 04_context_capacity.ipynb 05_tail_robust_scoring.ipynb 06_permutation_null_and_chronological_gain.ipynb 07_neon_feasibility_HARV_2023-07.ipynb 08_neon_label_measurement_model.ipynb 09_neon_coverage_features_dependence.ipynb 10_exploratory_visual_information.ipynb 11_projection_free_inference.ipynb 12_declared_analysis_failure_diagnostics.ipynb 13_neon_multiyear_availability_audit.ipynb 15_cper_2020_2023_acquisition_audit.ipynb
```

```bash
cd notebooks && OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONUTF8=1 ../.venv/Scripts/jupyter-execute.exe --inplace --timeout=-1 14_solar_context_and_dependence_aware_inference.ipynb 16_fresh_validation_solar_protocol.ipynb 17_cper_image_verification_and_sampler_audit.ipynb 18_cper_per_season_predictive_gains.ipynb 19_m14_sampler_synthetic_validation.ipynb 20_m14_cper_sampler_reaudit.ipynb
```

`PYTHONUTF8=1` matters on Windows: `jupyter execute` otherwise opens notebooks with the locale code page. Notebook 01 takes about 4 minutes, notebook 03 about 5, notebooks 04 and 05 about 20 minutes each and notebook 06 about 75 minutes on 16 parallel workers; notebook 07 downloads ~80 MB on first run; notebooks 08–09 need the NEON tables for HARV and CPER June–August 2023 and the 2574 hourly PhenoCam frames (1.22 GB) in `data/raw/`; notebooks 09 and 10 together take roughly 15 minutes, notebook 11 about 2.5 hours on 16 workers, notebook 12 about 20 minutes; notebook 13 downloads ~230 MB of tower data and 139 midday frames on first run; notebook 14 takes about 3 hours and notebook 16 about 9 hours on 16 workers (single-threaded BLAS per worker is about 7× faster than the default); notebook 15 downloads the CPER 2020–2023 tower tables and 3,792 `.meta` files; notebook 17 needs the 3,792 hourly CPER JPEGs of 2020–2022 (1.42 GB, checked against their manifest) and takes about 1 hour, notebook 18 about 6 minutes; notebook 19 about 9 hours on 18 workers (cached per section in `data/interim/m14/`), and notebook 20, which reads notebook 19's summary, seconds when the outcome is closed; notebook 02 queries the NEON and PhenoCam APIs live. A NEON API token, if needed, is read from `NEON_TOKEN` in `.env`.

## Layout

```text
configs/   inference settings (roles each setting may consume)
docs/      scope, policy, mathematics, decision log
schemas/   JSON-schema data contracts with x-role / x-derived-from annotations
src/visual_hygrometry/
           thermo.py  data.py  policy.py  splits.py  scoring.py  inference.py  synthetic.py  worlds.py  neon.py  features.py  suite.py  samplers.py
notebooks/ 00 thermodynamics + synthetic world, 01 first estimator validation, 02 public-data audit,
           03 revised inference / predictive families / censoring with a held-out validation suite,
           04 context capacity (flexible context basis, visual projection, adequacy diagnostics),
           05 tail-robust scoring (defensive Gaussian, common support) with a fresh validation suite,
           06 permutation null under persistence/regimes/seasons/missing frames, chronological gain,
           07 NEON feasibility (HARV, July 2023), 08 NEON label measurement model (HARV, CPER),
           09 coverage / verified image set / features / temporal dependence, 10 exploratory visual comparison,
           11 projection-free inference with a new synthetic validation suite, 12 diagnostics of the notebook 10 failure,
           13 multi-year NEON availability audit, 14 solar context and dependence-aware inference (development),
           15 CPER 2020–2023 acquisition audit, 16 fresh validation of the solar-context protocol,
           17 CPER image verification and real-image CRT sampler audit, 18 CPER per-season predictive gains,
           19 M1.4 synthetic validation of the repaired CRT samplers, 20 M1.4 re-audit on the CPER features
tests/     pytest suite (thermodynamics, policy canaries, splits/purging, scores, estimator bias)
data/      local data area; raw files are ignored by Git (data/README.md)
```

## Data sources and licences

NEON tower products (DP1.00098.001 relative humidity, DP1.00003.001 triple-aspirated air temperature, DP1.00023.001 shortwave radiation, DP1.00001.001 2D wind, DP1.00033.001 phenology images; National Ecological Observatory Network, Battelle) and the PhenoCam Network archive (CC BY 4.0). Licence of NEON data products to be confirmed before redistributing derived tables.
