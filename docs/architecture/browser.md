# Browser execution abstraction

## Purpose

Capture **browser evidence** (navigation, console messages, optional DOM snapshot refs) as **validated JSON** so benchmarks and reports can compare runs without depending on a live browser in **default CI**.

## Components

| Piece | Role |
| --- | --- |
| `BrowserEvidence` | Pydantic model + `schemas/v1/browser_evidence.schema.json` |
| `BrowserRunner` | ABC: `run(BrowserRunRequest) -> BrowserRunResult` |
| `MockBrowserRunner` | Deterministic synthetic evidence from request fields (tests, smoke) |
| `FileBrowserRunner` | Loads evidence from `fixtures/browser_evidence/v1/<scenario_id>.json` or a repo-relative path |
| `PlaywrightBrowserRunner` | **Optional** live capture via Playwright (`pyproject` extra **`[browser]`**); CLI `alwm browser run-playwright`; integration tests opt-in (`ALWM_PLAYWRIGHT_SMOKE=1`) |
| `MCPBrowserRunner` | **Stub** — raises `NotImplementedError` until MCP integration lands |
| `load_browser_evidence` / `evidence_to_prompt_block` | Validate fixtures and format text for LLM prompts |

## Determinism

- Prefer **committed JSON** under `fixtures/browser_evidence/v1/` for reproducible tests.
- `MockBrowserRunner` never performs I/O except hashing request fields.
- Default `just ci` does **not** install Playwright or browser binaries.

## Future integration

- **MCP:** implement `MCPBrowserRunner.run` by invoking browser tools on an MCP server and mapping tool output → `BrowserEvidence`.

Verification: `docs/workflows/live-verification.md`.

Labeling guidance: `docs/audits/capability-classification.md`.
