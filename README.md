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

- [just](https://github.com/casey/just) for project tasks (`brew install just` or see upstream install options)
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
just ci
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

### Benchmark harness (prompts × variants × backends)

Runs versioned YAML under `benchmarks/v1/` (see `benchmarks/v1/README.md`). Each variant specifies **agent stack**, **backend** (`mock` / `ollama` / `openai_compatible`), and **execution mode** (`cli`, `browser_mock`, `repo_governed`). Responses are stored as `benchmark_response` JSON, scored with the rubric, then aggregated into **grid** and **pairwise** matrices plus reports.

```bash
ALWM_FIXTURE_MODE=1 alwm benchmark run \
  --definition fixtures/benchmarks/offline.v1.yaml \
  --output-dir out/benchmark-offline \
  --created-at 1970-01-01T00:00:00Z \
  --run-id local-bench
alwm validate out/benchmark-offline/cells/v-cli__p-one/benchmark_response.json benchmark_response
```

Compose shortcuts (writes under `out/` in the mounted repo):

```bash
just benchmark-offline
just benchmark-ollama    # pull a model into the ollama service first
just benchmark-llamacpp    # start llama-server on the host (default :8080/v1)
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
docker compose --profile benchmark-offline run --rm benchmark-offline
just compose-help
```

See `docs/workflows/local-dev.md` for profile details (`dev`, `test`, `benchmark`, `benchmark-offline`, `benchmark-ollama`, `benchmark-llamacpp`).

## Architecture (summary)

| Layer | Role |
| --- | --- |
| **Docs** | `docs/` — architecture, workflows, implementation log |
| **Schemas** | JSON Schema for structured artifacts under `schemas/` |
| **Templates** | Markdown templates under `templates/` |
| **Prompts** | Versioned prompt registry under `prompts/` |
| **Python package** | `src/agent_llm_wiki_matrix` — CLI, pipelines, benchmark harness, validators |
| **Benchmarks** | `benchmarks/v1/*.yaml` — versioned definitions; `fixtures/benchmarks/` for tests |
| **Docker** | `Dockerfile`, `docker-compose.yml`, `docker-bake.hcl` |

Detailed diagrams and data flow: `docs/architecture/runtime.md`, `docs/architecture/data-model.md`, `docs/architecture/evaluation-pipeline.md`.

## Commands (just and CLI)

Run `just` with no arguments to list recipes. Common tasks:

| Command | Description |
| --- | --- |
| `just install-dev` | Editable install with dev dependencies |
| `just test` | Run pytest |
| `just smoke` | Smoke tests only |
| `just lint` | Ruff check |
| `just fmt` | Ruff format |
| `just typecheck` | Mypy |
| `just ci` | Lint + typecheck + tests |
| `just docker-build` | Build local image (`runtime` target) |
| `just docker-bake` | Multi-arch bake via `docker-bake.hcl` |
| `just compose-help` | Validate Compose for dev/test/benchmark + benchmark-offline/ollama/llamacpp |
| `just benchmark-offline` | Run mock benchmark via Compose → `out/benchmark-offline` |
| `just benchmark-ollama` | Ollama service + smoke benchmark → `out/benchmark-ollama` |
| `just benchmark-llamacpp` | OpenAI-compatible endpoint on host → `out/benchmark-llamacpp` |
| `alwm validate <file> <kind>` | Validate JSON against schema + Pydantic |
| `alwm ingest <input_dir> <output_dir>` | Markdown pages → Thought JSON |
| `alwm evaluate --subject … --rubric … --out …` | Deterministic rubric scoring |
| `alwm compare <eval.json>… --out … [--out-md …]` | Evaluations → matrix JSON (+ optional matrix Markdown) |
| `alwm report --matrix … --out-json … --out-md …` | Matrix → report JSON + Markdown |
| `alwm providers show` | Print resolved provider config (API keys redacted) |
| `alwm benchmark run --definition … --output-dir …` | Full harness: responses → evals → matrices → report |

## Repository layout

```
├── AGENTS.md              # Agent / contributor conventions
├── docker-compose.yml
├── docker-bake.hcl
├── Dockerfile
├── justfile               # just task runner (https://github.com/casey/just)
├── pyproject.toml
├── schemas/               # JSON Schemas (v1)
├── templates/             # Markdown report templates
├── prompts/               # Versioned prompts
├── config/                # Optional provider YAML (see providers.example.yaml)
├── examples/              # Example artifacts + dataset + generated matrix/report
├── benchmarks/v1/         # Versioned benchmark YAML
├── fixtures/              # Deterministic test inputs (+ benchmarks/)
├── src/agent_llm_wiki_matrix/
├── tests/
└── docs/
```

## License

MIT — see `LICENSE`.
