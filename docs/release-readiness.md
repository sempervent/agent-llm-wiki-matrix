# Release readiness — v0.1.0

This document summarizes what **v0.1.0** is intended to deliver versus what remains **partial**, **opt-in**, or **explicitly out of scope**. Command-backed evidence lives in [docs/audits/release-readiness-audit.md](audits/release-readiness-audit.md). A finer-grained live snapshot is in [docs/audits/current-capability-status.md](audits/current-capability-status.md).

---

## Complete capabilities (default workflows)

These are covered by **`just ci`** (lint, typecheck, unit tests excluding `tests/integration/`) and/or documented offline commands using **committed fixtures and examples**.

| Area | Notes |
| --- | --- |
| **Artifact validation** | `alwm validate <file> <kind>` for registered kinds (see `alwm validate --help` and `src/agent_llm_wiki_matrix/artifacts.py`). |
| **Pipelines** | `ingest`, `evaluate`, `compare`, `report` on repo examples under `examples/dataset/` (deterministic scoring). |
| **Prompt registry** | `alwm prompts check`, `list`, `show` against `prompts/registry.yaml`. |
| **Benchmark (offline)** | `ALWM_FIXTURE_MODE=1` + `alwm benchmark run` with `fixtures/benchmarks/*.yaml` or `benchmarks/v1/*.yaml`; outputs validate as benchmark artifacts; `manifest.json` as **`benchmark_manifest`**. |
| **Providers (unit)** | Mock and HTTP adapters tested without live network (`httpx` mocks). |
| **Browser (offline)** | Mock/file runners and `browser_evidence` validation in default tests. |
| **Docker** | `Dockerfile` `runtime` image; Compose profiles validate via `just compose-help`. |
| **Buildx Bake** | Default `orchestrator` build for **linux/amd64** and **linux/arm64** (see [Minimum supported environments](#minimum-supported-environments)). |

---

## Partial capabilities

| Area | Notes |
| --- | --- |
| **Live LLM backends** | Ollama and OpenAI-compatible HTTP paths exist and have opt-in integration tests; not required for merge or default CI. |
| **Playwright browser runner** | Optional extra `[browser]`; Compose `browser-verify` / Bake `browser-test` (**amd64-only** image target). |
| **Prompt registry in non-benchmark flows** | Registry is canonical for benchmark `prompt_ref`; other YAML may still use inline text. |

---

## Opt-in capabilities

Deliberately **not** in `just ci`: network, local daemons, or browser binaries.

| Mechanism | Notes |
| --- | --- |
| **`tests/integration/`** | Live Ollama / llama.cpp HTTP; Playwright smoke. |
| **`just verify-live-providers`** | Runs marked integration tests for live benchmarks. |
| **`just verify-playwright-local`** | Playwright file smoke with `ALWM_PLAYWRIGHT_SMOKE=1`. |
| **`just test-integration`** | Entire integration test subtree. |
| **Compose profiles** | `benchmark-ollama`, `benchmark-llamacpp`, `benchmark-probe`, `browser-verify`, etc. |

---

## Known non-goals for v0.1.0

- **Remote MCP browser tools** — Not shipped in v0.1.0; `MCPBrowserRunner` was (and remains) a **fixture bridge** only—see current **`docs/architecture/browser.md`** and **`docs/audits/capability-classification.md`**.
- **Default CI requiring live services** — No Ollama, llama-server, or Playwright install in `just ci`.
- **Hosted documentation site** — Docs live in-repo (`docs/`); no separate doc build is required for the tag.
- **Semantic LLM-as-judge rubrics** — Deterministic / fixture scoring is in scope; advanced LLM scoring is future work (see [docs/audits/mission-gap-audit.md](audits/mission-gap-audit.md) follow-ups).

---

## Minimum supported environments

These are **supported combinations** for building and running v0.1.0 as documented. Other environments may work but are not validated here.

### Local Python

| Requirement | Source of truth |
| --- | --- |
| **Python 3.11+** | `pyproject.toml` `requires-python = ">=3.11"`; `Dockerfile` uses `python:3.11-slim-bookworm`. |
| **Editable install** | `uv venv` + `uv pip install -e ".[dev]"`; run checks with **`uv run just ci`** (see `README.md` and **`AGENTS.md`**). |
| **CLI** | `alwm` console script from `[project.scripts]`. |

### Docker Compose

| Requirement | Notes |
| --- | --- |
| **Compose v2** | `docker compose` (see `README.md` / `just compose-help`). |
| **Profiles** | Validated by `just compose-help` (see audit). |

### Buildx Bake

| Requirement | Notes |
| --- | --- |
| **Buildx** | `docker buildx bake` with `docker-bake.hcl`. |
| **Default platforms** | `linux/amd64`, `linux/arm64` for `orchestrator`. |

### CPU architectures (container images)

| Architecture | Role |
| --- | --- |
| **amd64** | Primary CI/server target; full set of Bake targets including **`browser-test`**. |
| **arm64** | Apple Silicon and ARM64 Linux; supported for **`orchestrator`** / `orchestrator-arm64`; **`browser-test` is amd64-only** in `docker-bake.hcl`. |

---

## Tagging checklist

1. `just ci` passes on the release commit.
2. `alwm version` prints `0.1.0`.
3. `just compose-help` and `docker buildx bake --print` succeed (see audit).
4. [CHANGELOG.md](../CHANGELOG.md) includes `[0.1.0]` with date.
5. `git tag -a v0.1.0` after merge to the intended revision.
