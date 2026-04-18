#!/usr/bin/env python3
"""FastMCP stdio server: ``alwm_browser_evidence`` returns committed ``BrowserEvidence`` JSON.

Set ``ALWM_MCP_BROWSER_COMMAND`` to a shell argv that launches this script. Scenario selection
(``alwm:checkout_flow``, ``alwm:form_validation``, URL hints) is documented in
``docs/architecture/browser.md``. The shipped server returns fixtures only—not a live browser.
"""

from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

_REPO_ROOT = Path(__file__).resolve().parents[2]
_V1 = _REPO_ROOT / "fixtures" / "browser_evidence" / "v1"
_FIXTURES = {
    "export_flow": _V1 / "export_flow.json",
    "checkout_flow": _V1 / "checkout_flow.json",
    "form_validation": _V1 / "form_validation.json",
}

app = FastMCP("alwm_stdio_browser_evidence_fixture")


def _pick_fixture_key(start_url: str | None, steps: list[str] | None) -> str:
    s = [x for x in (steps or []) if isinstance(x, str)]
    if "alwm:checkout_flow" in s:
        return "checkout_flow"
    if "alwm:form_validation" in s:
        return "form_validation"
    u = (start_url or "").lower()
    if "checkout" in u:
        return "checkout_flow"
    if "signup" in u:
        return "form_validation"
    return "export_flow"


@app.tool()
def alwm_browser_evidence(
    start_url: str | None = None,
    steps: list[str] | None = None,
) -> str:
    """Return deterministic browser evidence JSON from committed fixtures."""
    key = _pick_fixture_key(start_url, steps)
    path = _FIXTURES[key]
    return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    app.run(transport="stdio")
