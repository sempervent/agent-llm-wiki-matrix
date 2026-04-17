# agent-llm-wiki-matrix

Markdown-first, git-native **LLM wiki + comparison matrix** system for capturing ideas, experiments, evaluations, prompts, and reports as structured files. It supports reproducible benchmarking of multiple agent stacks and model backends (including local models via **Ollama** or switchable **OpenAI-compatible / llama.cpp** HTTP servers).

**Repository:** [github.com/sempervent/agent-llm-wiki-matrix](https://github.com/sempervent/agent-llm-wiki-matrix)  
**Changelog:** [CHANGELOG.md](CHANGELOG.md) · **v0.1.0 notes:** [docs/releases/v0.1.0.md](docs/releases/v0.1.0.md) · **Release scope:** [docs/release-readiness.md](docs/release-readiness.md)

Contributors and coding agents should follow **`AGENTS.md`** for the full operating manual (contribution loop, decision rules, prompt registry policy, verification expectations, **multi-agent parallel work**, capability labels). Parallel agents: see **`docs/workflows/multi-agent-parallel.md`**.

## Goals

- **Markdown-first, git-native** artifacts: notes, matrices, rubrics, and reports live in the repo.
- **Comparison matrices** across agent stacks, models, backends, prompts, browser behaviors, and orchestration patterns.
- **Docker Compose** for local orchestration; **Docker Buildx Bake** for multi-platform images (`linux/amd64`, `linux/arm64` by default).
- **Deterministic pipelines** where possible: typed contracts, schemas, fixtures, and testable ingest → evaluate → compare → summarize flows.
- **Provider abstraction** for Ollama and OpenAI-compatible endpoints (see `docs/architecture/target-state.md`).

## Prerequisites

- [just](https://github.com/casey/just) for project tasks (`brew install just` or see upstream install options)
- Docker with Buildx, Docker Compose v2 (for container workflows)
- Python **3.11+** (see `pyproject.toml` `requires-python`; the `Dockerfile` uses 3.11)

---

## Exact quickstart (local Python)

From the repository root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

alwm version
alwm info
alwm validate examples/v1/thought.json thought
alwm validate examples/v1/rubric.json rubric
alwm validate examples/browser_evidence/v1/export_flow.json browser_evidence
alwm browser prompt-block examples/browser_evidence/v1/export_flow.json
alwm providers show
just ci
```

Optional Playwright-based browser capture (not required for `just ci`):

```bash
# pip install -e ".[browser]" && playwright install chromium
# alwm browser run-playwright …
```

---

## Benchmark quickstart (offline)

Runs versioned YAML under `benchmarks/v1/` or `fixtures/benchmarks/` (see `benchmarks/v1/README.md`). Each **prompt** is inline `text:` and/or a `prompt_ref` into `prompts/registry.yaml`. Variants choose **agent stack**, **backend** (`mock` / `ollama` / `openai_compatible`), and **execution mode** (`cli`, `browser_mock`, `repo_governed`). With **`ALWM_FIXTURE_MODE=1`**, backends resolve to deterministic mock output unless you opt out.

```bash
ALWM_FIXTURE_MODE=1 alwm benchmark run \
  --definition fixtures/benchmarks/offline.v1.yaml \
  --output-dir out/benchmark-offline \
  --created-at 1970-01-01T00:00:00Z \
  --run-id local-bench

alwm validate out/benchmark-offline/manifest.json benchmark_manifest
alwm validate out/benchmark-offline/cells/v-cli__p-one/benchmark_response.json benchmark_response
```

Compose shortcuts (writes under `out/` in the mounted repo):

```bash
just benchmark-offline
just benchmark-ollama    # pull a model into the ollama service first
just benchmark-llamacpp  # start llama-server on the host (default :8080/v1)
```

---

## Prompt registry quickstart

The registry file is `prompts/registry.yaml` (versioned prompt bodies under `prompts/versions/`).

```bash
alwm prompts check
alwm prompts list
alwm prompts show scaffold.echo.v1
```

Benchmark definitions may reference prompts with `prompt_ref` (and optional `registry_version` pins). See `examples/benchmark_suites/v1/` and `docs/workflows/benchmarking.md`.

---

## Manifest validation example

Benchmark runs write `manifest.json`, validated as artifact kind **`benchmark_manifest`** (JSON Schema `schemas/v1/manifest.schema.json`).

```bash
alwm validate examples/v1/manifest.json benchmark_manifest
```

Example run trees under `examples/benchmark_runs/*/manifest.json` are also valid for spot checks.

---

## Optional live verification commands

These are **not** part of default `just ci`. They need live HTTP endpoints, env vars, and/or the `[browser]` extra.

| Command | Purpose |
| --- | --- |
| `just verify-live-providers` | Integration tests for Ollama / OpenAI-compatible benchmark paths (skip when unreachable) |
| `just verify-playwright-local` | Playwright smoke (`ALWM_PLAYWRIGHT_SMOKE=1`; install `[browser]` + browsers first) |
| `just test-integration` | Full `tests/integration/` |
| `just benchmark-probe` | `alwm benchmark probe` inside Compose (see `justfile`) |
| `docker compose --profile browser-verify run --rm browser-verify` | Playwright tests in container (profile `browser-verify`) |

Details: `docs/workflows/benchmarking.md`, `docs/workflows/live-verification.md`.

---

## End-to-end pipeline (offline scoring)

Full scripted walkthrough (committed paths only, temp dir for outputs): **`docs/workflows/walkthrough-v0.1.0.md`**.

Compact inline example:

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

---

## Docker

```bash
cp .env.example .env
docker build -t agent-llm-wiki-matrix:local -f Dockerfile .
docker run --rm agent-llm-wiki-matrix:local version
```

## Buildx Bake (multi-arch)

Default platforms: **linux/amd64** and **linux/arm64** (`docker-bake.hcl`).

```bash
docker buildx bake
docker buildx bake orchestrator-amd64
docker buildx bake orchestrator-arm64
```

## Compose (profiles)

```bash
docker compose --profile dev run --rm orchestrator version
docker compose --profile test run --rm tests
docker compose --profile benchmark run --rm benchmark
docker compose --profile benchmark-offline run --rm benchmark-offline
just compose-help
```

See `docs/workflows/local-dev.md` for profile details (`dev`, `test`, `benchmark`, `benchmark-offline`, `benchmark-ollama`, `benchmark-llamacpp`, `browser-verify`).

---

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
| `just test` | Run pytest (excludes `tests/integration/` live provider tests) |
| `just test-integration` | Opt-in live Ollama / OpenAI-compatible benchmark checks (`ALWM_LIVE_BENCHMARK_*`) |
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
| `just benchmark-probe` | `alwm benchmark probe` in Compose (Ollama + host OpenAI URL) |
| `just benchmark-llamacpp` | OpenAI-compatible endpoint on host → `out/benchmark-llamacpp` |
| `alwm validate <file> <kind>` | Validate JSON against schema + Pydantic (includes `browser_evidence`, `benchmark_manifest`) |
| `alwm browser prompt-block <file>` | Load browser evidence JSON → stable prompt-sized text |
| `alwm browser run-mock` | Run `MockBrowserRunner` (deterministic; no browser binary) |
| `alwm browser run-playwright` | Run `PlaywrightBrowserRunner` (requires `pip install -e ".[browser]"` and `playwright install …`; not used in default CI) |
| `alwm ingest <input_dir> <output_dir>` | Markdown pages → Thought JSON |
| `alwm evaluate --subject … --rubric … --out …` | Deterministic rubric scoring |
| `alwm compare <eval.json>… --out … [--out-md …]` | Evaluations → matrix JSON (+ optional matrix Markdown) |
| `alwm report --matrix … --out-json … --out-md …` | Matrix → report JSON + Markdown |
| `alwm providers show` | Print resolved provider config (API keys redacted) |
| `alwm benchmark probe` | Check Ollama + OpenAI-compatible HTTP APIs (for live runs) |
| `alwm benchmark run --definition … --output-dir … [--prompt-registry PATH]` | Full harness: responses → evals → matrices + report; `browser_mock` variants run the browser abstraction and write `browser_evidence.json`; Playwright requires `ALWM_BENCHMARK_PLAYWRIGHT=1` + `[browser]` extra |
| `alwm prompts check` / `list` / `show <id>` | Validate and read `prompts/registry.yaml` (paths relative to repo root) |

## Repository layout

```
├── AGENTS.md              # Operating manual for agents (mission, loops, verification, prompts)
├── CHANGELOG.md           # Version history
├── docker-compose.yml
├── docker-bake.hcl
├── Dockerfile
├── justfile               # just task runner (https://github.com/casey/just)
├── pyproject.toml
├── schemas/               # JSON Schemas (v1)
├── templates/             # Markdown report templates
├── prompts/               # Versioned prompts
├── config/                # Optional provider YAML (see providers.example.yaml)
├── examples/              # Example artifacts + dataset + generated matrix/report + browser evidence
├── benchmarks/v1/         # Versioned benchmark YAML
├── fixtures/              # Deterministic test inputs (+ benchmarks/, browser_evidence/)
├── src/agent_llm_wiki_matrix/
├── tests/
└── docs/
```

## License

MIT — see `LICENSE`.
