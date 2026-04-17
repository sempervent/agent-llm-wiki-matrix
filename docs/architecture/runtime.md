# Runtime architecture

## Python environment

- **Package:** `agent-llm-wiki-matrix` (import name `agent_llm_wiki_matrix`).
- **Interpreter:** 3.11+ recommended; Docker image uses `python:3.11-slim-bookworm`.
- **CLI:** `alwm` (Click). Global option `--log-level` / `ALWM_LOG_LEVEL`.
- **Logging:** `structlog` with ISO timestamps (UTC) to stderr.

## Environment variables

See `.env.example`. Notable keys:

| Variable | Purpose |
| --- | --- |
| `ALWM_LOG_LEVEL` | Logging verbosity |
| `ALWM_REPO_ROOT` | Repository root for schema paths and future pipelines (Compose sets `/workspace`) |
| `ALWM_FIXTURE_MODE` | Convention: prefer fixtures / no live endpoints when set to `1` |
| `ALWM_PROVIDER` | `mock`, `ollama`, or `openai_compatible` |
| `ALWM_PROVIDER_CONFIG` | Optional path to YAML (see `config/providers.example.yaml`) |
| `OLLAMA_HOST`, `OLLAMA_MODEL` | Ollama endpoint overrides |
| `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `OPENAI_MODEL` | OpenAI-compatible server overrides |
| `LLAMACPP_OPENAI_BASE_URL` | Override for Compose **benchmark-llamacpp** (default `host.docker.internal:8080/v1`) |

## Docker

- **Image:** `Dockerfile` `runtime` target (CLI); `test` target installs `.[dev]` for pytest. Non-root user `alwm` (uid 1000); workdir `/workspace`.
- **Compose:** `orchestrator` (**dev**), `tests` (**test**, pytest), `benchmark` (**benchmark**, `alwm info` smoke), **`benchmark-offline`** (`alwm benchmark run` with `ALWM_FIXTURE_MODE=1` and mock backends), **`benchmark-ollama`** (bundled `ollama` service + `benchmarks/v1/ollama.v1.yaml`), **`benchmark-llamacpp`** (OpenAI-compatible URL toward the host for llama.cpp-style servers). All bind-mount the project to `/workspace`.
- **Bake:** `docker-bake.hcl` — variable `PLATFORM` (comma-separated) defaults to `linux/amd64,linux/arm64`; targets `orchestrator`, `orchestrator-amd64`, `orchestrator-arm64`.

## Benchmark execution

- **Provider layer:** `BaseProvider.complete` via `providers/factory.py` (`mock`, `ollama`, `openai_compatible`).
- **Execution tagging:** `providers/execution.py` wraps outputs for `cli` vs `browser_mock` vs `repo_governed` so rubric scores differ by execution mode without a real browser.
- **Per-variant config:** `providers/benchmark_config.py` merges `ProviderConfig` with each variant’s backend; when `ALWM_FIXTURE_MODE=1`, backends are forced to **mock** unless `alwm benchmark run --no-fixture-mock`.

## CI-friendly commands

`just ci` runs Ruff, Mypy, and pytest without Docker. `just benchmark-offline` runs the full harness in a container (mock-only, deterministic).
