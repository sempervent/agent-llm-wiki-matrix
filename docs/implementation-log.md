# Implementation log

Chronological record of repository work. Latest entries first.

## 2026-04-17 — Phase 4 complete (pipelines + Compose test image)

**Delivered:**

- **Rubric** JSON Schema (`schemas/v1/rubric.schema.json`) + Pydantic models; `alwm validate … rubric`.
- **Pipelines:** `ingest_markdown_pages`, deterministic `evaluate_subject`, `evaluations_to_matrix`, `build_report_from_matrix` + Markdown renderers for `templates/matrix.md` and `templates/report.md`.
- **CLI:** `alwm ingest`, `evaluate`, `compare` (optional `--out-md`), `report`.
- **Docker:** `Dockerfile` `test` stage (editable `.[dev]` + pytest); Compose services `orchestrator` (dev), `tests` (test), `benchmark` (benchmark); `make compose-help` validates all profiles.
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
- Top-level: `README.md`, `AGENTS.md`, `pyproject.toml`, `Makefile`, `.gitignore`, `.env.example`, `Dockerfile`, `docker-compose.yml`, `docker-bake.hcl`.
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
