# Capability classification (for agents and reviewers)

Use this vocabulary when describing features in PRs, `docs/implementation-log.md`, and code comments. **Do not label something “complete” without evidence** from the verification column.

## States

| State | Meaning | Evidence bar (minimum) |
| --- | --- | --- |
| **complete** | Matches the documented contract; safe for default CI and documented workflows. | Code path exists; **default tests** (`just ci`) or clearly scoped tests cover it; docs/commands match behavior. |
| **partial** | Shipped and safe, but missing depth, optional deps, or edge cases—call out what is missing. | Tests or manual steps document the gap; README/AGENTS do not imply full coverage. |
| **stub** | Intentional non-implementation: raises `NotImplementedError`, or exists only to reserve an API. | Raised error or obvious no-op; referenced from architecture or this file; **not** described as production-ready elsewhere. |
| **documented-only** | Described in docs or comments but **no** code path, or only scaffolding. | No contradictory “complete” claims; prefer upgrading to **stub** with an explicit error. |
| **broken** | Known incorrect behavior or failing tests; not acceptable on `main` without a ticket/fix plan. | Failing test, issue link, or explicit “do not use” in docs. |

## Cross-check: “complete” vs hype

Before writing **complete**:

1. **Code** — Grep for the public entrypoint (`cli.py`, `create_*`, factory).
2. **Tests** — `tests/` (and `tests/integration/` only if the feature is integration-only).
3. **Commands** — `alwm … --help` or `just …` matches README / AGENTS.
4. **Optional deps** — If the feature needs `uv pip install -e '.[browser]'` (or similar) for optional behavior, say **partial** or **complete (optional extra)** and name the extra.

## Repository examples (current; re-verify after changes)

| Capability | Suggested label | Why (evidence) |
| --- | --- | --- |
| `alwm validate` kinds | **complete** | `artifacts.py` + `tests/test_domain.py` / smoke |
| Committed **`examples/`** / **`fixtures/`** contract drift guard | **complete** | **`just validate-artifacts`** (`tests/test_schema_drift_contracts.py`); inventory **`docs/audits/schema-drift-contracts-inventory.md`** |
| `MockBrowserRunner` / `FileBrowserRunner` | **complete** | `tests/test_browser.py`; no network |
| `PlaywrightBrowserRunner` | **partial** (optional) | Requires `[browser]` extra + `playwright install`; `tests/integration/` gated by `ALWM_PLAYWRIGHT_SMOKE=1` |
| `MCPBrowserRunner` | **partial** | Fixture path **or** optional **local stdio MCP** when `ALWM_MCP_BROWSER_COMMAND` is set (`browser/mcp_runner.py`, `browser/mcp_stdio.py`); requires `mcp` (**`dev`** extra); `alwm browser run-mcp`; default tests cover the **shipped** stdio fixture server (`tests/test_mcp_stdio.py`); **remote / IDE-hosted MCP** not in scope (`docs/roadmap/v0.2.0.md`, `docs/architecture/browser.md`) |
| `browser_realism.v1` rubric | **partial** | **`examples/dataset/rubrics/browser_realism.v1.json`** — scores **grounding in committed `BrowserEvidence` JSON**; does **not** assert a live browser unless evidence came from **Playwright** (optional `[browser]`) |
| `alwm benchmark run` (offline) | **complete** | `tests/test_benchmark.py`, `tests/test_benchmark_browser.py`; `browser_mock` variants run browser phase + write `browser_evidence.json` |
| `alwm benchmark campaign run` (incl. `--dry-run`) | **complete** | `tests/test_benchmark_campaign.py`; manifests registered in `artifacts.py`; workflow **`docs/workflows/benchmark-campaigns.md`**, walkthrough **`docs/workflows/campaign-walkthrough.md`** |
| Benchmark + **Playwright** | **partial** (opt-in) | Variant `browser.runner: playwright` requires `ALWM_BENCHMARK_PLAYWRIGHT=1` + `[browser]` extra; not in default CI |
| `alwm benchmark probe` | **complete** (live) | `tests/test_live_probe.py`; integration opt-in |
| Prompt registry CLI | **complete** | `tests/test_prompt_registry.py`. Registry content grows over time—that is data, not stubbing. |

## When to file drift

If README, `AGENTS.md`, **`docs/workflows/verification.md`**, and `docs/architecture/*.md` disagree about a verification command or dependency, treat it as **drift**: fix docs or code in the same PR, or open a short note in `docs/implementation-log.md`.
