# Provider comparison — Longitudinal benchmark analysis

Per **backend_kind** (from each cell's benchmark response), mean of cell total scores within each run. Use **`comparison_fingerprints`** on each run's `manifest.json` to confirm the same suite, prompt set, provider config, scoring config, browser config, and prompt registry state before comparing scores. Optional `run_context.json` adds git/release labels.

## Comparison fingerprints (manifest)

| Run id | Suite | Prompts | Providers | Scoring | Browser | Registry |
| --- | --- | --- | --- | --- | --- | --- |
| `longitudinal-w02` | `sha256:4b999adcafe861…` | `sha256:4048d181372ff7…` | `sha256:4fbcb71d4546d6…` | `sha256:f958bcbda76ced…` | `sha256:0801b86094b64d…` | `sha256:9604a174787655…` |
| `longitudinal-w03` | `sha256:4b999adcafe861…` | `sha256:4048d181372ff7…` | `sha256:4fbcb71d4546d6…` | `sha256:f958bcbda76ced…` | `sha256:0801b86094b64d…` | `sha256:9604a174787655…` |

Full hashes are 72 characters (`sha256:` + 64 hex). Truncated above for layout.

## By run and backend kind

| Run id | Benchmark | Backend kind | Cells | Mean score |
| --- | --- | --- | ---: | ---: |
| `longitudinal-w02` | `bench.fixtures.longitudinal.v1` | `mock` | 1 | 0.820000 |
| `longitudinal-w03` | `bench.fixtures.longitudinal.v1` | `mock` | 1 | 0.700000 |

## By scoring backend (evaluation)

| Run id | Scoring backend | Cells | Mean score |
| --- | --- | ---: | ---: |
| `longitudinal-w02` | `deterministic` | 1 | 0.820000 |
| `longitudinal-w03` | `deterministic` | 1 | 0.700000 |

## Grouping index (optional)

Use `group_snapshots_by(snapshots, key)` in Python with keys: `git_ref`, `release_tag`, `provider_fingerprint`, `scoring_backend`, `execution_mode`, `task_family`, `suite_definition_fingerprint`, `prompt_set_fingerprint`, `provider_config_fingerprint`, `scoring_config_fingerprint`, `browser_config_fingerprint`, `prompt_registry_state_fingerprint`.
