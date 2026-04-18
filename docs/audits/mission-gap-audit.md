# Mission gap audit (code-verified)

**Last verified:** 2026-04-17 (stabilization refresh)  
**Method:** Inspect `src/agent_llm_wiki_matrix/`, run `just ci`, `just compose-help`, `just verify-live-providers`, `just verify-playwright-local`, representative `alwm` commands, and `docker buildx bake --print`. Claims below are backed by command output unless marked *static review*.

**Related:** `docs/audits/current-capability-status.md` (summary table), `docs/audits/capability-classification.md` (labeling rules), `docs/release-readiness.md` and `docs/audits/release-readiness-audit.md` (v0.1.0 tagging scope).

## Classification key

| Label | Meaning |
| --- | --- |
| **complete** | Implemented, exercised by tests and/or manual run in this audit |
| **partial** | Works for some paths; production/live path missing, untested, or env-dependent |
| **stub** | API exists; raises `NotImplementedError` or equivalent |
| **documented-only** | Described in docs/layout but no executable integration |
| **broken** | Intended behavior fails when run |

---

## 1. CLI capabilities

### `alwm validate`

| Status | **complete** |
| --- | --- |
| **Evidence** | `src/agent_llm_wiki_matrix/cli.py` (`cmd_validate`); `artifacts.py` registers kinds. |
| **Tests** | `tests/test_domain.py`, `tests/test_browser.py` (browser_evidence), etc. |
| **Run** | `alwm validate examples/v1/thought.json thought` → `ok: … (thought)`. |
| **Gap** | Only JSON files with registered kinds; use `alwm prompts check` for `prompts/registry.yaml`. |

### `alwm ingest` / `evaluate` / `compare` / `report`

| Status | **complete** |
| --- | --- |
| **Evidence** | `cli.py` → pipeline modules under `pipelines/`. |
| **Tests** | `tests/test_pipelines.py`, integration-style checks via fixtures. |

### `alwm benchmark run`

| Status | **complete** (offline default) |
| --- | --- |
| **Evidence** | `benchmark/runner.py`; inline `text` and/or `prompt_ref`; `manifest.json` includes optional `definition_source_relpath`, `prompt_registry_effective_ref` when recorded. |
| **Tests** | `tests/test_benchmark.py`, `tests/test_benchmark_prompt_registry.py`, `tests/test_benchmark_expansion.py`. |
| **Run** | `ALWM_FIXTURE_MODE=1 alwm benchmark run --definition fixtures/benchmarks/offline.v1.yaml --output-dir /tmp/…` → success; manifest shows `definition_source_relpath` when run via CLI from within repo. |

### `alwm benchmark probe` / `alwm providers show`

| Status | **complete** |
| --- | --- |
| **Evidence** | `benchmark/live_probe.py`; CLI wiring; `tests/test_live_probe.py`. |

### `alwm prompts` (`check` / `list` / `show`)

| Status | **complete** |
| --- | --- |
| **Evidence** | `prompt_registry.py`; `tests/test_prompt_registry.py`. |

---

## 2. Provider switching (mock, Ollama, OpenAI-compatible / llama.cpp)

| Status | **partial** |
| --- | --- |
| **What works** | `ProviderConfig.kind` ∈ `{mock, ollama, openai_compatible}`; `create_provider`; benchmark per-variant merge; `ALWM_FIXTURE_MODE=1` forces mock unless `--no-fixture-mock`. |
| **Tests** | `tests/test_providers.py` uses **httpx.MockTransport** (no live network). |
| **Live path** | **opt-in:** `tests/integration/test_live_benchmark_providers.py`, `just verify-live-providers`, Compose `benchmark-ollama` / `benchmark-llamacpp`. |

---

## 3. Browser evidence abstraction

| Status | **partial** |
| --- | --- |
| **Offline** | **complete:** `MockBrowserRunner`, `FileBrowserRunner`, `BrowserEvidence` validation (`tests/test_browser.py`). |
| **Playwright** | **partial (optional):** `browser/playwright_runner.py`, `[browser]` extra; `tests/integration/test_playwright_browser.py` with `ALWM_PLAYWRIGHT_SMOKE=1`; `just verify-playwright-local`; Compose **`browser-verify`**. |
| **MCP runner** | **partial:** fixtures **or** local stdio MCP (`browser/mcp_runner.py`, `browser/mcp_stdio.py`, `mcp` client); `alwm browser run-mcp` (`--stdio`); IDE/remote MCP not a v0.2.0 goal (`docs/roadmap/v0.2.0.md`). |

---

## 4. Docker Compose profiles

| Status | **complete** |
| --- | --- |
| **Evidence** | `docker-compose.yml` — `dev`, `test`, `benchmark`, `benchmark-offline`, `ollama` + `benchmark-ollama`, `benchmark-probe`, `benchmark-llamacpp`, `browser-verify`. |
| **Run** | `just compose-help` exited 0 and listed services (including `ollama` twice as dependency of multiple profiles): `orchestrator`, `tests`, `benchmark`, `benchmark-offline`, `ollama`, `benchmark-ollama`, `benchmark-probe`, `benchmark-llamacpp`, `browser-verify`. |

---

## 5. Docker Buildx Bake targets

| Status | **complete** |
| --- | --- |
| **Evidence** | `docker-bake.hcl`: `orchestrator` (default group), `orchestrator-amd64`, `orchestrator-arm64`, optional `browser-test` (linux/amd64). |
| **Run** | `docker buildx bake --print` returned resolved JSON for default `orchestrator` (platforms `linux/amd64`, `linux/arm64`). |

---

## 6. Prompt registry (`prompts/registry.yaml`)

| Status | **partial** |
| --- | --- |
| **Done** | Schema + `load_prompt_registry_yaml`; CLI `alwm prompts check|list|show`; benchmarks support **`prompt_ref`** + optional **`registry_version`**; `resolve_registry_yaml_path` exported; example suites under `examples/benchmark_suites/v1/suite.registry.*.v1.yaml`; tests in `test_prompt_registry.py`, `test_benchmark_prompt_registry.py`, `test_benchmark_expansion.py`. |
| **Remaining gap** | Non-benchmark pipelines (e.g. wiki ingest) do not require registry ids; inline prompt text in some YAML remains valid for one-offs. |

---

## 7. Test suite summary (default CI)

| Command | Result (stabilization refresh) |
| --- | --- |
| `just ci` (ruff + mypy + `pytest tests/ --ignore=tests/integration`) | **85 passed, 1 skipped** |
| `mypy src` | Success: **42** source files |

Test modules include: `test_benchmark`, `test_benchmark_cases`, `test_benchmark_expansion`, `test_benchmark_prompt_registry`, `test_browser`, `test_domain`, `test_example_campaigns`, `test_live_probe`, `test_pipelines`, `test_prompt_registry`, `test_providers`, `test_smoke`, and others under `tests/`.

---

## 8. Documentation drift (vs source of truth)

| Document | Notes |
| --- | --- |
| **`docs/implementation-log.md`** | Older “Known gaps” blocks in early phases are **historical**; prefer latest dated entries and `docs/audits/current-capability-status.md`. |
| **`AGENTS.md` / `README.md`** | Must match `just ci`, `justfile`, and CLI; capability labels per `capability-classification.md`. |
| **External Cursor rules** | If any still reference `Makefile` / `make ci`, treat as **stale** (repo uses `justfile`). |

---

## 9. Prioritized remediation (rolling)

1. **Live provider scheduling** — Optional scheduled/manual `just verify-live-providers` against real Ollama/llama-server; keep default CI offline (`AGENTS.md`).
2. **Implementation log hygiene** — Mark or archive obsolete Phase-1 “Known gaps” bullets so they are not read as current.
3. **Remote MCP browser tools** — Implement transport + tool mapping + tests per roadmap in `docs/architecture/browser.md`; until then capability stays **partial** (fixture bridge only).

---

## 10. Product follow-ups

High-value optional work remains: **LLM-assisted rubric scoring**, **MCP-based browser evidence**, and continued **benchmark/example** expansion using `prompt_ref` (see `docs/implementation-log.md`).

---

## Appendix: exact commands run (stabilization refresh)

```text
just ci
# 85 passed, 1 skipped; ruff + mypy clean

just compose-help
# services: orchestrator, tests, benchmark, benchmark-offline, ollama, benchmark-ollama,
#           benchmark-probe, benchmark-llamacpp, browser-verify

just verify-live-providers
# 2 skipped (no ALWM_LIVE_BENCHMARK_* / live services)

just verify-playwright-local
# 2 passed (with Playwright + ALWM_PLAYWRIGHT_SMOKE=1 in this environment)

docker buildx bake --print
# default target orchestrator, platforms linux/amd64 + linux/arm64

alwm validate examples/v1/thought.json thought
ALWM_FIXTURE_MODE=1 alwm benchmark run --definition fixtures/benchmarks/offline.v1.yaml --output-dir /tmp/alwm-stab/bench …
# manifest.json includes definition_source_relpath; prompt_registry_effective_ref null for inline-only defs

alwm prompts check
```
