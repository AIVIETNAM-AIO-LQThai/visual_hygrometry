# Mathematical formulation

Notation: `T` air temperature (°C), `Td` dew point (°C), `D = T − Td` dew-point depression (K), `RH` relative humidity over liquid water (%), `e`, `e_s` vapour and saturation vapour pressure (hPa), `V` visual observations, `C` conditioning context, `H` local hour, `S` season/site, `A` dry-aerosol reference. Information in nats.

## 1 · Thermodynamic reference (`thermo.py`, notebook 00)

**Saturation pressure.** Labels use Magnus over water with WMO-No. 8 coefficients, `e_s(T) = 6.112 exp(BT/(C+T))`, `B = 17.62`, `C = 243.12 °C`, stated range −45…60 °C. Against IAPWS-95 steam tables it is within 0.32 % on 0–50 °C and 0.58 % at −40 °C; Murphy & Koop (2005) reproduces the tables to < 0.01 % and serves as reference.

**Dew point and depression.** With `γ = ln(RH/100) + BT/(C+T)`, `Td = Cγ/(B − γ)` is the exact inverse of Magnus, so RH → Td → RH round-trips to machine precision. Using Murphy–Koop instead changes `D` by at most 0.077 K on −20…45 °C (largest when hot and dry), always well below the propagated reading error of a ±2 %RH probe.

**D–RH identity.** Under Magnus, exactly,

$$\ln\frac{RH}{100} = -\frac{B\,C\,D}{(C+T)(C+T-D)}.$$

For fixed `T` this is a strictly monotone map, hence for any `V`, `C`: `I(D; V | T, C) = I(RH; V | T, C)` **when `T` is the label unit's own temperature**. With an independent conditioning thermometer the identity holds only up to the inter-unit temperature discrepancy. The near-saturation slope `k(T) = BC/(C+T)²` varies ±23 % over −20…40 °C.

**Fixed vapour pressure.** At fixed `Td`, `∂D/∂T = 1` and RH falls ~6 %/K. A scene cue that tracks temperature or time of day therefore predicts RH and `D` without any moisture signal. The same identity means a probe whose sensing element is radiatively heated by δ reports the correct dew point but `D + δ` exactly.

**Reading-error propagation.** `σ_D² = (∂D/∂T)² σ_T² + (∂D/∂RH)² σ_RH² + 2ρ(∂D/∂T)(∂D/∂RH)σ_Tσ_RH` with

$$\frac{\partial D}{\partial RH} = -\frac{BC}{(B-\gamma)^2\,RH},\qquad \frac{\partial D}{\partial T} = 1 - \frac{BC}{(B-\gamma)^2}\frac{BC}{(C+T)^2}.$$

At 20 °C, `∂D/∂T` is 0.08 at 50 %RH and falls towards 0 at saturation, so RH error dominates everywhere (±2 %RH → σ_D ≈ 0.6 K at 50 %RH, 0.33 K at 98 %RH).

**Censoring rule.** Near saturation `D/σ_D ≈ (100 − RH)RH/(100σ_RH) ≈ (100 − RH)/σ_RH`, independent of temperature (exact crossing within 0.05 %RH of `100 − σ_RH` at 0, 20, 35 °C). Readings with `RH ≥ RH_c = 100 − kσ_RH` (default k = 1) are left-censored: the label is the bound `d_c = D(T, RH_c)` and the likelihood term is `log P(D ≤ d_c)`. The limit comes from the instrument specification only, never from the label distribution.

## 2 · Information targets

$$E_1 = I(D;V\mid H,S),\qquad E_2 = I(D;V\mid H,S,T),\qquad E_3 = I(D;V\mid H,S,T,A).$$

`E2` is primary: what the images say about `D` once clock, season and independently measured temperature (and, in serious context models, its history) are known.

**No ordering between E1 and E2.** By the chain rule,

$$E_1 - E_2 = I(D;T\mid H,S) - I(D;T\mid V,H,S),$$

an interaction information of either sign. A visual thermometer gives `E1 > E2 = 0`; a cue of absolute moisture (`Td`) gives `E2 ≫ E1` (notebook 01 §4: 0.80 vs 0.04 nats); even a temperature-independent moisture cue gives `E2 > E1` because conditioning on `T` removes nuisance variance from `D` (notebook 00 §6: 0.050 vs 0.036). The same holds for `E3 − E2`. Neither difference can be read as a test of a mechanism without estimating both terms.

**What may be conditioned on.** Conditioning on a variable caused by humidity (visibility, leaf wetness, undried PM) blocks the pathway being measured or opens collider paths; such variables are mediators or forbidden, never context.

## 3 · Estimator (`scoring.py`, notebook 01)

Fit a context model `q_C(d | c)` and a joint model `q_VC(d | v, c)` with identical model class, context columns and tuning, the joint model adding only visual columns. On held-out rows,

$$\widehat\Delta_{LS} = \frac1N\sum_{i}\big[\log q_{VC}(d_i\mid v_i,c_i) - \log q_C(d_i\mid c_i)\big].$$

**Decomposition.** For fixed fitted models and held-out rows drawn from `p`,

$$\mathbb E\,\widehat\Delta_{LS} = I(D;V\mid C) - \mathbb E_{v,c}\,\mathrm{KL}\big(p(\cdot\mid v,c)\,\|\,q_{VC}\big) + \mathbb E_{c}\,\mathrm{KL}\big(p(\cdot\mid c)\,\|\,q_C\big),$$

which follows from `E log q = −H − E KL` applied to both terms. Consequences: (i) the contrast equals the CMI only for correct models; (ii) a deficient context model (`KL_C > 0`) inflates it, so a positive contrast requires evidence that `q_C` is competitive (residual-vs-context diagnostics); (iii) a deficient or over-confident joint model deflates it, so a null requires positive controls and calibration checks; (iv) the empirical estimator is **not** an unbiased estimate of CMI and must not be called one.

**Predictive family.** Gaussian with ridge mean on standardised inputs. The SD comes from grouped inner out-of-fold residuals of the training rows (homoscedastic) or from a regression of `log r²` on the same inputs with the bias correction `E[log χ²₁] = ψ(½) + log 2 = −1.2704` (heteroscedastic). In-sample residual SD is optimistic and is kept only to demonstrate failure.

**Censored labels.** Censored rows contribute `log Φ((d_c − μ)/σ)`. Fitting the mean on censored labels as if exact is biased; a Tobit-type fit is required once censoring is non-negligible in real data (not yet implemented).

**Label noise.** If `d_obs = D + ν` with `ν ⊥ V | D, C`, the observation-level contrast targets `I(D_obs; V | C) ≤ I(D; V | C)` (data processing): it is conservative. For homoscedastic Gaussian noise of known SD, `½ log((s_C² − σ_ν²)/(s_VC² − σ_ν²))` recovers the latent value; it depends on knowing `σ_ν` and is unstable when either predictive variance approaches `σ_ν²`. If the noise depends on `V` (e.g. radiation error correlated with visible sunshine), the inequality fails and the contrast can be positive without any atmospheric information (§4).

**Transform invariance.** For a bijective transform `z = φ(d)` shared by both models, `log q(d) = log q_z(φ(d)) + log|φ'(d)|`; the Jacobian term cancels in the contrast. Modelling `log D` or RH-given-T instead of `D` changes the estimator through model fit only, not through the scale.

## 4 · Measurement error in the conditioning thermometer

Linear-Gaussian illustration with hour absorbed: `d = βt + r`, a probe error `e` that the image can predict, `Var(t) = σ_t²`, `Var(r) = σ_r²`, `Var(e) = σ_e²`, and `V` revealing `e`. Let `v_e = σ_e²σ_t²/(σ_t² + σ_e²)` be the error variance left after observing `T_cond = t + e`.

- Shared unit (`d_ref = d + e`, `T_cond = t + e`): `d_ref = βT_cond + (1 − β)e + r`, so the spurious `E2 = ½ log(1 + (1 − β)² v_e/σ_r²)`.
- Aspirated label, biased conditioning unit (`d_ref = d`): `d_ref = βT_cond − βe + r`, spurious `E2 = ½ log(1 + β² v_e/σ_r²)`.

With `β = 0.4`, `σ_t = 3`, `σ_r = 2`, `σ_e = 1 K` these are 0.039 and 0.018 nats, the same order as the illustrative 0.05-nat threshold. Which configuration is worse depends on `β`, so both units must be aspirated; swapping roles tests independent errors but not common-mode ones. Random (non-predictable) thermometer noise causes the same residual confounding only through visual thermometry and is negligible for a 0.1–0.2 K instrument.

## 5 · Uncertainty and nulls

- **Independent units** are days (default) or weeks. Rows within a unit are strongly dependent (synthetic: lag-1 autocorrelation 0.93, 69 % of moisture-residual variance between days).
- **Interval.** Percentile bootstrap of `Δ̂_LS` over units, conditional on the fitted models (training variability is not resampled). Notebook 01 §10 measures its repeated-sampling coverage; naive row bootstraps are invalid.
- **Permutation nulls.** Exchanging `V` between whole days preserves within-day structure but also breaks the `V`–`T` link, so it tests the E1-type null `V ⊥ D | H`, not the E2 null `V ⊥ D | H, T`. A valid E2 permutation needs a conditional scheme (e.g. conditional randomisation with a model of `V | C`); until then E2 inference rests on the cross-fitted contrast and its interval.
- **Thresholds.** A practical threshold for "meaningful visual information" must come with a power analysis on the real dependence structure; the 0.05-nat figure is a placeholder.

## 6 · Not established here

The Gaussian family for real `D` (skewed, bounded below, regime-dependent spread), the right temperature-history look-back, the Tobit fit for censored labels, a conditional permutation test for E2, and any optical forward model (extinction, wetness) are open. None of the synthetic results is evidence about real imagery.

## References

- WMO (2018). *Guide to Instruments and Methods of Observation*, WMO-No. 8, Vol. I, Annex 4.B (Magnus coefficients over water and ice).
- Murphy, D. M., Koop, T. (2005). Review of the vapour pressures of ice and supercooled water for atmospheric applications. *Q. J. R. Meteorol. Soc.* 131, 1539–1565.
- Alduchov, O. A., Eskridge, R. E. (1996). Improved Magnus form approximation of saturation vapor pressure. *J. Appl. Meteorol.* 35, 601–609.
- Gneiting, T., Raftery, A. E. (2007). Strictly proper scoring rules, prediction, and estimation. *J. Am. Stat. Assoc.* 102, 359–378.
- Künsch, H. R. (1989). The jackknife and the bootstrap for general stationary observations. *Ann. Stat.* 17, 1217–1241.
- Roberts, D. R. et al. (2017). Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. *Ecography* 40, 913–929.
- Candès, E., Fan, Y., Janson, L., Lv, J. (2018). Panning for gold: model-X knockoffs for high dimensional controlled variable selection. *J. R. Stat. Soc. B* 80, 551–577 (conditional randomisation test).
- Vapnik, V., Vashist, A. (2009). A new learning paradigm: learning using privileged information. *Neural Netw.* 22, 544–557.
- Narasimhan, S. G., Nayar, S. K. (2002). Vision and the atmosphere. *Int. J. Comput. Vis.* 48, 233–254.
