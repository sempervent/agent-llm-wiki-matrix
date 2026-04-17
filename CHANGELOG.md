# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-04-17

First tagged release: offline-first CLI, pipelines, benchmark harness, prompt registry, JSON Schema artifacts, and Docker tooling. See [docs/releases/v0.1.0.md](docs/releases/v0.1.0.md) for narrative notes and [docs/release-readiness.md](docs/release-readiness.md) for capability scope.

### Added

- **`alwm` CLI** — `validate`, ingest / evaluate / compare / report, `prompts` (check / list / show), `benchmark` (run / probe), `browser` helpers, `providers show`.
- **Pipelines** — Markdown ingest → rubric evaluation → comparison matrix → report (deterministic, tested offline).
- **Benchmark harness** — Versioned YAML definitions; inline prompts and `prompt_ref` into `prompts/registry.yaml`; mock / Ollama / OpenAI-compatible backends; matrices and `manifest.json` as **`benchmark_manifest`** artifacts.
- **Prompt registry** — `prompts/registry.yaml` with versioned prompt files under `prompts/versions/`.
- **Schemas** — JSON Schema under `schemas/v1/` for artifacts, rubrics, benchmark I/O, and run manifests.
- **Docker** — `Dockerfile` (`python:3.11-slim`), Compose profiles for dev/test/benchmark and optional live probes, `docker-bake.hcl` for multi-arch **`linux/amd64`** and **`linux/arm64`** (`orchestrator` target).
- **Quality** — `just ci` (ruff, mypy, pytest excluding `tests/integration/`); opt-in integration tests for live providers and Playwright.

### Documentation

- Architecture and workflow docs under `docs/`.
- Audits: mission gap, capability classification, current capability status, **release-readiness** ([docs/release-readiness.md](docs/release-readiness.md)), and [docs/audits/release-readiness-audit.md](docs/audits/release-readiness-audit.md) (command-backed evidence).

[0.1.0]: https://github.com/sempervent/agent-llm-wiki-matrix/releases/tag/v0.1.0
