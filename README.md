# visual_hygrometry

Can a fixed camera observe near-surface moisture, and how much does it see **beyond** what clock, season, air temperature, aerosol state and camera effects already explain?

The project treats this as an identifiability problem, not as image-to-humidity regression. The primary estimand is the conditional mutual information `E2 = I(D; V | hour, season, T)` between images `V` and the dew-point depression `D = T − Td`, estimated by the held-out log-score contrast of matched probabilistic models. Camera-only (CO), temperature-assisted (TA) and contextual (CTX) predictors are separate products with separate input contracts ([docs/research_scope.md](docs/research_scope.md)).

## Current stage: Phase 0 / M0 — foundation, data contract, estimator validation

| piece | where | status |
|---|---|---|
| scope, settings, field-role matrix | [docs/research_scope.md](docs/research_scope.md) | drafted |
| leakage policy | [docs/metadata_policy.md](docs/metadata_policy.md), `src/visual_hygrometry/policy.py`, [configs/inference_settings.yaml](configs/inference_settings.yaml) | enforced, tested |
| data contracts | [schemas/](schemas/) (`sample`, `frame`, `sensor`) | drafted; site/calibration schemas pending |
| thermodynamics | `thermo.py`, [notebooks/00](notebooks/00_thermodynamics_and_synthetic_data.ipynb) | validated against steam tables |
| blocked splits, purging | `splits.py` | tested |
| information estimator | `scoring.py`, `synthetic.py`, [notebooks/01](notebooks/01_information_estimator.ipynb) | first validation (kept as record, including failures) |
| revised inference, families, censoring | `inference.py`, `scoring.py`, [notebooks/03](notebooks/03_inference_and_density_revision.ipynb), [addendum](docs/m0_decision_addendum.md) | 7/8 held-out criteria pass; context-capacity check (A5) fails, blocks confirmatory use |
| public data | [notebooks/02](notebooks/02_public_data_audit.ipynb) | NEON stage 1 (metadata); token now available via `.env` (never committed); feasibility use only |
| maths | [docs/mathematical_formulation.md](docs/mathematical_formulation.md) | |

Nothing here is evidence that RGB imagery carries moisture information; all estimator results so far are on synthetic data with known truth.

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
cd notebooks && PYTHONUTF8=1 ../.venv/Scripts/jupyter-execute.exe --inplace 00_thermodynamics_and_synthetic_data.ipynb 01_information_estimator.ipynb 02_public_data_audit.ipynb 03_inference_and_density_revision.ipynb
```

`PYTHONUTF8=1` matters on Windows: `jupyter execute` otherwise opens notebooks with the locale code page. Notebook 01 takes about 4 minutes, notebook 03 about 5 minutes on 16 parallel workers; notebook 02 queries the NEON and PhenoCam APIs live. A NEON API token, if needed, is read from `NEON_TOKEN` in `.env`.

## Layout

```text
configs/   inference settings (roles each setting may consume)
docs/      scope, policy, mathematics, decision log
schemas/   JSON-schema data contracts with x-role / x-derived-from annotations
src/visual_hygrometry/
           thermo.py  data.py  policy.py  splits.py  scoring.py  inference.py  synthetic.py
notebooks/ 00 thermodynamics + synthetic world, 01 first estimator validation, 02 public-data audit,
           03 revised inference / predictive families / censoring with a held-out validation suite
tests/     pytest suite (thermodynamics, policy canaries, splits/purging, scores, estimator bias)
data/      local data area; raw files are ignored by Git (data/README.md)
```

## Data sources and licences

NEON tower products (DP1.00098.001 relative humidity, DP1.00003.001 triple-aspirated air temperature, DP1.00033.001 phenology images; National Ecological Observatory Network, Battelle) and the PhenoCam Network archive (CC BY 4.0). Licence of NEON data products to be confirmed before redistributing derived tables.
