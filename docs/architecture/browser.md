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
| `MCPBrowserRunner` | **Partial** — (1) same fixture loading as `FileBrowserRunner` when `scenario_id` or `fixture_relpath` is set; (2) **optional MCP stdio** when those fields are **absent** and **`ALWM_MCP_BROWSER_COMMAND`** is set: runs the official MCP client (`mcp` package, included in **`dev`** extras), calls a configurable tool (default **`alwm_browser_evidence`**), parses **JSON text** from the tool result into `BrowserEvidence`. CLI: `alwm browser run-mcp` (`--scenario-id` / `--fixture`, or `--stdio`). |
| `load_browser_evidence` / `evidence_to_prompt_block` | Validate fixtures and format text for LLM prompts |

## Determinism

- Prefer **committed JSON** under `fixtures/browser_evidence/v1/` for reproducible tests.
- `MockBrowserRunner` never performs I/O except hashing request fields.
- Default `just ci` does **not** install Playwright or browser binaries.
- **MCP stdio** uses a **local subprocess** (no network); CI runs a **fixture FastMCP server** at `fixtures/mcp_servers/stdio_browser_evidence_server.py`.

## MCP stdio (minimal real protocol path)

**Implemented:** stdio transport + `call_tool` + JSON → `BrowserEvidence` validation (`browser/mcp_stdio.py`).

| Variable | Purpose |
| --- | --- |
| `ALWM_MCP_BROWSER_COMMAND` | Required for stdio mode: shell-parsed argv to launch the MCP server (e.g. `python fixtures/mcp_servers/stdio_browser_evidence_server.py`). |
| `ALWM_MCP_BROWSER_TOOL` | Optional; default **`alwm_browser_evidence`**. |
| `ALWM_MCP_BROWSER_CWD` | Optional working directory for the server process (repo-relative paths resolved against `ALWM_REPO_ROOT`). |

**Contract:** the tool should return **text content** whose concatenation is a single JSON object matching **`BrowserEvidence`**. Extra arguments (`start_url`, `steps`) are passed from `BrowserRunRequest` for forward-compatible servers; the fixture server ignores them.

**Dependency:** `mcp>=1.27` is listed under **`[project.optional-dependencies] dev`** and **`[dependency-groups] dev`** so `uv pip install -e ".[dev]"` / `uv sync --group dev` install it.

**Not in scope (v0.2.x milestone):** Cursor/IDE-hosted MCP servers, streamable HTTP/SSE MCP to remote hosts, or vendor-specific browser tool shapes—see **`docs/roadmap/v0.2.0.md`** non-goals. The stdio path is the supported **protocol-capable** hook for future work.

### Roadmap (follow-on)

1. Optional **`[mcp]`** install surface for non-dev consumers (if needed).
2. Tool discovery (`tools/list`) and mapping profiles for heterogeneous servers.
3. Opt-in integration tests against a user-provided MCP command (env-gated, not default CI).

Verification: `docs/workflows/live-verification.md`.

## Scoring (browser interpretation)

Use **`examples/dataset/rubrics/browser_realism.v1.json`** when rubrics should stress **grounding** in the trace, **hallucination resistance**, and **source fidelity** to URLs/selectors/console lines. Default CI keeps **deterministic** hash-based scores unless a suite opts into semantic judging.

## Benchmark harness

For variants with **`execution_mode: browser_mock`**, `run_benchmark` (`benchmark/runner.py`) calls **`run_benchmark_browser_phase`** (`benchmark/browser_execution.py`), persists **`BrowserEvidence`** to `cells/<cell>/browser_evidence.json`, and augments the provider prompt before scoring. Configure runners via **`variant.browser`** on the benchmark definition (see `schemas/v1/benchmark_definition.schema.json`). Opt-in Playwright for benchmarks: **`ALWM_BENCHMARK_PLAYWRIGHT=1`** (in addition to the `[browser]` install).

Labeling guidance: `docs/audits/capability-classification.md`.
