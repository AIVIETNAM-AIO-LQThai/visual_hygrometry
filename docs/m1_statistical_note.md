# Statistical note: E2, G, Q0 and interval targets

This note fixes what each reported quantity means, what its uncertainty statement may claim, and why the operational gain G is not bounded above by the information E2 (review 5, items 2 and 8.4). It replaces the gate G8 of notebook 11, which assumed that bound.

## 1 · Quantities

- **Variables.** D is the label (dew-point depression), V the image features, and C the declared context. In the primary analysis C is clock time, season, solar geometry and conditioning temperature; E2_illum adds the clear-sky index K. p denotes the true joint law, which is stationary within a camera epoch.
- **E2 = I(D; V | C) = E[log p(D | V, C) − log p(D | C)] ≥ 0.** This is the *scientific* target: how much the image tells about D beyond C. It is a property of the population and of C, not of any model. Neither it nor E2_illum is a causal humidity–optics effect; information can arrive through vegetation state, illumination, acquisition or any other pathway that C does not contain.
- **The model pair.** q_C(D | C) and q_VC(D | V, C) are fitted on training data of a given design (n_fit seasons), and the held-out contrast of a row is Δ = log q_VC(D | V, C) − log q_C(D | C).
- **G(design) = E[Δ]** over future data, with the fitted pair held fixed. This is the *operational* target: the predictive gain this pipeline actually delivers.
- **The cross-fitted estimate** (leave one season out) estimates the average of G over the training sets that design produces. It is an estimate of G, not of E2.
- **Q0, H0: V ⊥ D | C.** This is a *test*, not an estimate. Rejection says that the image carries some information beyond C, provided the null generator is valid (§3). It bounds nothing.

## 2 · Why G need not satisfy G ≤ E2

For fixed fitted models, taking expectations over the true law,

  E Δ = E2 − E KL(p(· | V, C) ‖ q_VC) + E KL(p(· | C) ‖ q_C).

The two KL terms are non-negative and enter with **opposite signs**.
- **G > E2** whenever the joint model repairs more of the context model's misfit than it adds of its own: KL_C > KL_VC + (E2 − G). The extreme case is E2 = 0. If V encodes a function of C that q_C cannot represent, q_VC uses V to represent it and G > 0 although V carries no information beyond C.
  - Notebook 11: V-N9 (season × hour) gives an estimate of +0.009 nats with E2 = 0, and its test rejects in 79 % of replicates.
  - Notebooks 03–04: the same mechanism produced false rejections in up to 100 % of replicates before context capacity was added.
- **G < E2** whenever q_VC is misspecified or over-fitted (a large KL_VC). This happens with linear V effects for regime-specific or rare-row information (notebook 11: 0.005 of 0.025 and 0.001 of 0.015 captured), with shrinkage (V-P1 and V-P2: 12 % and 8 % low), and with small n_fit.
- **G ≤ E2 holds only if q_C is correct (KL_C = 0).** No real context model is known to be correct, so G ≤ E2 is not a usable property. It is not a gate: captured-versus-true information is reported descriptively.

Consequently:
1. A positive G is evidence of information beyond C only to the extent that the context model's adequacy is established. This is why the adequacy auditor (§4) must have demonstrated power.
2. A G below a scientifically meaningful threshold does not show that E2 is small.

## 3 · Validity of Q0

The test refits the joint model on null visual data V* and compares the observed contrast with the null contrasts. Its validity depends on the generator, never on a single summary such as residual lag-one autocorrelation (review 5, item 4).

| generator | V* | valid when | known failure modes |
|---|---|---|---|
| cyclic shift (within seasons) | V̂(C) + residuals shifted by k ≥ 7 days, re-orthogonalised | residual series stationary and exchangeable under shifts within each stratum; the wrap-around join is harmless; V̂ is linear in the context basis, so any V–C structure outside that basis is broken by the shift | non-linear V–C structure; regime changes inside a stratum; persistence long relative to the season (notebook 11: 0.100 at AR 0.9) |
| conditional randomisation (CRT) | Ê[V \| C] + a simulated residual process (day-level and within-day AR(1) per season) | the model of V \| C is right, in mean and in dependence | an omitted V–C dependence, a misspecified residual process (regimes, heteroscedasticity, non-Gaussian tails) |

**Rule:** if no generator controls Type I in fresh worlds spanning the persistence and regime structure of the data, no conditional-independence claim is made, and only descriptive predictive results are reported.

**Status (notebook 16).** The CRT controlled Type I (0.02–0.08) in ten fresh nulls, including persistence 0.90–0.97, independent regimes and a camera change; the shift test did not (0.15 at persistence 0.90 and 0.97). This is synthetic evidence that the generator is robust to the structures simulated. It does not show that the sampler describes real images.

**Status (notebook 17).** On the real CPER features it does not: within-day persistence is under-simulated, and the residual scale (by hour and temperature) and heavy tails are not reproduced. By the declared rule it is not suitable, and no real-data Q0 p-value has been computed.

## 4 · Context adequacy

- **Why it matters.** The KL_C term is the route to false discovery, so every Q0 or G report needs an auditor that would have detected inadequacy.
- **Auditor.** A context-only challenger: the audited context plus a regularised non-linear correction on the raw context variables, scored on the same held-out folds. The training-only E[V | C] repair gain is a secondary diagnostic only.
- **Validation.** An auditor is validated on both sides: false alarms under adequate contexts, and detection power under deliberately misspecified ones. A diagnostic that never fires (notebook 11, G9) shows nothing.
- **Status (notebook 16).** The challenger failed on both sides: false alarms up to 0.19 on the chosen context, and detection 0.54 under the misspecified context. The repair diagnostic (τ = 0.002 nats per row) passed both: false alarms ≤ 0.05, detection 1.00. No validated primary auditor exists yet.

## 5 · Interval targets and what may be reported

| target | estimator | uncertainty sources | interval allowed |
|---|---|---|---|
| E2 | none directly; only via G under a validated, adequate context | model misspecification (KL terms) | none |
| G (leave one season out) | mean held-out contrast | within-season dependence, between-season variation, training-set variability | only an interval whose coverage is demonstrated near nominal in fresh worlds with the data's dependence (≥ 0.93 for a 95 % interval). The candidate is a t interval over per-season means (season clusters); otherwise none |
| season-specific G_s | held-out mean in season s | within-season dependence | none; reported descriptively, per season |
| frozen-model future G | chronological fit on early seasons, scored on a later season | between-season variation; a single evaluation season | none until a validated procedure exists |

Week-cluster intervals are no longer reported as confirmatory statements about future-season performance. They covered the truth in only 0.49 of replicates when the information persisted for weeks (notebook 11).

More seasons do not by themselves guarantee valid intervals. Season clusters with K seasons give K − 1 degrees of freedom and assume seasons are independent and identically distributed; camera epochs, trends across years and regime frequencies that change between years all violate that.

**Status (notebook 16).** The season-cluster t interval reached 0.92 coverage of G in only 3 of 15 fresh worlds (0.71–0.91 elsewhere), with small bias, so it is too narrow and is not validated. Notebook 16's gate was 0.92, below the 0.93 written above; the outcome is the same at either threshold.

## 6 · Reporting rules

1. Report E2 only as a scientific target, never as an estimate.
2. Report G, with design and n_fit stated, beside the auditor's result and the Q0 result with its generator, number of draws and minimum attainable p.
3. Report season-specific G descriptively.
4. Report every sensitivity analysis both as frozen-model deletion and as a full refit.
5. Never describe information beyond C as a direct humidity–optics signal without mediator evidence.
