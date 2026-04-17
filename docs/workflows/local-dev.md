# Local development workflow

## Python

1. Use Python **3.11+** (matches Docker). On macOS with Homebrew: `/opt/homebrew/bin/python3.11`.
2. Create a venv: `python3.11 -m venv .venv && source .venv/bin/activate`.
3. Install: `pip install -e ".[dev]"`.
4. Run checks: `make ci`.
5. CLI: `alwm version`, `alwm info`, `alwm validate …`, pipeline commands (`ingest`, `evaluate`, `compare`, `report`), `alwm providers show`.

## Docker

```bash
cp .env.example .env   # optional
docker build -t agent-llm-wiki-matrix:local -f Dockerfile .
docker run --rm agent-llm-wiki-matrix:local version
```

## Docker Compose profiles

| Profile | Service | Intended use |
| --- | --- | --- |
| `dev` | `orchestrator` | Interactive `alwm` against the mounted repo (`command` defaults to `--help`; override when running) |
| `test` | `tests` | `python -m pytest` in the `Dockerfile` `test` stage (dev dependencies installed) |
| `benchmark` | `benchmark` | Smoke `alwm info` with repo mounted at `/workspace` |
| `benchmark-offline` | `benchmark-offline` | `alwm benchmark run` with mock backends (`ALWM_FIXTURE_MODE=1`) → `out/benchmark-offline` |
| `benchmark-ollama` | `ollama`, `benchmark-ollama` | Ollama daemon + `benchmarks/v1/ollama.v1.yaml` → `out/benchmark-ollama` |
| `benchmark-llamacpp` | `benchmark-llamacpp` | OpenAI-compatible URL (default host port 8080) + `llamacpp.v1.yaml` → `out/benchmark-llamacpp` |

Examples:

```bash
docker compose --profile dev run --rm orchestrator version
docker compose --profile test run --rm tests
docker compose --profile benchmark run --rm benchmark
docker compose --profile benchmark-offline run --rm benchmark-offline
```

`make compose-help` validates the Compose file for each profile and prints service names. Shortcut targets: `make benchmark-offline`, `make benchmark-ollama`, `make benchmark-llamacpp`.

## Buildx Bake

- Multi-arch: `docker buildx bake` (see `docker-bake.hcl`).
- Faster single-arch: `docker buildx bake orchestrator-amd64` or `orchestrator-arm64`.

Other ARM variants (for example `linux/arm/v7`) are **not** assumed; add explicit targets and base-image validation before advertising support.
