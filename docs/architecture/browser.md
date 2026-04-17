# Browser execution abstraction

## Purpose

Capture **browser evidence** (navigation, console messages, optional DOM snapshot refs) as **validated JSON** so benchmarks and reports can compare runs without depending on a live browser in CI.

## Components

| Piece | Role |
| --- | --- |
| `BrowserEvidence` | Pydantic model + `schemas/v1/browser_evidence.schema.json` |
| `BrowserRunner` | ABC: `run(BrowserRunRequest) -> BrowserRunResult` |
| `MockBrowserRunner` | Deterministic synthetic evidence from request fields (tests, smoke) |
| `FileBrowserRunner` | Loads evidence from `fixtures/browser_evidence/v1/<scenario_id>.json` or a repo-relative path |
| `PlaywrightBrowserRunner` / `MCPBrowserRunner` | **Stubs** — raise `NotImplementedError` until Playwright/MCP integration lands |
| `load_browser_evidence` / `evidence_to_prompt_block` | Validate fixtures and format text for LLM prompts |

## Determinism

- Prefer **committed JSON** under `fixtures/browser_evidence/v1/` for reproducible tests.
- `MockBrowserRunner` never performs I/O except hashing request fields.

## Future integration

- **Playwright:** implement `PlaywrightBrowserRunner.run` using a browser binary and trace export → `BrowserEvidence`.
- **MCP:** implement `MCPBrowserRunner.run` by invoking browser tools on an MCP server and mapping tool output → `BrowserEvidence`.

Do not commit live automation until those implementations have their own tests and optional dependencies.
