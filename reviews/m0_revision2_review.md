# M0 revision 2 review: zero-information test validated; effect-size interval unresolved

## Why this is a review checkpoint

After the first independent review (decision: MODIFY), the estimator was revised in three stages. Each stage was validated on a fresh synthetic suite with criteria declared before the run. The zero-information test and the point estimate now pass on worlds never used in development. One consequential choice remains open and should not be made by the implementer alone: **which interval to report for the effect size, and for which estimand.** It determines what a future "E2 ≥ δ" claim means.

## What was done since the first review

| stage | change | fresh-suite outcome |
|---|---|---|
| notebook 03 | Q0/Q1/Q2 separation; refitting day-block permutation test; frozen hold-out interval; Tobit fitting; KDE and binned families; η² fix | 7/8 pass; **A5 fail**: an image encoding a temperature non-linearity the context could not represent gave 100 % false rejection in a null world |
| notebook 04 | flexible context in both models: fixed-knot cubic spline in T + hour × T products + cross-fitted gradient-boosting projection E[V | hour, T] (labels unused); SD floor in standardisation | 3/7 pass; permutation Type I 0.033–0.060 in six fresh nulls (the old context reached 1.00); **effect-size mean wrecked** by single rows of −117 to −130 nats at context-support edges |
| notebook 05 | Gaussian predictive mixed 1 % with a Cauchy(μ, 4σ) component (still proper); scoring restricted to rows inside the 0.5–99.5 % training quantile box of (hour, T) (1.5 % excluded, reported) | 5/7 pass (below) |

Rejected along the way, with the evidence kept in the notebooks:
- `log r²` variance regression;
- binned family with V × context interactions;
- light penalty on the context block (catastrophic rows);
- squares/products and boosted-context adequacy diagnostics as a substitute for context capacity (flag rates 0.37–1.00);
- the frozen one-sided test for Q0.

## Notebook 05 fresh validation (seeds 120 000+, 150 replicates per world)

Worlds: 30 samples/day, 100 days. Nulls: well-specified; regime with strong serial dependence; and a hinge, cubic, softplus or bilinear context term encoded by the cue (truth 0). Positives: plain cue (0.05, 0.10), and mixed cues encoding a context non-linearity plus moisture (0.05, 0.10, 0.05). Method: `spline+proj` context, robust Gaussian, common support.

| id | criterion | value | pass |
|---|---|---|---|
| C1 | permutation Type I ≤ 0.085 in each null | 0.060, 0.047, 0.053, 0.053, 0.027, 0.033 | yes |
| C2 | frozen one-sided Type I ≤ 0.085 | 0.027, 0.027, 0.047, **0.167** (cubic), 0.020, 0.080 | no |
| C3 | permutation power ≥ 0.80 | 1.00, 1.00, 1.00 | yes |
| C4 | mean bias ≤ 0.01 plain, ≤ 0.015 mixed | −0.001, −0.000, −0.000, −0.009, +0.002 | yes |
| C5 | frozen interval covers truth and its target ≥ 0.88 | target 0.91–0.93; truth 0.89, 0.91, **0.82, 0.75**, 0.89 | no |
| C6 | worst single row ≥ −10 nats | −4.2 (plain Gaussian: −10 931) | yes |
| C7 | off-support share ≤ 0.05 | 0.015 | yes |

## The open decision

**Observation.** The frozen hold-out interval is calibrated for its own target, the population contrast of models fitted on half of the days (coverage 0.91–0.93). That target sits below E2 when the image carries both context structure and moisture, and above zero in the cubic null. So it is neither a lower bound nor an unbiased target for E2. The cross-fitted point estimate is nearly unbiased for E2 (C4), but in earlier stages its day-cluster t interval under-covered at 60 days (0.86) and was conservative at the null.

**Options:**
1. **Report the frozen target honestly as "information captured by a model fitted on n/2 days"**, and drop interval claims about E2. Q2 (meaningful effect) then becomes "a deployable model captures at least δ". This is scientifically clear but answers a different question.
2. **Cross-fitted day-cluster t interval for E2 with a calibration study**, such as a world-matched parametric or residual-block bootstrap that refits the models. The review asked for any such procedure to be validated under misspecification.
3. **Nested or repeated cross-fitting variance estimators** (Bates, Hastie & Tibshirani 2024; corrected resampled t, Nadeau & Bengio 2003), whose target is the cross-fitted estimand.
4. **Inversion of the permutation test.** Test H0: E2 ≤ δ by shifting the statistic? There is no exact construction; it would need a model of how the statistic depends on δ.

**Also needs a ruling:** common-support scoring changes the estimand to information on the supported context region. That is harmless in all synthetic worlds here (the per-row information is context-independent), but not in general. Should Exp 2a report E2 on the support plus the excluded share (current plan), or require a sensitivity analysis with wider boxes (0.1–99.9 %)?

## Caveats

- All results are synthetic; real `D | C` and real images may break assumptions not represented: e.g. context-dependent information, non-stationary days, and visual features that are high-dimensional rather than single cues.
- The visual feature in every world is one column. The ≤ 10-feature Exp 2a-A design and the frozen-encoder Exp 2a-B design (decisions D-021, D-022) are not yet simulated.
- The permutation test reached Type I 0.09 in one strongly dependent development world in notebook 03 (unexplained); every validation null since has been 0.027–0.060.
- Defensive weight 1 %, Cauchy scale 4σ, quantile box 0.5–99.5 % and knot grid were fixed a priori, not tuned; their sensitivity is untested.

## Recommended next step

Adopt option 1 for the deployment-relevant question and option 3 for E2. Validate option 3 on a fresh suite, including the mixed-cue worlds where frozen and cross-fitted targets diverge. Keep Q0 on the permutation test.

**Alternative:** option 2, a refitting residual-block bootstrap calibrated per world. It is costlier and depends on a fitted world model, so it must itself be tested under misspecification.

## Ready-to-send discussion prompt

> You reviewed an earlier version of this estimator and asked for revisions (MODIFY). The attached report summarises three revision stages, each validated on a fresh synthetic suite with pre-declared criteria. The zero-information test is now a refitting day-block permutation test with a flexible context (spline in T, hour × T products, cross-fitted projection of the visual feature on the context), robust Gaussian scoring (1 % Cauchy mixture) and common-support restriction. Its Type I error is 0.027–0.060 in six fresh nulls, including context non-linearities encoded by the cue, with power 1.00. The cross-fitted point estimate's bias is ≤ 0.009 nats.
>
> The remaining issue: the frozen hold-out interval covers its own target (information captured by half-data models) at 0.91–0.93, but not E2 (0.75–0.82 in mixed-cue worlds), and its one-sided test rejects a cubic null 17 % of the time.
>
> Please challenge, specifically:
> 1. Is it legitimate to answer Q1 (effect size) with "information captured by a model fitted on n/2 days" rather than E2, and what would that change in a GO/STOP decision?
> 2. Which interval construction for the cross-fitted E2 estimate would you trust at 60–120 independent days, and how should it be validated: nested CV, corrected resampled t, refitting block bootstrap, or something else?
> 3. Is restricting scoring to the training context support (1.5 % excluded) an acceptable estimand change? What sensitivity analysis should accompany it?
> 4. Are the defensive Cauchy mixture and the cross-fitted visual projection sound in principle, or could either hide real information (false STOP) or create it (false GO) in a way these synthetic worlds would not reveal?
> 5. Is the estimator now acceptable for exploratory NEON feasibility work, and what must be added before confirmatory Exp 2a?
>
> Do not assume the recommendations are correct. Give GO / MODIFY / STOP for proceeding to (a) NEON feasibility analysis and (b) confirmatory Exp 2a design.
