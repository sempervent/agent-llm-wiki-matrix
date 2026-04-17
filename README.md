# agent-llm-wiki-matrix

Markdown-first, git-native **LLM wiki + comparison matrix** system for capturing ideas, experiments, evaluations, prompts, and reports as structured files. It supports reproducible benchmarking of multiple agent stacks and model backends (including local models via **Ollama** or switchable **OpenAI-compatible / llama.cpp** HTTP servers).

**Repository:** [github.com/sempervent/agent-llm-wiki-matrix](https://github.com/sempervent/agent-llm-wiki-matrix)

## Goals

- **Markdown-first, git-native** artifacts: notes, matrices, rubrics, and reports live in the repo.
- **Comparison matrices** across agent stacks, models, backends, prompts, browser behaviors, and orchestration patterns.
- **Docker Compose** for local orchestration; **Docker Buildx Bake** for multi-platform images (`linux/amd64`, `linux/arm64` by default).
- **Deterministic pipelines** where possible: typed contracts, schemas, fixtures, and testable ingest → evaluate → compare → summarize flows.
- **Provider abstraction** for Ollama and OpenAI-compatible endpoints (see roadmap in `docs/architecture/target-state.md`).

## Quickstart

### Prerequisites

- Docker with Buildx, Docker Compose v2
- Python **3.11+** recommended (matches the `Dockerfile`; use `pyenv`/`brew` if your system Python is older)

### Local Python

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alwm version
alwm info
alwm validate examples/v1/thought.json thought
alwm providers show
make ci
```

### Docker

```bash
cp .env.example .env
docker build -t agent-llm-wiki-matrix:local -f Dockerfile .
docker run --rm agent-llm-wiki-matrix:local version
```

### Buildx Bake (multi-arch)

```bash
docker buildx bake
# Single architecture (faster iteration):
docker buildx bake orchestrator-amd64
```

### Compose (profiles)

```bash
docker compose --profile dev run --rm orchestrator version
```

See `docs/workflows/local-dev.md` for profile details (`dev`, `test`, `benchmark`).

## Architecture (summary)

| Layer | Role |
| --- | --- |
| **Docs** | `docs/` — architecture, workflows, implementation log |
| **Schemas** | JSON Schema for structured artifacts under `schemas/` |
| **Templates** | Markdown templates under `templates/` |
| **Prompts** | Versioned prompt registry under `prompts/` |
| **Python package** | `src/agent_llm_wiki_matrix` — CLI, pipelines, validators (growing by phase) |
| **Docker** | `Dockerfile`, `docker-compose.yml`, `docker-bake.hcl` |

Detailed diagrams and data flow: `docs/architecture/runtime.md`, `docs/architecture/data-model.md`, `docs/architecture/evaluation-pipeline.md`.

## Commands (Makefile)

| Target | Description |
| --- | --- |
| `make install-dev` | Editable install with dev dependencies |
| `make test` | Run pytest |
| `make smoke` | Smoke tests only |
| `make lint` | Ruff check |
| `make fmt` | Ruff format |
| `make typecheck` | Mypy |
| `make ci` | Lint + typecheck + tests |
| `make docker-build` | Build local image |
| `make docker-bake` | Multi-arch bake via `docker-bake.hcl` |
| `make compose-help` | Validate Compose file and list services |
| `alwm validate <file> <kind>` | Validate JSON against schema + Pydantic (`thought`, `event`, …) |
| `alwm providers show` | Print resolved provider config (API keys redacted) |

## Repository layout

```
├── AGENTS.md              # Agent / contributor conventions
├── docker-compose.yml
├── docker-bake.hcl
├── Dockerfile
├── Makefile
├── pyproject.toml
├── schemas/               # JSON/YAML schemas
├── templates/             # Markdown report templates
├── prompts/               # Versioned prompts
├── config/                # Optional provider YAML (see providers.example.yaml)
├── examples/              # Example artifacts
├── fixtures/              # Deterministic test inputs (growing)
├── src/agent_llm_wiki_matrix/
├── tests/
└── docs/
```

## License

MIT — see `LICENSE`.
