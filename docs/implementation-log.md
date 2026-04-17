# Implementation log

Chronological record of repository work. Latest entries first.

## 2026-04-17 — Benchmark run artifact persistence

**Delivered:** Structured output under `cells/`, `matrices/`, `markdown/`, `reports/` with stable `cell_id` slugs, **benchmark_request** + raw/normalized response text files, aggregate **benchmark_response**, per-cell **evaluation**, **matrix_grid_inputs** / **matrix_pairwise_inputs**, and manifest **cells[]** index; execution layer returns raw vs normalized text.

## 2026-04-17 — Replace Makefile with justfile

**Delivered:** [just](https://github.com/casey/just) `justfile` with the same recipes as the former Makefile (`ci`, lint, compose-help, benchmark profiles, etc.); removed `Makefile`; documentation and `AGENTS.md` now reference `just …`.

## 2026-04-17 — Benchmark case schema (v1) + task examples

**Delivered:**

- JSON Schema `schemas/v1/benchmark_case.schema.json` and Pydantic `BenchmarkCase` / `BenchmarkExecutionMetadata` with validation that `expected_artifact_kinds` references registered `alwm validate` kinds.
- Loader `benchmark/cases.py` (`load_benchmark_case`, `validate_benchmark_case_file`).
- Catalog `benchmarks/cases/v1/` with four task kinds: repo scaffolding, Markdown synthesis, comparison matrix, browser-evidence interpretation; mirrored under `fixtures/benchmark_cases/v1/` and `examples/benchmark_cases/v1/`.
- Tests: `tests/test_benchmark_cases.py`.

## 2026-04-17 — Phase 5 complete (benchmark harness)

**Delivered:**

- **Provider execution:** `providers/execution.py` applies deterministic execution-mode tags (`cli`, `browser_mock`, `repo_governed`) on top of the same `CompletionRequest` for all backends.
- **Backend selection:** `providers/benchmark_config.py` merges global YAML/env with per-variant `mock` / `ollama` / `openai_compatible` settings; `ALWM_FIXTURE_MODE=1` forces mock unless `--no-fixture-mock`.
- **Benchmark definitions:** Pydantic `BenchmarkDefinitionV1` + `load_benchmark_definition` for YAML/JSON under `benchmarks/v1/` (mirrored in `fixtures/benchmarks/` for tests).
- **Artifacts:** `schemas/v1/benchmark_response.schema.json`, `BenchmarkResponse` model, `alwm validate … benchmark_response`.
- **Pipeline:** `benchmark/runner.py` stores raw responses, rubric-evaluates each cell, builds **grid** and **pairwise** `ComparisonMatrix` JSON + Markdown, `report.json` / `report.md`, and `manifest.json`.
- **CLI:** `alwm benchmark run --definition … --output-dir …`.
- **Compose / just:** profiles **`benchmark-offline`**, **`benchmark-ollama`** (+ `ollama` service), **`benchmark-llamacpp`**; recipes `just benchmark-offline`, `just benchmark-ollama`, `just benchmark-llamacpp`.
- **Tests:** `tests/test_benchmark.py` asserts deterministic offline matrix output and validates artifacts.

**Next:** Richer prompt registry wiring; optional LLM rubric; real browser trace ingestion.

## 2026-04-17 — Phase 4 complete (pipelines + Compose test image)

**Delivered:**

- **Rubric** JSON Schema (`schemas/v1/rubric.schema.json`) + Pydantic models; `alwm validate … rubric`.
- **Pipelines:** `ingest_markdown_pages`, deterministic `evaluate_subject`, `evaluations_to_matrix`, `build_report_from_matrix` + Markdown renderers for `templates/matrix.md` and `templates/report.md`.
- **CLI:** `alwm ingest`, `evaluate`, `compare` (optional `--out-md`), `report`.
- **Docker:** `Dockerfile` `test` stage (editable `.[dev]` + pytest); Compose services `orchestrator` (dev), `tests` (test), `benchmark` (benchmark); `just compose-help` validates all profiles.
- **Examples:** `examples/dataset/` wiki pages, evaluations, thoughts, and `examples/generated/` matrix + report pair; tests validate checked-in generated JSON.
- **Docs:** Updated `docs/workflows/*`, `docs/architecture/current-state.md`, `docs/architecture/evaluation-pipeline.md`, `docs/architecture/runtime.md`, and `README.md` with exact commands.

**Next:** Optional LLM-assisted scoring behind providers; richer ingest extraction; browser evidence fixtures.

## 2026-04-17 — Phase 3 complete (provider abstraction)

**Delivered:**

- `BaseProvider` + `CompletionRequest` contract.
- `MockProvider` (deterministic, no network).
- `OllamaProvider` (`/api/chat`) and `OpenAICompatibleProvider` (`/v1/chat/completions`) using `httpx` with injectable `MockTransport` for tests.
- `ProviderConfig` loaded from optional YAML + environment overrides (`load_provider_config`).
- Example YAML: `config/providers.example.yaml`; local `config/providers.yaml` gitignored.
- CLI: `alwm providers show` prints redacted configuration.
- Tests in `tests/test_providers.py` (mocked HTTP only).

**Next:** Phase 4 — ingest pipeline, claim extraction stubs, rubric evaluation, matrix persistence.

## 2026-04-17 — Phase 2 complete (domain models + schemas)

**Delivered:**

- JSON Schemas under `schemas/v1/` for `thought`, `event`, `experiment`, `evaluation`, `matrix`, `report` (plus existing `note`).
- Pydantic models in `src/agent_llm_wiki_matrix/models.py` with extra validation for matrix score shapes.
- `src/agent_llm_wiki_matrix/artifacts.py` for dual JSON Schema + Pydantic validation.
- CLI: `alwm validate <path> <kind>`.
- Fixtures: `fixtures/v1/*.json`; examples mirrored under `examples/v1/`.
- Markdown templates: `templates/thought.md`, `event.md`, `experiment.md`, `evaluation.md`, `matrix.md`, `report.md` (plus weekly stub).
- Tests: `tests/test_domain.py`, `tests/conftest.py` (repo root + cwd for deterministic schema resolution).

**Next:** Phase 3 — provider abstraction (`BaseProvider`, Ollama, OpenAI-compatible HTTP, mock) with YAML/env configuration.

## 2026-04-17 — Phase 1 complete (scaffold)

**Audit:** Initial repository contained only `LICENSE`. No prior scaffold to migrate.

**Delivered:**

- Repository layout: `src/agent_llm_wiki_matrix/`, `tests/`, `docs/`, `schemas/`, `templates/`, `prompts/`, `examples/`, `fixtures/`.
- Top-level: `README.md`, `AGENTS.md`, `pyproject.toml`, `justfile`, `.gitignore`, `.env.example`, `Dockerfile`, `docker-compose.yml`, `docker-bake.hcl`.
- Python package: Click CLI (`alwm`), structlog-based logging, JSON Schema helpers (`schema.py`) with path-aware caching.
- Schemas: `schemas/v1/note.schema.json`; example `examples/sample-note.json`.
- Prompt registry skeleton: `prompts/registry.yaml` + `prompts/versions/scaffold.echo.v1.txt`.
- Report template skeleton: `templates/report-weekly.md`.
- Smoke tests: CLI and schema validation (`tests/test_smoke.py`).
- Docker: orchestrator image (`Dockerfile`); Compose profiles `dev`, `test`, `benchmark`; Bake targets for multi-arch and single-arch convenience (`orchestrator-amd64`, `orchestrator-arm64`).

**Known gaps (by design until later phases):**

- Domain models beyond minimal `note` schema (Phase 2).
- Provider adapters (Phase 3).
- Ingest/evaluate/matrix/report pipelines (Phases 4–5).
- Compose services for Ollama / model endpoints (Phase 6; placeholder comment in `docker-compose.yml`).

**Next:** Phase 2 — domain models and schemas for thought, event, experiment, evaluation, matrix, report; validators; expanded fixtures and examples.
