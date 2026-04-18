#!/usr/bin/env python3
"""Minimal FastMCP stdio server for tests: one tool returns committed ``BrowserEvidence`` JSON.

Set ``ALWM_MCP_BROWSER_COMMAND`` to ``python`` + this script path (see ``browser.md``).
"""

from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

_REPO_ROOT = Path(__file__).resolve().parents[2]
_FIXTURE = _REPO_ROOT / "fixtures" / "browser_evidence" / "v1" / "export_flow.json"

app = FastMCP("alwm_stdio_browser_evidence_fixture")


@app.tool()
def alwm_browser_evidence() -> str:
    """Return deterministic browser evidence JSON (same as ``export_flow`` fixture)."""
    return _FIXTURE.read_text(encoding="utf-8")


if __name__ == "__main__":
    app.run(transport="stdio")
