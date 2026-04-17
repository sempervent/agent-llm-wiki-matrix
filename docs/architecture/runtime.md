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
| `ALWM_FIXTURE_MODE` | Future: force fixture-only behavior (no network) |
| `ALWM_PROVIDER` | Future: `mock`, `ollama`, `openai_compatible` |

## Docker

- **Image:** `Dockerfile` `runtime` target; non-root user `alwm` (uid 1000); workdir `/workspace`.
- **Compose:** Service `orchestrator` is gated by profiles `dev`, `test`, `benchmark`; bind-mounts the project to `/workspace`.
- **Bake:** `docker-bake.hcl` — variable `PLATFORM` (comma-separated) defaults to `linux/amd64,linux/arm64`; targets `orchestrator`, `orchestrator-amd64`, `orchestrator-arm64`.

## CI-friendly commands

`make ci` runs Ruff, Mypy, and pytest without Docker. For container parity, build the image and run `docker run --rm -v "$PWD":/workspace -w /workspace agent-llm-wiki-matrix:local …` (pattern to be wrapped in Make targets in Phase 6+).
