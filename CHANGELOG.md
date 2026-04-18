# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Ollama (gpt-oss:20b)** — `just ollama-gptoss-setup` starts Compose Ollama, pulls **`gpt-oss:20b`**, verifies with **`alwm benchmark probe`**; **`just smoke-ollama-live`** runs a minimal live benchmark. Defaults (**`OLLAMA_MODEL`**, **`benchmarks/v1/ollama.v1.yaml`**, **`alwm benchmark probe`**) use that tag; docs include migration from the old named Docker volume to **`./.ollama-models`**.
- **Campaign orchestration** — `alwm benchmark campaign run` with **`--dry-run`** (plans sweep: `manifest.json`, `campaign-summary.*`, `campaign-dry-run.json` without member `runs/`). Artifact kinds **`campaign_definition`**, **`campaign_manifest`**, **`campaign_summary`** (aliases align with **`benchmark_campaign_*`**). Campaign manifests record fingerprints (**`campaign_definition_fingerprint`**, **`campaign_experiment_fingerprints`** as of **[0.2.0]**), timing, git provenance, **`run_status_summary`**, optional per-run failures, and **`inputs_snapshot`** for audits; member runs still use **`run_benchmark`**.
- **Documentation** — `docs/wiki/campaign-orchestration.md`, `docs/tracking/campaign-orchestration.md`, ADR `docs/adr/0001-campaign-orchestration.md` (see also `docs/architecture/adr/0001-benchmark-campaign-orchestration.md`); workflow and README updates; longitudinal compatibility documented.

## [0.2.0] — 2026-04-18

### Added

- **Benchmark `comparison_fingerprints` (six axes)** — `manifest.json` includes **`prompt_registry_state`**: hash of the effective prompt registry YAML when `prompt_ref` prompts are used, or an inline-only sentinel when all prompts are inline.
- **Campaign `campaign_experiment_fingerprints` (six axes)** — `campaign_definition`, **`suite_definitions`**, **`provider_configs`**, **`scoring_configs`**, **`browser_configs`**, and **`prompt_registry_state`** on campaign **`manifest.json`** and **`campaign-summary.json`** for longitudinal grouping and audits.
- **Longitudinal reporting** — `group_snapshots_by` key **`prompt_registry_state_fingerprint`**; **`provider-comparison.md`** includes a **Registry** column alongside the other fingerprint columns.

### Changed

- **`campaign_definition_fingerprint`** — canonical identity hash (cosmetic fields excluded; stable list ordering); aligns with the **`campaign_definition`** field inside **`campaign_experiment_fingerprints`**.

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
[0.2.0]: https://github.com/sempervent/agent-llm-wiki-matrix/releases/tag/v0.2.0
