# Local development workflow

## Python

1. Install **[uv](https://docs.astral.sh/uv/)** (required for this repository’s host workflow).
2. From the repo root: `uv venv --python 3.11` then `uv pip install -e ".[dev]"` (see **`AGENTS.md`**). Activating `.venv` is optional if you use **`uv run`** for commands.
3. Run checks: **`uv run just ci`** (install [just](https://github.com/casey/just) if needed). Equivalent: activate `.venv` and run `just ci`.
4. CLI examples: `uv run alwm version`, `uv run alwm validate …`, pipeline commands (`ingest`, `evaluate`, `compare`, `report`), `uv run alwm providers show`.

Do **not** use `python -m venv`, bare `pip install`, Poetry, Pipenv, or Conda for the standard setup here unless you have an explicit reason (document in PRs if so).

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
| `test` | `tests` | Image runs pytest with dev dependencies in the `Dockerfile` `test` stage (container path; host devs use **`uv run just test`**) |
| `benchmark` | `benchmark` | Smoke `alwm info` with repo mounted at `/workspace` |
| `benchmark-offline` | `benchmark-offline` | `alwm benchmark run` with mock backends (`ALWM_FIXTURE_MODE=1`) → `out/benchmark-offline` |
| `ollama-gptoss-setup` | `ollama` | Start Ollama, pull **gpt-oss:20b**, `alwm benchmark probe` (bind-mount `./.ollama-models`) |
| `benchmark-ollama` | `ollama`, `benchmark-ollama` | After setup: `benchmarks/v1/ollama.v1.yaml` → `out/benchmark-ollama` |
| `smoke-ollama-live` | — | Opt-in host live benchmark (not default CI) |
| `benchmark-llamacpp` | `benchmark-llamacpp` | OpenAI-compatible URL (default host port 8080) + `llamacpp.v1.yaml` → `out/benchmark-llamacpp` |
| `benchmark-probe` | `benchmark-probe`, `ollama` | `alwm benchmark probe` (Ollama + host OpenAI-compatible reachability only) |
| `browser-verify` | `browser-verify` | Builds `Dockerfile` target `browser-test`; runs Playwright integration tests (`ALWM_PLAYWRIGHT_SMOKE=1`) |

Examples:

```bash
docker compose --profile dev run --rm orchestrator version
docker compose --profile test run --rm tests
docker compose --profile benchmark run --rm benchmark
docker compose --profile benchmark-offline run --rm benchmark-offline
```

`just compose-help` validates the Compose file for each profile and prints service names. Shortcut recipes: `just benchmark-offline`, `just ollama-gptoss-setup`, `just benchmark-ollama`, `just smoke-ollama-live`, `just benchmark-probe`, `just benchmark-llamacpp`, `just browser-verify`.

Opt-in live checks (providers + Playwright) are summarized in [live-verification.md](live-verification.md).

## Buildx Bake

- Multi-arch: `docker buildx bake` (see `docker-bake.hcl`).
- Faster single-arch: `docker buildx bake orchestrator-amd64` or `orchestrator-arm64`.

Other ARM variants (for example `linux/arm/v7`) are **not** assumed; add explicit targets and base-image validation before advertising support.
