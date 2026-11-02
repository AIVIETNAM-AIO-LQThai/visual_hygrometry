# Review 8: M1.4 closes NEON Q0. No repaired CRT sampler held level at the required precision, and the misspecified samplers did not inflate either

## Why this is a review checkpoint

Discussion 8 asked for escalation at the end of the bounded M1.4 experiment. It has ended. Under the rules declared before any code ([plan](../docs/m14_sampler_experiment_plan.md) §4, §8), no candidate is eligible, so the outcome is **closed**: NEON Q0 development ends for this phase, and the real labels were not read (D-085). The M2A design also has open decisions that change cost and site count, and M1.4 adds one more: how the field null will be calibrated.

## Decisions requested

1. **Accept the closure as recorded,** including the reading that P failed on precision, not on demonstrated invalidity.
2. **The methods lesson.** Is it right to read M1.4 as: on single-site data of this size, CRT Type I is only weakly sensitive to the visual sampler's distributional fidelity (about 0.04–0.11 across samplers and worlds), so neither fidelity audits nor 400-dataset gates can certify a sampler at the 0.10 tolerance?
3. **Null calibration in the field pilot** (m2a §14 item 6): replication across sites and seasons, a sampler fitted on far more independent data, or negative-control targets in frame. Which should drive the site count and duration?
4. **The other M2A escalation items** (m2a §14 items 1–5): one camera or two; the site; T_surface in the P2 context; the near-saturation label (heated probe or chilled mirror); the budget tier.

## What was done (M1.4)

- **Code.**
  - `samplers.py`: generators P (parametric: hour- and temperature-dependent scale, simulation-calibrated within-day AR, day-level AR, joint Student-t innovations) and R (scale model, day-mean AR with resampled innovations, donor within-day days by season and daily-max-T tercile), plus the worlds and the held-out audit.
  - 12 tests. The suite stands at 125 passing.
  - One implementation fix, found in code review before any result existed: R's day-mean variance is rescaled. Recorded in plan §10.
- **Exchangeability checks for R.**
  - Donor pools hold 29–31 days per season × tercile.
  - The ratio of residual SD between the late and early halves of each season is 0.97–1.20, and between warm and cool days within a tercile it is 0.93–1.03.
- **Run times.** Notebook 19 took 9 h 10 min on 18 workers, against an estimate of 4–5 h; the 10 h cap was not reached. Notebook 20 ended at its decision step.

## Type I (notebook 19; rejections at p ≤ 0.05, 39 draws, exact level 0.05)

| sampler | W0R | W0P | W1 regime | W2 volatility | W3 long memory | pooled |
|---|---|---|---|---|---|---|
| **P** (n = 400) | 32 | 14 | 29 | 24 | 30 | 0.065 |
| **R** (n = 400) | 29 | 20 | 34 | 30 | 45 | 0.079 |
| M-a, notebook 17 sampler (n = 200) | 8 | 6 | 11 | 15 | 9 | 0.049 |
| M-b, φ_w = 0 | 11 | 7 | 18 | 18 | 21 | 0.075 |
| M-c, Gaussian, no scale | 13 | 8 | 15 | 12 | 18 | 0.066 |
| M-d, independent features | 23 | 16 | 17 | 17 | 16 | 0.089 |
| M-e, persistence × 1.5 | 10 | 6 | 8 | 5 | 13 | 0.042 |

- **Acceptable** requires ≤ 29/400 or ≤ 12/200. **Demonstrated inflation** requires ≥ 51/400 or ≥ 28/200.
- **P** missed acceptability in W0R by 3 rejections and in W3 by 1. An exact-level sampler passes all five worlds with probability 0.91, but P's pooled excess is real (p = 0.004 against 0.05).
- **R** is worst in long memory: 45/400, with a one-sided lower bound of 0.087.
- **No pair shows demonstrated inflation.** By world, the pooled rates are W0R 0.070, W0P 0.043, W1 0.073, W2 0.067 and W3 0.084.

## Audit, power, re-audit

- **Audit: inconclusive by rule.** Validation needs an invalid pair, and there is none.
  - Descriptively, the candidates have the lowest mean A (≈ 0.22). Most misspecified samplers are higher, up to 0.72. M-c in long memory is lower, at 0.15.
  - A's ranking does not track Type I. M-a and M-e audit badly (A ≈ 0.35–0.65) yet hold level best.
  - τ_A = 0.56. The acceptable pair M-a × W1 has a false-alarm rate of 0.45.
- **Power was not estimated,** because no candidate was eligible.
- **Notebook 20** recorded *closed* without auditing anything and computed no p-value.

## Weaknesses of the design (admitted)

- **The misspecified arms were too small.** At n = 200, an exact-level sampler is classed acceptable in all five worlds only 32 % of the time, and a sampler at a true rate of 0.15 is flagged only 68 % of the time.
- **The audit's validation depended on an invalid pair,** which needed inflation of roughly 0.15 or more. These operating characteristics were computable before the run and were not computed.
- **The worlds may be too benign** to make the chosen misspecifications harmful, or the held-out log-score statistic may be robust to them. M1.4 cannot separate these two explanations.
- **The tolerance itself.** The 0.10 tolerance with one-sided 95 % bounds asks for ≤ 0.0725 observed at n = 400. A sampler whose true rate is around 0.065 passes each world only marginally.

## What stands, and what does not

- **Stands:**
  - the NEON measurement model and the verified CPER image set;
  - the descriptive per-season gains (notebook 18);
  - the methods results of notebooks 11, 14, 17 and 19.
- **Not shown:**
  - that CPER images carry no moisture information;
  - that the samplers are invalid. They are not shown valid at the required precision.
- **CPER 2024–2025 stay frozen and unused.**

## Recommendation

1. **Accept the closure.** No further NEON Q0 design iteration (plan §8, D-085).
2. **M2A carries the question forward,** with the null-calibration decision made before the budget tier. The leading option is replication across independent seasons *and* at least two sites. Negative-control targets in frame are a cheap supplement, not a substitute.
3. **For any future simulation gate,** compute the gate's operating characteristics (pass probability at the nominal rate and at the tolerance) before declaring it, and size every arm so that an invalid class is reachable.

## Ready-to-send discussion prompt

> You reviewed this project seven times and discussed it once (latest: M2A primary; one bounded M1.4 CRT sampler experiment with candidates P and R, five null worlds outside the class, five misspecified samplers, held-out audit, Q0 only if valid and ≥ 0.80 power at 0.05 nats). M1.4 is complete; the report is attached.
>
> **Result: closed.** No candidate was eligible, so the real labels were never read.
> - P: 32/400 rejections in W0R and 30/400 in long memory, against an acceptable limit of 29; pooled 0.065 over 2000 datasets (p = 0.004 against 0.05).
> - R: 45/400 in long memory; pooled 0.079.
> - No pair showed demonstrated inflation.
>
> **The misspecified samplers did not inflate either.** Pooled rates were 0.042–0.089. The notebook 17 sampler, which failed the real-image audit, held 0.049. So no invalid pair existed, and the held-out audit's validation is inconclusive by rule. The audit's A ranks the candidates best, but A does not track Type I.
>
> **Admitted design weakness.** With n = 200 arms, an invalid class needed inflation of about 0.15 or more; this was not computed beforehand.
>
> Please challenge, specifically:
> 1. Is "closed" the right reading, given that P's failure is on precision and an exact-level sampler passes all five worlds only 91 % of the time? Or does the pooled excess of 0.065 justify closure on its own?
> 2. Is the methods lesson sound: that single-site CRT Type I is weakly sensitive to sampler fidelity, so fidelity audits are a poor proxy for validity? Or were the worlds and misspecifications too benign to show it?
> 3. For the field pilot, how should the null be calibrated: replication across sites and seasons, a sampler fitted on much more independent data, or negative-control targets in frame? What does that imply for site count and duration?
> 4. The M2A escalation items: one camera or two; site; T_surface in the P2 context; heated probe or chilled mirror; minimum or recommended tier first.
>
> Do not assume the recommendations are correct. Give GO / MODIFY / STOP for (a) closing NEON Q0, (b) the null-calibration strategy, and (c) each M2A escalation item.
