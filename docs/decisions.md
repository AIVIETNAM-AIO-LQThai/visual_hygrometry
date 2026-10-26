# Decision log

Status: **adopted** (in force, evidence cited), **provisional** (in force until the named check), **open** (undecided), **rejected** (tried and dropped, kept for the record).

| id | decision | status | evidence / revisit when |
|---|---|---|---|
| D-001 | Primary scientific estimand is `E2 = I(D; V | hour, season, T)`; E1 and E3 are reported beside it, never inferred from it. `E1 − E2` and `E3 − E2` have no fixed sign. | adopted | math §2; nb00 §6; nb01 §4 |
| D-002 | Estimator: cross-fitted held-out log-score contrast of a matched joint model `q(D|V,C)` vs context model `q(D|C)` (same family, same context columns, same tuning); replaces score stacking on a black-box summary. Called an *estimate of a contrast*, never an unbiased CMI estimate. | adopted | math §3 decomposition; nb01 |
| D-003 | Labels: Magnus over water with WMO-No. 8 coefficients; Murphy–Koop (2005) as accuracy reference. | adopted | nb00 §1–2: max ΔD 0.077 K, ≤ 5 % of σ_D for a ±2 %RH probe |
| D-004 | Censoring limit from the instrument specification only: `RH_c = 100 − kσ_RH`, k = 1 default, k = 2 as sensitivity. Censored rows scored with `log P(D ≤ d_c)`. | provisional | nb00 §5; revisit with the actual datasheet of each source |
| D-005 | Settings SCI-E1/E2/E3, CO, TA, CTX, TEACHER with the field-role matrix; CO excludes clock and all live meteorology; predicted D + measured T is TA. | adopted | research_scope.md |
| D-006 | Closed-world data contract with roles and lineage; empirical η² audit at 0.95 as a net for mis-declared fields. | provisional | tests/test_policy.py; the η² threshold is a heuristic |
| D-007 | Temperature features from the label's own unit require an explicit `allow_shared_sensor=True` and are reported as a limitation. | adopted | nb01 §9: a 1 K sunshine-driven error creates spurious E2 of the order of 0.05 nats |
| D-008 | Independent unit = local calendar day by default; week blocks or contiguous folds whenever look-backs cross days. Purge + 1 h embargo on dependency intervals. | provisional | nb01 §1: 24 h look-back purges ~49 % of training rows with interleaved day folds vs ~3 % contiguous / ~8 % interleaved weeks |
| D-009 | Ridge penalty selected by day-grouped inner CV (not sklearn's row-wise LOO). | adopted | policy consistency; nb01 §6 shows it does not by itself fix high-dimensional false nulls |
| D-010 | Undried optical PM forbidden for every setting including the teacher. | provisional | revisit at Exp 2b |
| D-011 | Teacher is training-only; soft targets out-of-fold. | adopted | test_teacher_is_training_only |
| D-012 | Heteroscedastic variance via log-link regression of squared out-of-fold residuals. | adopted | unit test (consistent for E[r²|x]); nb01 §7 |
| D-013 | `log r²` regression for the variance model. | rejected | estimates the geometric-mean variance under unexplained heteroscedasticity; inflated the regime contrast to 0.437 vs truth 0.227 (nb01 first run) |
| D-014 | Default predictive family for real `D`: Gaussian vs location-scale with KDE residual density vs binned categorical. | open | nb01 §7/§10: Gaussian is efficient but biased under a regime mixture (0.291 vs truth 0.227; decomposition predicts 0.328); location-scale KDE gives 0.199 at ~30 % more SD on Gaussian data. Decide on real-data residual diagnostics + review (reviews/m0_estimator_review.md) |
| D-015 | Interval for the contrast: percentile day-block bootstrap, conditional on fitted models. | provisional | nb01 §10: positive-case coverage 0.75 / 0.84 / 0.94 at 20 / 60 / 180 days (SE underestimated 21 / 13 / 3 %); null side 0–2 % false positives but coverage of 0 ≈ 0.78 at every n. Needs a correction (nested/repeated CV variance, one-sided test + separate interval, or simulation calibration) before confirmatory use |
| D-016 | Visual feature dimension must be budgeted against the number of independent days. | adopted | nb01 §6: 200 noise dimensions at 30 days turn a 0.05-nat signal into a false null under every tuning scheme |
| D-017 | First public source: NEON terrestrial towers (HMP155 label, aspirated PRT conditioning, PhenoCam RGB, same tower top). | provisional | nb02: 47 sites, median 116 months with all three; data access blocked (HTTP 403) pending an API token |
| D-018 | Practical threshold for a "meaningful" E2. | open | 0.05 nats is a placeholder; nb01 §10 gives synthetic power (MDE₈₀) per number of days; fix after real dependence structure is measured |

## After the independent review (see [m0_decision_addendum.md](m0_decision_addendum.md))

| id | decision | status | evidence / revisit when |
|---|---|---|---|
| D-015 | Percentile day-block bootstrap for the contrast. | rejected | nb03: over-conservative under null (Type I 0–1 %), under-covers effects at 60 days |
| D-019 | Q0 (any information): refitting day-block permutation test with re-projected residuals. Q1 (effect size): frozen hold-out, day-cluster t, reported as information captured by the frozen models. Q2 (meaningful): frozen lower bound vs a pre-fixed δ. | provisional | nb03 dev + validation A1–A4 pass; open: permutation Type I 0.09 in one strongly dependent dev world |
| D-020 | Confirmatory claims need an independent aspirated conditioning thermometer; label-unit temperature only as a sensitivity analysis. NEON = feasibility only until shielding, geometry, timestamps and radiation bias are verified. | adopted | review item 4; nb01 §9; nb03 V-S |
| D-021 | Exp 2a-A: ≤ 10 predefined physical/scene features; a null result does not end the study. | adopted | addendum |
| D-022 | Exp 2a-B: frozen encoder reduced to k ∈ {4, 8, 16, 32} by PCA fitted on non-evaluation days, grouped tuning. | adopted | addendum; nb01 §6 |
| D-023 | Family panel: GO requires `ls-kde+T` (1 % defensive KDE, transform rule blind to V); `gauss+T` as efficiency reference; binned (labelled as binned-D information) where censoring matters. | provisional | nb03 §4, validation A6 |
| D-024 | Censored labels: penalised Tobit fit (or binned family); dropping censored rows is not acceptable for confirmatory work. | adopted | nb03 §5, A7; unit tests |
| D-025 | Context capacity must exceed what the image can encode about context. Adopted remedy: spline-in-T + hour × T basis plus cross-fitted visual projection (`spline+proj`) in both models. | adopted for Q0 | nb04 validation B1: permutation Type I 0.033–0.060 in six fresh nulls (was up to 1.00) |
| D-027 | SD floor 0.05 in standardisation. | adopted | nb04 first dev run (edge spline columns exploded); unit test |
| D-028 | Light penalty on the context block (ctx_pen = 0.01). | rejected | nb04 dev: mixed-cue bias −1.27, P1 power 0.85 |
| D-029 | Adequacy diagnostics (`flex`, `proj`) as a substitute for context capacity. | rejected (kept as secondary check) | nb04 validation B6: 0.37–1.00 flag rates on inadequate contexts |
| D-030 | Effect size by mean held-out log score with unbounded Gaussian tails. | rejected | nb04 validation B4/B5: single rows of −117 to −130 nats at context-support edges |
| D-031 | Robust Gaussian predictive (1 % Cauchy(μ, 4σ) mixture) and common-support scoring (0.5–99.5 % training box of hour, T; excluded share reported). | adopted | nb05 validation C1, C3, C4, C6, C7 pass; worst row −4.2 nats |
| D-032 | Frozen hold-out one-sided test for Q0. | rejected | nb05 validation C2: 0.167 in a cubic null |
| D-033 | Interval and estimand for the effect size (frozen captured information vs E2 on the support). | **open, review requested** | nb05 validation C5: frozen interval covers its target 0.91–0.93, E2 only 0.75–0.82 in mixed cues; reviews/m0_revision2_review.md |
| D-026 | η² leakage audit uses average ranks (row-order invariant, ties share a bin). | adopted | test_eta2_ignores_row_order_and_keeps_ties_together |

## After independent review 2 (see [m0_review2_addendum.md](m0_review2_addendum.md))

| id | decision | status | evidence / revisit when |
|---|---|---|---|
| D-034 | Estimands: E2 scientific; G(n_fit) = held-out predictive log-score gain of the defined model pair fitted on n_fit days (operational effect size for M1); permutation test = exploratory zero-information test, not a bound on E2. | adopted | review 2 |
| D-035 | Visual projection fitted per split on training days only (`project_splits`); null generator may use analysis-sample (C, V), never D. | adopted | review 2 item 2; test_project_splits_never_uses_test_rows |
| D-036 | Q0 null: cyclic-shift refitting permutation (shifts ≥ 7 days, enumerated), contiguous 16-day folds, 3-day purge, strata at declared breaks; validity region ρ ≤ 0.6. Day-unit permutation only for ρ ≤ 0.3. | adopted for exploratory M1 | nb06 sweep + validation V1/V2 |
| D-037 | G interval: chronological hold-out (60 % / 2-day purge / 40 %), week-cluster t. Newey–West and day clusters rejected for ≤ 30 evaluation days. | adopted for exploratory M1 | nb06 validation V3/V4 |
| D-038 | Support box q = 0.5 % kept; excluded share and support-dependent truth reported; never q ≥ 2.5 % without a sensitivity check. | adopted | nb06 §4 |
| D-039 | Robust mixture 1 % Cauchy(μ, 4σ) kept; not influential once support is restricted; log loss unbounded. | adopted | nb06 §4 |
| D-040 | NEON label: probe-temperature D vs hybrid D (aspirated T, probe dew point). | superseded by D-046 | nb07: probe +0.55 K by day, up to +2 K |
| D-041 | Near-saturation censoring for HMP155 labels. | superseded by D-046 | nb07: no reading above 99.02 % RH; per-minute rule censors 5 minutes, specification rule 3.3 % |
| D-042 | PhenoCam overlay mask (three fixed rectangles, 3.1 %) applied before any visual feature; exposure and camera temperature never features. | adopted | nb07 §6–8 |
| D-043 | NEON PhenoCam imagery (auto-haze, AGC, JPEG) is not used for extinction-mechanism claims. | adopted | nb07 `.meta` |

## After independent review 3 (see [m1_exploratory_findings.md](m1_exploratory_findings.md))

| id | decision | status | evidence / revisit when |
|---|---|---|---|
| D-044 | Cyclic-shift null enumerates `shift_configs`: one shift k for every stratum, k ∈ [shift_min, n_min − shift_min]; the number of shifts and the attainable minimum p are reported with every p-value. | adopted | review 3 item 4; test_shift_configs_count_min_p_and_strata (31 days, shift_min 7: 18 shifts, min p 0.0526) |
| D-045 | NEON HMP155 is in a passive shield (ATBD NEON.DOC.000851 rev A and C, §6.1.1.2); no radiation or wind QC flag exists in the published RH product. | verified | nb08 §1 |
| D-046 | NEON measurement model: label `D_h = T_asp − Td_probe`; `D_probe` mandatory sensitivity; minutes with D_h < −2σ(D_h) excluded as inconsistent; RH_implied ≥ 98.3 % a sensitivity stratum, not censored. No censored likelihood for NEON labels. | adopted for exploratory M1 (supersedes D-040, D-041) | nb08 §2–5 |
| D-047 | `td_ref_c` is a permitted SCI target. At fixed conditioning temperature it carries the same information as `d_ref_k`, and it is used as a sensitivity in which T_asp enters only the context. | adopted | nb10 §2 |
| D-048 | Acquisition-only control: the `calib` role (e.g. `calib_exposure`) may enter the visual side only at SCI level `e2_acq_control`; it is never a visual feature of `e2`. | adopted | test_acquisition_state_only_in_the_acquisition_control; nb10 §2 |
| D-049 | Predefined visual features: nine overlay-masked scene statistics in fixed image bands (`features.py`). Both sky features are dropped for a site when the median clipped-sky share exceeds 0.2 (image QC only, declared before any label–feature relation was examined). | adopted for exploratory M1 | nb09 §4 |
| D-050 | Contrasting site CPER (semi-arid grassland, UTC−7) alongside HARV, June–August 2023, hourly frames 06–19 LST. | adopted for exploratory M1 | nb09 |
| D-051 | Declared exploratory comparison (nb10 §1–2): no moisture-information claim. Shift test p = 0.90 (HARV) and 0.59 (CPER); chronological G is unstable under nuisance choices, from −9.7 to +1.5 nats at HARV. | recorded | nb10 |
| D-052 | Train-only visual projection E[V \| hour, T, doy] (D-035) on single-season real data: its inner day folds interpolate across neighbouring days, creating a fit/evaluation asymmetry (CPER R² 0.63 vs 0.00) and a contaminated null (median +0.14 nats). | **reopened, review requested** | nb10 §3; reviews/m1_exploratory_review.md |
| D-053 | Illumination and acquisition state as a pathway outside C: auto-exposure alone passes the shift test at both sites. | **open, review requested** | nb09 §4, nb10 §2 |

## Open questions carried to M1

- CO-RH construction (direct RH head vs joint `p(T, D | V)`), and the clock-only reference for CO.
- Site and calibration schemas (target distances, region maps, radiometric response), deferred until a fixed site or public camera is chosen.
- Solar geometry features (`solar_elev_deg`) and a conditional permutation test for E2.
- Tobit-type fitting for censored labels; temperature-history look-back ablation.
- Dried-aerosol feasibility for E3.
