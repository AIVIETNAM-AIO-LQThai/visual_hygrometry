# data

Raw imagery, sensor files and API caches never enter Git (`data/raw/`, `data/cache/`, `data/interim/` are ignored). What may be committed: small manifests that conform to `schemas/` (frame paths with SHA-256, sensor readings tables when licences allow), fold assignments and snapshot descriptors, so that every reported number can be traced to exact inputs.

| directory | content | in Git |
|---|---|---|
| `raw/<provider>/<product>/<site>/` | files exactly as downloaded, never edited | no |
| `cache/` | API responses, thumbnails | no |
| `interim/` | aligned tables before QC | no |
| `manifests/` | frame and sensor manifests, split assignments, hashes | yes, if small and licence-compatible |

Credentials (e.g. a NEON API token) are read from environment variables and are never written to files in this repository.
