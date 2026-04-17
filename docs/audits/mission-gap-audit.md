# Mission gap audit (code-verified)

**Date:** 2026-04-17  
**Method:** Inspect `src/agent_llm_wiki_matrix/`, run `just compose-help`, `pytest`, representative `alwm` commands, and `docker buildx bake --print`. Claims below are backed by command output unless marked *static review*.

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
| **Run** | `alwm validate examples/v1/thought.json thought` → `ok: … (thought)`; `alwm validate examples/v1/rubric.json rubric` → ok. |
| **Gap** | Only JSON files with registered kinds; use `alwm prompts check` for `prompts/registry.yaml`. |

### `alwm ingest`

| Status | **complete** |
| --- | --- |
| **Evidence** | `cli.py` → `ingest_markdown_pages` (`pipelines/ingest.py`). |
| **Run** | Ingest to `/tmp/alwm-audit-out/thoughts` wrote two `*.thought.json` files. |

### `alwm evaluate`

| Status | **complete** |
| --- | --- |
| **Evidence** | `cli.py` → `evaluate_subject` (deterministic pipeline evaluator). |
| **Run** | Wrote `/tmp/alwm-audit-out/evals/retrieval.eval.json`. |

### `alwm compare`

| Status | **complete** |
| **Evidence** | `cli.py` → `evaluations_to_matrix`. |
| **Run** | Wrote `matrix.json` and `matrix.md`. |

### `alwm report`

| Status | **complete** |
| **Evidence** | `cli.py` → `build_report_from_matrix` + Markdown render. |
| **Run** | Wrote `report.json` and `report.md`. |

### `alwm benchmark run`

| Status | **complete** |
| --- | --- |
| **Evidence** | `benchmark/runner.py` full pipeline; `tests/test_benchmark.py` deterministic offline run. |
| **Run** | `ALWM_FIXTURE_MODE=1 alwm benchmark run --definition fixtures/benchmarks/offline.v1.yaml --output-dir /tmp/alwm-audit-bench …` → success. |

### `alwm providers show`

| Status | **complete** |
| --- | --- |
| **Run** | Prints JSON with default `kind: mock` and Ollama/OpenAI-compatible sections. |

---

## 2. Provider switching (mock, Ollama, OpenAI-compatible / llama.cpp)

| Status | **partial** |
| --- | --- |
| **What works** | `ProviderConfig.kind` ∈ `{mock, ollama, openai_compatible}` (`providers/config.py`). `create_provider` dispatches (`providers/factory.py`). Benchmark merges variant `backend.kind` + model via `load_provider_config_for_benchmark_variant` (`providers/benchmark_config.py`). `ALWM_FIXTURE_MODE=1` forces mock when `fixture_mode_force_mock` is true (default CLI). |
| **Tests** | `tests/test_providers.py`: mock deterministic; Ollama and OpenAI-compatible use **httpx.MockTransport** (no live network). |
| **Not verified here** | Live calls to Ollama or llama-server: require running services; *correct by design* but not part of CI. |
| **Compose** | `benchmark-ollama` and `benchmark-llamacpp` profiles point at `benchmarks/v1/ollama.v1.yaml` and `llamacpp.v1.yaml` with `--no-fixture-mock`. *Static review:* `docker compose --profile benchmark-offline config` validated via `just compose-help`; full `docker compose run` not executed in this audit (needs Docker daemon + optionally models). |

---

## 3. Browser evidence abstraction

| Status | **partial** |
| --- | --- |
| **Complete path** | `BrowserEvidence` schema + `alwm validate … browser_evidence`; `load_browser_evidence`, `evidence_to_prompt_block`; `MockBrowserRunner`; `FileBrowserRunner` (`tests/test_browser.py`). |
| **Run** | `alwm browser prompt-block examples/browser_evidence/v1/export_flow.json` printed structured markdown. |
| **Stub** | `PlaywrightBrowserRunner`, `MCPBrowserRunner` raise `NotImplementedError` (`browser/stubs.py`). |

---

## 4. Docker Compose profiles

| Status | **complete** |
| --- | --- |
| **Evidence** | `docker-compose.yml` defines `dev`, `test`, `benchmark`, `benchmark-offline`, `ollama`+`benchmark-ollama`, `benchmark-llamacpp`. |
| **Run** | `just compose-help` exited 0 and listed services: `orchestrator`, `tests`, `benchmark`, `benchmark-offline`, `ollama`, `benchmark-ollama`, `benchmark-llamacpp`. |

---

## 5. Docker Buildx Bake targets

| Status | **complete** |
| --- | --- |
| **Evidence** | `docker-bake.hcl`: `orchestrator`, `orchestrator-amd64`, `orchestrator-arm64`; `justfile` recipes `docker-bake`, `docker-build`. |
| **Run** | `docker buildx bake --print` returned resolved JSON for `orchestrator` (platforms `linux/amd64`, `linux/arm64`). Full image build not required to prove HCL validity. |

---

## 6. Prompt registry (`prompts/registry.yaml`)

| Status | **partial** (discovery + validation; benchmark defs still inline prompts) |
| --- | --- |
| **Shipped in this remediation** | `schemas/v1/prompt_registry.schema.json`, `prompt_registry.load_prompt_registry_yaml`, CLI `alwm prompts check|list|show`, `tests/test_prompt_registry.py`. |
| **Remaining gap** | Benchmark YAML and other pipelines do not yet reference registry ids instead of inline `text:` (optional future work). |

---

## 7. Test suite summary

| Command | Result |
| --- | --- |
| `pytest tests/ -q` | **53 passed** (after prompt-registry tests; session on 2026-04-17) |
| `ruff check src tests` | All checks passed |
| `mypy` | Success: 37 source files |

Test modules: `test_benchmark`, `test_benchmark_cases`, `test_browser`, `test_domain`, `test_example_campaigns`, `test_pipelines`, `test_prompt_registry`, `test_providers`, `test_smoke`.

---

## 8. Documentation drift (vs source of truth)

| Document | Drift |
| --- | --- |
| **`docs/implementation-log.md`** | Phase 1 block still lists “Known gaps” (e.g. Phase 6 placeholder) that are **obsolete** relative to current code (Ollama profile exists; pipelines exist). Latest “Next” lines are more accurate than older embedded gap lists. |
| **`AGENTS.md` / `README.md`** | Largely aligned with `just ci`, `justfile`, and CLI. Both claim a prompt **registry** under `prompts/`; until registry wiring shipped, that was aspirational. |
| **Cursor / workspace rules** | If any external rule still references `Makefile` or `make ci`, that is **stale** (repo uses `justfile`; no `Makefile` in tree). |

---

## 9. Prioritized remediation

1. **P0 — Prompt registry wiring** (explicit “Next” in implementation log): schema + loader + CLI so the registry is validated and addressable from `alwm`, with tests. *Done (same change set as this audit).*
2. **P1 — Live provider smoke (optional CI job)** Document or script a manual/scheduled check for Ollama + OpenAI-compatible endpoints; keep default CI offline-only per `AGENTS.md`.
3. **P2 — Implementation log hygiene** Replace or clearly mark historical “Known gaps” in Phase 1 so they are not mistaken for current state.
4. **P3 — Browser automation** Implement `PlaywrightBrowserRunner` or MCP behind the same `BrowserRunner` ABC when scope allows (currently intentional stubs).

---

## 10. Single most important next phase (product mission)

**Prompt registry integration (P0)** — The mission emphasizes git-native prompts and reproducibility; a registry file that nothing loads undermines trust and duplicates benchmark inline prompts. Wiring validation + discovery is the smallest step that connects documentation to code.

After that, **optional LLM-assisted rubric scoring** and **real browser runners** remain the larger capability jumps recorded in `docs/implementation-log.md`.

---

## Appendix: exact commands run (audit)

```text
.venv/bin/python -m pytest tests/ -q
# 48 passed

.venv/bin/alwm validate examples/v1/thought.json thought
.venv/bin/alwm validate examples/v1/rubric.json rubric

.venv/bin/alwm ingest examples/dataset/pages /tmp/alwm-audit-out/thoughts --created-at 1970-01-01T00:00:00Z
.venv/bin/alwm evaluate --subject examples/dataset/pages/retrieval-basics.md --rubric examples/v1/rubric.json --out /tmp/alwm-audit-out/evals/retrieval.eval.json
.venv/bin/alwm compare /tmp/alwm-audit-out/evals/retrieval.eval.json examples/dataset/evals/chunking-strategies.eval.json --out /tmp/alwm-audit-out/matrix.json --id audit-matrix --title "Audit" --out-md /tmp/alwm-audit-out/matrix.md
.venv/bin/alwm report --matrix /tmp/alwm-audit-out/matrix.json --out-json /tmp/alwm-audit-out/report.json --out-md /tmp/alwm-audit-out/report.md --id audit-report

ALWM_FIXTURE_MODE=1 .venv/bin/alwm benchmark run --definition fixtures/benchmarks/offline.v1.yaml --output-dir /tmp/alwm-audit-bench --created-at 1970-01-01T00:00:00Z --run-id audit-bench

.venv/bin/alwm providers show
.venv/bin/alwm browser prompt-block examples/browser_evidence/v1/export_flow.json

just compose-help
docker buildx bake --print

.venv/bin/alwm prompts check
.venv/bin/alwm prompts show scaffold.echo.v1
```
