"""Reserved runners for future Playwright and MCP-based browser automation.

These classes exist so callers can depend on `BrowserRunner` without importing
optional heavy dependencies. They are not wired into the CLI or Docker image
until integration work lands.
"""

from __future__ import annotations

from agent_llm_wiki_matrix.browser.base import BrowserRunner
from agent_llm_wiki_matrix.browser.models import BrowserRunRequest, BrowserRunResult


class PlaywrightBrowserRunner(BrowserRunner):
    """Future: drive Chromium/WebKit/Firefox via Playwright."""

    def __init__(self, *, headless: bool = True) -> None:
        self._headless = headless

    @property
    def name(self) -> str:
        return "playwright"

    def run(self, request: BrowserRunRequest) -> BrowserRunResult:
        raise NotImplementedError(
            "PlaywrightBrowserRunner is not implemented yet. "
            "Use MockBrowserRunner or FileBrowserRunner with JSON fixtures, "
            "or integrate Playwright here when adding live browser automation."
        )


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
