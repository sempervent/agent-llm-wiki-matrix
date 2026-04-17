# Implementation log

Chronological record of repository work. Latest entries first.

## 2026-04-17 — Browser-backed benchmark execution

**Why:** `browser_mock` previously only tagged LLM output; benchmarks did not exercise `BrowserRunner` or persist evidence.

**Delivered:** `BrowserBenchConfig` + optional `variant.browser` in `benchmark/definitions.py` and `schemas/v1/benchmark_definition.schema.json`. `run_benchmark` calls `run_benchmark_browser_phase` for `execution_mode: browser_mock`, writes **`cells/.../browser_evidence.json`**, augments the provider prompt, and records **`browser_runner`** / **`browser_evidence_relpath`** on request/response/manifest cells. **`MCPBrowserRunner`** (`browser/mcp_runner.py`): fixture-backed bridge; remote MCP tools not wired. Playwright gated by **`ALWM_BENCHMARK_PLAYWRIGHT=1`**. Fixtures under `fixtures/benchmarks/browser_*.v1.yaml`; example `examples/benchmarks/v1/browser_file.v1.yaml`. Tests: `tests/test_benchmark_browser.py`. Docs: `docs/workflows/benchmarking.md`, `benchmarks/v1/README.md`, `docs/architecture/browser.md`, `docs/audits/capability-classification.md`. **`evaluation.schema.json`:** optional `scoring_backend` / `judge_provenance_relpath` (not in `required`) for Pydantic alignment.

**Verification:** `just ci` (default tests; no Playwright in CI).

## 2026-04-17 — Benchmark corpus expansion: taxonomy metadata + eight tagged suites

**Delivered:** `BenchmarkTaxonomyV1`, optional `time_budget_seconds`, `token_budget`, `retry_policy`, `tags`, `expected_artifact_kinds` on `BenchmarkDefinitionV1`; same fields on `BenchmarkRunManifest` and `schemas/v1/manifest.schema.json` (optional). New prompts `bench.task.runtime_config.v1`, `bench.task.multi_agent_coord.v1`; registry **0.3.0**. Eight example suites under `examples/benchmark_suites/v1/suite.taxonomy.*.v1.yaml` covering repo, runtime, docs, browser evidence, matrix reasoning, multi-agent coordination, campaign sweep, and integration stress. Fixture `fixtures/benchmarks/suite_taxonomy_minimal.v1.yaml`; example runs `examples/benchmark_runs/taxonomy-repo-governance/`, `taxonomy-runtime-config/`. Tests: `tests/test_benchmark_taxonomy.py`, manifest validation. Docs: `docs/workflows/benchmarking.md`, `examples/benchmark_suites/v1/README.md`. `schemas/v1/benchmark_taxonomy.schema.json` for standalone taxonomy JSON.

## 2026-04-17 — v0.1.0 release preparation

**Delivered:** First semver release tag readiness: `CHANGELOG.md`, `docs/releases/v0.1.0.md`, `docs/release-readiness.md`, `docs/audits/release-readiness-audit.md`, `docs/workflows/walkthrough-v0.1.0.md`. README quickstarts (exact local, benchmark, prompt registry, manifest validate, optional live verification) and `pyproject.toml` `urls` + sdist `CHANGELOG.md` include. Version metadata remains **0.1.0** (`pyproject.toml`, `__version__`). Evidence: `just ci` (85 passed, 1 skipped), `just compose-help`, `docker buildx bake --print`.

## 2026-04-17 — Post-merge stabilization (parallel tracks)

**Delivered:** Single coherent tree on `main`: lazy `run_benchmark` in `benchmark/__init__.py` to avoid `artifacts` ↔ `pipelines` import cycles after manifest consolidation; audit docs refreshed (`mission-gap-audit.md`, **`current-capability-status.md`**) with **85 passed, 1 skipped** from `just ci`; staged governance and benchmark expansion artifacts (registry suites, example runs, `test_benchmark_expansion`).

## 2026-04-17 — Benchmark manifest: JSON Schema + `benchmark_manifest` artifact kind

**Delivered:** `schemas/v1/manifest.schema.json` (Draft 2020-12); `BenchmarkRunManifest` / `BenchmarkCellArtifactPaths` moved to **`models.py`** (re-exported from `benchmark/manifest.py`) to avoid import cycles with `artifacts.py`. Registered `benchmark_manifest` in `artifacts.py`; `write_benchmark_manifest` in `benchmark/persistence.py` validates against JSON Schema before writing; `run_benchmark` uses it. CLI: `alwm validate … benchmark_manifest`. Fixture `fixtures/v1/manifest.json`; tests `tests/test_manifest.py` + `test_domain` / `test_benchmark` hooks. Docs: `data-model.md`, `benchmarking.md`, `examples/v1/README.md`. Committed example runs under `examples/benchmark_runs/` unchanged (backward compatible: optional provenance keys omitted).

## 2026-04-17 — Benchmark expansion: registry suites, comparison rubric, manifest provenance

**Delivered:** Four versioned prompts under `prompts/versions/` (`bench.task.repo_governed.v1`, `markdown_synthesis`, `matrix_reasoning`, `browser_evidence`) registered in `prompts/registry.yaml` (**0.2.0**). New rubric `examples/dataset/rubrics/comparison.v1.json` (structure / task_fit / grounding / brevity). Three example suites: `suite.registry.four_modes.v1.yaml`, `suite.registry.strict_duo.v1.yaml`, `suite.registry.generous_duo.v1.yaml`; fixture mirror `fixtures/benchmarks/suite_four_modes.v1.yaml`. Committed offline runs under `examples/benchmark_runs/registry-four-modes`, `registry-strict-duo`, `registry-generous-duo`. `BenchmarkRunManifest` + `run_benchmark(..., definition_source_relpath=...)` + CLI wiring for optional manifest fields. Tests: `tests/test_benchmark_expansion.py`. Docs: `data-model.md`, `evaluation-pipeline.md`, `benchmarking.md`, `examples/benchmark_suites/v1/README.md`.

## 2026-04-17 — Runtime hardening: live verification paths

**Delivered:** `PlaywrightBrowserRunner` exported from `playwright_runner` (MCP-only stub file); `create_browser_runner(..., "playwright")`; Dockerfile target **`browser-test`** (Playwright + Chromium); Compose profile **`browser-verify`**; `docker-bake.hcl` target `browser-test` (linux/amd64); `just` recipes `verify-live-providers`, `verify-playwright-local`, `browser-verify`; `pytest` marker **`live_playwright`**; `tests/integration/test_playwright_browser.py` marked `integration` + `live_playwright`; **`docs/workflows/live-verification.md`**; `docs/architecture/runtime.md` refresh; workflow cross-links; `.env.example` notes `ALWM_PLAYWRIGHT_SMOKE`. Default **`just ci`** unchanged (`tests/integration/` still excluded).

## 2026-04-17 — Governance: AGENTS manual, multi-agent workflow, capability audit

**Why:** Reduce drift between docs and implementation; make parallel agent work predictable; require evidence-backed labels (“complete” vs partial/stub).

**What changed:**

- **`AGENTS.md`** — Stronger operating manual: non-goals folded into success criteria (evidence-backed claims), multi-agent rules (summary + pointer), expanded anti-patterns, verification table (Playwright opt-in), links to **`docs/audits/capability-classification.md`**, updated browser decision rule (Playwright optional; MCP stub), layout includes `docs/audits/`, `docs/examples/`, `docs/workflows/multi-agent-parallel.md`.
- **`docs/workflows/multi-agent-parallel.md`** — Branch strategy, file ownership zones, conflict avoidance, merge order, required handoff template.
- **`docs/audits/capability-classification.md`** — Taxonomy: complete / partial / stub / documented-only / broken + evidence bar and repository examples (re-verify after changes).
- **`docs/examples/README.md`** — Clarifies repo-root **`examples/`** vs `docs/examples/`.
- **Drift repair** — **`README.md`**: `alwm browser run-playwright`, optional `[browser]` install comment, pointer to multi-agent doc. **`docs/architecture/browser.md`**, **`current-state.md`**, **`runtime.md`**: Playwright optional; MCP stub; prompt registry **implemented** in current-state. **`docs/audits/mission-gap-audit.md`**: browser §3 and doc-drift rows updated; P3 reframed to MCP runner.

**Verification:** Documentation-only change set; command names cross-checked against `src/agent_llm_wiki_matrix/cli.py` (`browser run-playwright`, `benchmark probe`, `prompts` group).

## 2026-04-17 — AGENTS.md operating manual

**Why:** The old `AGENTS.md` was principles-only; agents needed actionable rules for this repo (benchmarks, prompt registry, integration tests, browser stubs, documentation touchpoints).

**What changed:** Expanded `AGENTS.md` with mission/success criteria, required contribution loop, decision table (including **prefer `prompt_ref` over duplicated inline prompt text** where appropriate), anti-patterns, verification/reporting table, documentation update rules, completion vs partial vs stubbed definitions, and project-specific examples (implementation, auditing, drift repair, benchmarks, browser). README now points contributors to `AGENTS.md` for the full manual.

**How to use it:** Before sizable work, read Mission, Contribution loop, and Prompt registry sections; after work, satisfy Verification + Documentation update rules and add an implementation-log entry when behavior or contracts shift.

## 2026-04-17 — Registry-backed benchmark prompts

**Delivered:** `PromptItem` supports `text` xor `prompt_ref` (+ optional `registry_version` pin); `BenchmarkDefinitionV1.prompt_registry_ref`; `resolve_benchmark_prompts` (`benchmark/prompt_resolution.py`) using `load_prompt_registry_yaml`; `run_benchmark(..., prompt_registry_path=...)` and CLI `--prompt-registry`; `BenchmarkRequestRecord` / `BenchmarkResponse` fields `prompt_source`, `prompt_registry_id`, `registry_document_version`, `prompt_source_relpath`; JSON Schema updates + `schemas/v1/benchmark_definition.schema.json`. Fixtures under `fixtures/prompt_registry/` and `fixtures/benchmarks/registry_*.yaml`; tests `tests/test_benchmark_prompt_registry.py`; example `examples/benchmark_suites/v1/registry.mixed.v1.yaml` + committed run `examples/benchmark_runs/registry-mixed/`. Prompt `bench.sample.prompt.v1` added under `prompts/`.

## 2026-04-17 — Live benchmark verification (Compose + opt-in integration tests)

**Delivered:** `benchmark/live_probe.py`; CLI `alwm benchmark probe`; Ollama healthcheck + `service_healthy` for `benchmark-ollama`; Compose profile **`benchmark-probe`** (`just benchmark-probe`); integration tests under `tests/integration/` gated by `ALWM_LIVE_BENCHMARK_OLLAMA` / `ALWM_LIVE_BENCHMARK_LLAMACPP` with skips when unreachable; `just test` ignores `tests/integration/`; `tests/test_live_probe.py` unit tests.

## 2026-04-17 — Mission gap audit + prompt registry CLI

**Delivered:** `docs/audits/mission-gap-audit.md` (code-verified status of CLI, providers, browser layer, Compose, Bake; drift notes). **Prompt registry wiring:** `schemas/v1/prompt_registry.schema.json`, `prompt_registry.py` (YAML load + JSON Schema + path safety), CLI `alwm prompts check|list|show`, tests `tests/test_prompt_registry.py`. README and `AGENTS.md` updated for new commands.

## 2026-04-17 — Browser execution abstraction

**Delivered:** `BrowserRunner` ABC; `BrowserEvidence` JSON Schema + Pydantic models; `MockBrowserRunner` and `FileBrowserRunner`; fixture `fixtures/browser_evidence/v1/export_flow.json`; `PlaywrightBrowserRunner` / `MCPBrowserRunner` stubs (`NotImplementedError`); `load_browser_evidence`, `evidence_to_prompt_block`; artifact kind `browser_evidence` for `alwm validate`; CLI `alwm browser prompt-block` and `alwm browser run-mock`; tests `tests/test_browser.py`; `docs/architecture/browser.md`.

**Not in scope:** live Playwright or MCP browser automation (stubs only).

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
