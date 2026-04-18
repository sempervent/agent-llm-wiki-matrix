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
- **MCP stdio** uses a **local subprocess** (no network). The committed **FastMCP** server at `fixtures/mcp_servers/stdio_browser_evidence_server.py` returns **realistic** multi-field `BrowserEvidence` from `fixtures/browser_evidence/v1/` (see scenario table below). That proves the MCP client and validation path—not a live browser.

## MCP stdio (minimal real protocol path)

**Implemented:** stdio transport + `call_tool` + JSON → `BrowserEvidence` validation (`browser/mcp_stdio.py`).

| Variable | Purpose |
| --- | --- |
| `ALWM_MCP_BROWSER_COMMAND` | Required for stdio mode: shell-parsed argv to launch the MCP server (e.g. `python fixtures/mcp_servers/stdio_browser_evidence_server.py`). |
| `ALWM_MCP_BROWSER_TOOL` | Optional; default **`alwm_browser_evidence`**. |
| `ALWM_MCP_BROWSER_CWD` | Optional working directory for the server process (repo-relative paths resolved against `ALWM_REPO_ROOT`). |

**Contract:** the tool should return **text content** whose concatenation is a single JSON object matching **`BrowserEvidence`**. Extra arguments (`start_url`, `steps`) are passed from `BrowserRunRequest`; the **shipped fixture server** uses them to pick a committed JSON file:

| Signal | Fixture (under `fixtures/browser_evidence/v1/`) |
| --- | --- |
| `steps` contains `alwm:checkout_flow`, or `start_url` contains `checkout` | `checkout_flow.json` (multi-screenshot, rich `extensions`) |
| `steps` contains `alwm:form_validation`, or `start_url` contains `signup` | `form_validation.json` (a11y-heavy excerpts) |
| otherwise | `export_flow.json` |

**Tests:** `tests/test_mcp_stdio.py` exercises checkout + form scenarios over stdio (deterministic; requires `mcp` from **dev** extras).

**Dependency:** `mcp>=1.27` is listed under **`[project.optional-dependencies] dev`** and **`[dependency-groups] dev`** so `uv pip install -e ".[dev]"` / `uv sync --group dev` install it.

**Not in scope (v0.2.x milestone):** Cursor/IDE-hosted MCP servers, streamable HTTP/SSE MCP to remote hosts, or vendor-specific browser tool shapes—see **`docs/roadmap/v0.2.0.md`** non-goals. The stdio path is the supported **protocol-capable** hook for future work.

### Roadmap (follow-on)

1. Optional **`[mcp]`** install surface for non-dev consumers (if needed).
2. Tool discovery (`tools/list`) and mapping profiles for heterogeneous servers.
3. Optional extra integration tests against a **user-provided** MCP command (beyond the shipped fixture server exercised in **`tests/test_mcp_stdio.py`**).

Verification: `docs/workflows/live-verification.md`.

## Scoring (browser interpretation)

Use **`examples/dataset/rubrics/browser_realism.v1.json`** when rubrics should stress **grounding** in the trace, **hallucination resistance**, and **source fidelity** to URLs/selectors/console lines. That rubric scores whether the **model’s answer respects the committed JSON**—it does **not**, by itself, prove that a real browser was automated. **Playwright** (optional `[browser]`) is the path for live DOM capture into `BrowserEvidence`; **MCP stdio** here is still **fixture JSON** unless you replace the server with your own tool implementation.

## Benchmark harness

For variants with **`execution_mode: browser_mock`**, `run_benchmark` (`benchmark/runner.py`) calls **`run_benchmark_browser_phase`** (`benchmark/browser_execution.py`), persists **`BrowserEvidence`** to `cells/<cell>/browser_evidence.json`, and augments the provider prompt before scoring. Configure runners via **`variant.browser`** on the benchmark definition (see `schemas/v1/benchmark_definition.schema.json`). Opt-in Playwright for benchmarks: **`ALWM_BENCHMARK_PLAYWRIGHT=1`** (in addition to the `[browser]` install).

## Reporting (Markdown)

`browser/formatting.py` renders human-readable blocks for **`reports/report.md`** (per-run benchmark) and **`reports/campaign-report.md`** (campaign comparative, when member runs contain browser evidence):

- **Summary table** — runner kind, evidence id, counts (DOM excerpts, screenshots, extension keys).
- **Legible detail** — screenshot metadata as a table (viewport, DPR, sequence, short content hash); DOM excerpts as a table plus optional fenced **`html`** snippets; **`extensions`** as labeled bullets with remainder in fenced JSON so nested objects stay readable.

Copy in those sections states that **Playwright is optional** and that **MCP** here means a **local stdio tool bridge** returning JSON — not a remote or IDE-hosted browser session.

Labeling guidance: `docs/audits/capability-classification.md`.
