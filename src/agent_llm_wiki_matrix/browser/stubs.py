"""Reserved runner for future MCP-based browser automation.

`PlaywrightBrowserRunner` lives in `browser.playwright_runner` (optional `playwright` dep).
"""

from __future__ import annotations

from agent_llm_wiki_matrix.browser.base import BrowserRunner
from agent_llm_wiki_matrix.browser.models import BrowserRunRequest, BrowserRunResult


class MCPBrowserRunner(BrowserRunner):
    """Future: delegate to a browser-capable MCP server (tool calls)."""

    @property
    def name(self) -> str:
        return "mcp"

    def run(self, request: BrowserRunRequest) -> BrowserRunResult:
        raise NotImplementedError(
            "MCPBrowserRunner is not implemented yet. "
            "Use MockBrowserRunner or FileBrowserRunner with JSON fixtures, "
            "or wire MCP tool calls here when integrating a browser MCP server."
        )
