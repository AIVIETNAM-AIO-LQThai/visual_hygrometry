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
| D-025 | Context capacity must exceed what the image can encode about context; polynomial adequacy diagnostic insufficient. | **open, blocking** | nb03 validation A5 failed (39 % flag rate, 100 % false rejection in V-N4) |
| D-026 | η² leakage audit uses average ranks (row-order invariant, ties share a bin). | adopted | test_eta2_ignores_row_order_and_keeps_ties_together |

## Open questions carried to M1

- CO-RH construction (direct RH head vs joint `p(T, D | V)`), and the clock-only reference for CO.
- Site and calibration schemas (target distances, region maps, radiometric response), deferred until a fixed site or public camera is chosen.
- Solar geometry features (`solar_elev_deg`) and a conditional permutation test for E2.
- Tobit-type fitting for censored labels; temperature-history look-back ablation.
- Dried-aerosol feasibility for E3.
