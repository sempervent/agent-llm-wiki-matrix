# agent-llm-wiki-matrix

Markdown-first, git-native **LLM wiki + comparison matrix** system for capturing ideas, experiments, evaluations, prompts, and reports as structured files. It supports reproducible benchmarking of multiple agent stacks and model backends (including local models via **Ollama** or switchable **OpenAI-compatible / llama.cpp** HTTP servers).

**Repository:** [github.com/sempervent/agent-llm-wiki-matrix](https://github.com/sempervent/agent-llm-wiki-matrix)

## Goals

- **Markdown-first, git-native** artifacts: notes, matrices, rubrics, and reports live in the repo.
- **Comparison matrices** across agent stacks, models, backends, prompts, browser behaviors, and orchestration patterns.
- **Docker Compose** for local orchestration; **Docker Buildx Bake** for multi-platform images (`linux/amd64`, `linux/arm64` by default).
- **Deterministic pipelines** where possible: typed contracts, schemas, fixtures, and testable ingest → evaluate → compare → summarize flows.
- **Provider abstraction** for Ollama and OpenAI-compatible endpoints (see `docs/architecture/target-state.md`).

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
alwm validate examples/v1/rubric.json rubric
alwm providers show
make ci
```

### End-to-end pipeline (offline scoring)

```bash
alwm ingest examples/dataset/pages examples/dataset/thoughts --created-at 1970-01-01T00:00:00Z
alwm evaluate --subject examples/dataset/pages/retrieval-basics.md \
  --rubric examples/v1/rubric.json \
  --out examples/dataset/evals/retrieval-basics.eval.json --id eval-retrieval-basics
alwm compare examples/dataset/evals/retrieval-basics.eval.json \
  examples/dataset/evals/chunking-strategies.eval.json \
  --out examples/generated/wiki_matrix.json \
  --out-md examples/generated/wiki_matrix.md \
  --id wiki-matrix-001 \
  --title "Wiki pages (example dataset)"
alwm report --matrix examples/generated/wiki_matrix.json \
  --out-json examples/generated/wiki_report.json \
  --out-md examples/generated/wiki_report.md \
  --id wiki-report-001
alwm validate examples/generated/wiki_matrix.json matrix
alwm validate examples/generated/wiki_report.json report
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
docker buildx bake orchestrator-arm64
```

### Compose (profiles)

```bash
docker compose --profile dev run --rm orchestrator version
docker compose --profile test run --rm tests
docker compose --profile benchmark run --rm benchmark
make compose-help
```

See `docs/workflows/local-dev.md` for profile details (`dev`, `test`, `benchmark`).

## Architecture (summary)

| Layer | Role |
| --- | --- |
| **Docs** | `docs/` — architecture, workflows, implementation log |
| **Schemas** | JSON Schema for structured artifacts under `schemas/` |
| **Templates** | Markdown templates under `templates/` |
| **Prompts** | Versioned prompt registry under `prompts/` |
| **Python package** | `src/agent_llm_wiki_matrix` — CLI, pipelines, validators |
| **Docker** | `Dockerfile`, `docker-compose.yml`, `docker-bake.hcl` |

Detailed diagrams and data flow: `docs/architecture/runtime.md`, `docs/architecture/data-model.md`, `docs/architecture/evaluation-pipeline.md`.

## Commands (Makefile and CLI)

| Command | Description |
| --- | --- |
| `make install-dev` | Editable install with dev dependencies |
| `make test` | Run pytest |
| `make smoke` | Smoke tests only |
| `make lint` | Ruff check |
| `make fmt` | Ruff format |
| `make typecheck` | Mypy |
| `make ci` | Lint + typecheck + tests |
| `make docker-build` | Build local image (`runtime` target) |
| `make docker-bake` | Multi-arch bake via `docker-bake.hcl` |
| `make compose-help` | Validate Compose for `dev`, `test`, `benchmark` and list services |
| `alwm validate <file> <kind>` | Validate JSON against schema + Pydantic |
| `alwm ingest <input_dir> <output_dir>` | Markdown pages → Thought JSON |
| `alwm evaluate --subject … --rubric … --out …` | Deterministic rubric scoring |
| `alwm compare <eval.json>… --out … [--out-md …]` | Evaluations → matrix JSON (+ optional matrix Markdown) |
| `alwm report --matrix … --out-json … --out-md …` | Matrix → report JSON + Markdown |
| `alwm providers show` | Print resolved provider config (API keys redacted) |

## Repository layout

```
├── AGENTS.md              # Agent / contributor conventions
├── docker-compose.yml
├── docker-bake.hcl
├── Dockerfile
├── Makefile
├── pyproject.toml
├── schemas/               # JSON Schemas (v1)
├── templates/             # Markdown report templates
├── prompts/               # Versioned prompts
├── config/                # Optional provider YAML (see providers.example.yaml)
├── examples/              # Example artifacts + dataset + generated matrix/report
├── fixtures/              # Deterministic test inputs
├── src/agent_llm_wiki_matrix/
├── tests/
└── docs/
```

## License

MIT — see `LICENSE`.
