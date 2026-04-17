"""Abstract browser runner — Playwright/MCP implementations plug in here later."""

from __future__ import annotations

from abc import ABC, abstractmethod

from agent_llm_wiki_matrix.browser.models import BrowserRunRequest, BrowserRunResult


class BrowserRunner(ABC):
    """Execute a browser scenario and return structured evidence.

    Live automation (Playwright, browser MCP tools, etc.) should implement this
    contract. Tests and offline pipelines should use `MockBrowserRunner` or
    `FileBrowserRunner` for determinism.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Stable runner id (mock, file, playwright, mcp, …)."""

    @abstractmethod
    def run(self, request: BrowserRunRequest) -> BrowserRunResult:
        """Produce `BrowserEvidence` for the given request."""
