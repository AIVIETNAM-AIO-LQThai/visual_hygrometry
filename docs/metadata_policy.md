# Metadata and leakage policy

Any variable that encodes the label, its descendants, or information the deployed product will not have can make a model look like a hygrometer. This policy decides which fields may enter which model, and it is enforced in code before any array reaches a model: `visual_hygrometry.policy.select` (deployment settings, teacher) and `policy.select_sci` (matched information contrasts).

## Roles

Each field of the aligned observation table ([`schemas/sample.schema.json`](../schemas/sample.schema.json)) declares `x-role` and, if computed from other fields, `x-derived-from`. The settings that may consume each role are listed in [`configs/inference_settings.yaml`](../configs/inference_settings.yaml) and summarised as the field-role matrix in [research_scope.md](research_scope.md).

| role | meaning | rule |
|---|---|---|
| `id` | sample, site, camera identifiers | grouping/splitting only; never a feature (site/day ids memorise weather) |
| `time` | UTC timestamp, site UTC offset | only through derived `clock` fields |
| `visual` | frames and features computed from frames only | CO and above; SCI visual side |
| `acq` | relative frame timing, visual look-back | with `visual` |
| `calib` | exposure, gain, aperture, white balance, resolution | radiometric normalisation only, never a feature |
| `clock` | local hour, day of year, fixed Fourier bases, solar elevation | CTX, TEACHER, SCI context |
| `temp_cond` / `temp_hist` | conditioning thermometer and its causal history | TA and above; SCI E2/E3 context |
| `met` | wind, rain, shortwave, pressure | CTX, TEACHER |
| `aerosol_dry` | PM after a verified dryer | TEACHER; SCI E3 context |
| `mediator` | humidity-affected physical states (visibility, leaf wetness, road state) | TEACHER inputs or auxiliary targets; never conditioning |
| `label` / `label_qc` | reference RH, T, Td, D; censor flags, label windows | targets only |
| `provenance` | sensor ids, hashes, sources | audits only |
| `forbidden` | undried optical PM, present-weather codes, NWP/reanalysis humidity | nowhere; each carries an `x-reason` |

## Enforcement layers

| # | layer | failure it prevents | test |
|---|---|---|---|
| 1 | closed-world registration: unregistered columns are refused when requested and reported when skipped | ad-hoc columns (e.g. a pasted station RH) entering features | `test_label_canary_refused_everywhere` |
| 2 | role permission per setting | e.g. clock in CO, temperature in CO, met in TA | `test_role_matrix`, `test_humidity_coded_shortcuts_refused` |
| 3 | lineage: any field transitively derived from a `label` field is refused regardless of declared role | lagged RH, RH-derived indices mis-declared as `met` | `test_lineage_overrides_declared_role` |
| 4 | sensor roles: temperature features from the label's own unit require `allow_shared_sensor=True` and are reported | common-mode error between label `D` and conditioning `T` | `test_shared_sensor_requires_explicit_permission` |
| 5 | phase: training-only settings refused at inference | teacher inputs at student inference | `test_teacher_is_training_only` |
| 6 | empirical audit: single-feature correlation ratio η² with the target ≥ 0.95 is refused | label-equivalent columns mis-declared as legitimate (e.g. `vis_canary = D + noise`) | `test_disguised_canary_caught_by_audit` |
| 7 | matched SCI design: context columns identical in both models, roles split context/visual | capacity or information asymmetry between `q(D|V,C)` and `q(D|C)` | `test_sci_contrast_is_matched` |

Layers 1–5 and 7 are exact. Layer 6 is a heuristic net: it catches near-copies of the label but not, for instance, a coarse humidity code (that is what layers 1–3 are for). Overriding it requires an explicit argument and a decision-log entry.

## Leakage the column policy cannot see

- **Pixels**: road and webcam images often burn in timestamps and even station readings (temperature, sometimes humidity). Overlays are masked before feature extraction and the frame manifest records `overlay_masked`; each public source gets a visual audit of sample frames.
- **File metadata**: EXIF timestamps, filenames with dates, and per-frame exposure are not features; frame ordering inside a sample must not encode absolute time for CO.
- **Camera state**: auto-exposure, IR-cut switching, internal heaters and lens droplets correlate with time and humidity; they are QC flags (`frame.qc`), and CO features must be invariant to them or stratified by them.
- **Processing fitted on test data**: scalers, PCA, colour normalisation, scene calibration, variance models and teachers are fitted inside training folds only. The Fourier clock basis is data-independent by construction.

## Sensor roles

Where possible the label (`ref_sensor_id`) and the conditioning thermometer (`cond_sensor_id`) are different, independently shielded and aspirated units, and the analysis is repeated with roles swapped. Agreement between two units does not reveal their common-mode radiation error. Notebook 01 §9 shows why this matters: a radiation error that the image can predict (sunshine) produces a positive E2 in a world with no visual moisture information. Public single-station data are usable only with `allow_shared_sensor=True` and this limitation stated with every result.

## Time

- `time_utc` is the keyframe time. Label quantities are averaged over `label_window_s` centred on it; all feature windows are causal, `(t − w, t]` (`data.causal_mean`).
- A sample's **dependency interval** spans its longest look-back and its label window. Training rows whose interval comes within the embargo of any evaluation interval are purged (`splits.purge`). Notebook 01 §1 quantifies the cost: long look-backs with interleaved day folds purge both neighbours of every test day.
- **Independent units** are local calendar days by default; week blocks when synoptic persistence exceeds a day. Bootstrap and permutation procedures resample these units, never rows.

## Data stages

| stage | use | firewall |
|---|---|---|
| public dry run | pipeline, join audit, exploratory contrasts | never cited as confirmatory evidence |
| development pilot | measurement-chain fixes, hyper-parameters, feature design | weeks used here are excluded from confirmatory testing |
| calibration | site/camera radiometric calibration, CO site calibration | disjoint from evaluation blocks, disclosed |
| confirmatory | pre-declared estimand, splits and threshold | touched once, after the analysis plan is frozen |

Fold assignments, preprocessing versions and data snapshots are recorded alongside every reported number.

## Teacher-specific rules

Teacher soft targets are produced out-of-fold. Teacher inputs exclude anything target-equivalent (`label`, `forbidden`), and undried PM stays forbidden even for the teacher until Exp 2b decides otherwise (decision D-010). A teacher can only improve a camera-only student's estimation efficiency; it cannot create information absent from the image.
