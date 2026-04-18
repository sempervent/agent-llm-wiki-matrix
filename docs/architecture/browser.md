# Browser execution abstraction

## Purpose

Capture **browser evidence** (navigation, console messages, optional DOM snapshot refs, **DOM excerpts**, **screenshot metadata**, and an **`extensions`** JSON object) as **validated JSON** so benchmarks and reports can compare runs without depending on a live browser in **default CI**.

## Components

| Piece | Role |
| --- | --- |
| `BrowserEvidence` | Pydantic model + `schemas/v1/browser_evidence.schema.json` |
| `BrowserRunner` | ABC: `run(BrowserRunRequest) -> BrowserRunResult` |
| `MockBrowserRunner` | Deterministic synthetic evidence from request fields (tests, smoke) |
| `FileBrowserRunner` | Loads evidence from `fixtures/browser_evidence/v1/<scenario_id>.json` or a repo-relative path |
| `PlaywrightBrowserRunner` | **Optional** live capture via Playwright (`pyproject` extra **`[browser]`**); CLI `alwm browser run-playwright`; integration tests opt-in (`ALWM_PLAYWRIGHT_SMOKE=1`) |
| `MCPBrowserRunner` | **Partial** — same fixture loading as `FileBrowserRunner` when `scenario_id` or `fixture_relpath` is set; annotates evidence notes and uses runner id **`mcp`**. Without those fields it raises **`RuntimeError`** (remote MCP browser tools are **not** implemented). CLI: `alwm browser run-mcp`. |
| `load_browser_evidence` / `evidence_to_prompt_block` | Validate fixtures and format text for LLM prompts |

## Determinism

- Prefer **committed JSON** under `fixtures/browser_evidence/v1/` for reproducible tests.
- `MockBrowserRunner` never performs I/O except hashing request fields.
- Default `just ci` does **not** install Playwright or browser binaries.

## Scoring (browser interpretation)

Use **`examples/dataset/rubrics/browser_realism.v1.json`** when rubrics should stress **grounding** in the trace, **hallucination resistance**, and **source fidelity** to URLs/selectors/console lines. Default CI keeps **deterministic** hash-based scores unless a suite opts into semantic judging.

## Remote MCP browser tools (not implemented)

**Status:** **documented-only** for the MCP protocol and live tool execution. The **`MCPBrowserRunner`** name indicates the *intended* integration point for Cursor/IDE MCP browser tools; today only the fixture bridge is implemented.

### Roadmap (concrete)

1. **Dependency and transport** — Add an optional extra (e.g. `[mcp]`) pulling a maintained MCP client library; support stdio and/or streamable HTTP transport to a configured server command or URL.
2. **Configuration** — Repo-local config (env + optional YAML) for server launch args, working directory, timeouts, and which tool names map to navigation vs snapshot (no invented vendor APIs; discover tools from the server where possible).
3. **`BrowserRunRequest` contract** — Define how `start_url` / `steps` (or a new field) drive MCP tool calls; map tool results → `BrowserEvidence` (`load_browser_evidence`-compatible shape).
4. **Tests** — Mock transport or recorded MCP frames in `fixtures/` for default CI; opt-in integration test behind an env flag (similar to Playwright).
5. **Docs and CLI** — Extend `alwm browser run-mcp` with a documented live path; update this file and `docs/audits/capability-classification.md` to **complete** or **partial (optional)** when evidence-backed.

Verification: `docs/workflows/live-verification.md`.

## Benchmark harness

For variants with **`execution_mode: browser_mock`**, `run_benchmark` (`benchmark/runner.py`) calls **`run_benchmark_browser_phase`** (`benchmark/browser_execution.py`), persists **`BrowserEvidence`** to `cells/<cell>/browser_evidence.json`, and augments the provider prompt before scoring. Configure runners via **`variant.browser`** on the benchmark definition (see `schemas/v1/benchmark_definition.schema.json`). Opt-in Playwright for benchmarks: **`ALWM_BENCHMARK_PLAYWRIGHT=1`** (in addition to the `[browser]` install).

Labeling guidance: `docs/audits/capability-classification.md`.
