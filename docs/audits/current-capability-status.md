# Current capability status

**Last verified:** 2026-04-17 (stabilization pass; `just ci`, compose profiles, optional integration recipes).

**v0.1.0 release:** See [docs/release-readiness.md](../release-readiness.md) and [release-readiness-audit.md](release-readiness-audit.md).

This document is a **high-level snapshot**. For command-level evidence, see `docs/audits/mission-gap-audit.md` (refreshed with the same pass). For labeling rules in PRs, see `docs/audits/capability-classification.md`.

## Legend

| Label | Meaning |
| --- | --- |
| **complete** | Default CI (`just ci`) or documented offline workflow covers it. |
| **partial** | Shipped but needs optional deps, live services, or manual steps for full depth. |
| **stub** | API reserved; raises `NotImplementedError` or equivalent. |
| **opt-in** | Deliberately excluded from default CI; env flags or `tests/integration/`. |

## Core CLI and pipelines

| Area | Status | Notes |
| --- | --- | --- |
| `alwm validate` | **complete** | Registered JSON artifact kinds; schema + Pydantic. |
| `alwm ingest` / `evaluate` / `compare` / `report` | **complete** | Offline deterministic scoring path; tests in `tests/test_pipelines.py`, etc. |
| `alwm prompts check` / `list` / `show` | **complete** | `prompts/registry.yaml` + JSON Schema. |
| `alwm benchmark run` | **complete** (offline) | Mock/fixture mode; registry `prompt_ref` + inline `text`; manifest records `definition_source_relpath` / `prompt_registry_effective_ref` when applicable. |
| `alwm benchmark probe` | **complete** | HTTP reachability for Ollama + OpenAI-compatible; `tests/test_live_probe.py`. |
| `alwm providers show` | **complete** | Resolved config display. |

## Providers

| Area | Status | Notes |
| --- | --- | --- |
| Mock / Ollama / OpenAI-compatible adapters | **complete** (unit) | `httpx.MockTransport` in tests; no live network in `just ci`. |
| Live Ollama / llama.cpp HTTP | **partial** | **opt-in:** `tests/integration/test_live_benchmark_providers.py`, Compose profiles `benchmark-ollama`, `benchmark-llamacpp`, `just verify-live-providers`. |

## Browser

| Area | Status | Notes |
| --- | --- | --- |
| `MockBrowserRunner` / `FileBrowserRunner` / `BrowserEvidence` | **complete** | Default tests; no browser binary. |
| `PlaywrightBrowserRunner` | **partial** | **opt-in:** `[browser]` extra, `alwm browser run-playwright`, `ALWM_PLAYWRIGHT_SMOKE=1`, `just verify-playwright-local`, Compose **`browser-verify`** (`Dockerfile` target `browser-test`). |
| `MCPBrowserRunner` | **partial** | Fixtures + optional local **stdio MCP** (`ALWM_MCP_BROWSER_COMMAND`, `mcp` from **dev** extras); `alwm browser run-mcp`; IDE/remote MCP not a milestone goal—see `docs/architecture/browser.md`, `docs/roadmap/v0.2.0.md`. |

## Docker / Bake

| Area | Status | Notes |
| --- | --- | --- |
| Compose profiles (`dev`, `test`, `benchmark`, `benchmark-offline`, `benchmark-ollama`, `benchmark-probe`, `benchmark-llamacpp`, `browser-verify`) | **complete** | `just compose-help` validates config. |
| Buildx Bake (`orchestrator`, `orchestrator-amd64`, `orchestrator-arm64`, optional `browser-test`) | **complete** | `docker buildx bake --print` resolves HCL. |

## Tests

| Suite | Status | Notes |
| --- | --- | --- |
| `just ci` (`tests/` excluding `tests/integration/`) | **complete** | Deterministic; **85 passed, 1 skipped** at last stabilization. |
| `tests/integration/` | **opt-in** | Live providers + Playwright; skipped or gated by env. |

## Intentional non-goals (current)

- **IDE-hosted / remote MCP browser servers** — not a release goal; local stdio MCP client + fixture server is supported (`docs/architecture/browser.md`).
- **Default CI** — no Ollama, llama-server, or Playwright browsers required.
