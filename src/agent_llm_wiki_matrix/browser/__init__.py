"""Browser execution abstraction (mock + file + optional Playwright; MCP fixture bridge)."""

from __future__ import annotations

from agent_llm_wiki_matrix.browser.base import BrowserRunner
from agent_llm_wiki_matrix.browser.factory import create_browser_runner
from agent_llm_wiki_matrix.browser.file_runner import FileBrowserRunner
from agent_llm_wiki_matrix.browser.formatting import evidence_to_prompt_block
from agent_llm_wiki_matrix.browser.load import load_browser_evidence
from agent_llm_wiki_matrix.browser.mcp_runner import MCPBrowserRunner
from agent_llm_wiki_matrix.browser.mock import MockBrowserRunner
from agent_llm_wiki_matrix.browser.models import (
    BrowserEvidence,
    BrowserRunRequest,
    BrowserRunResult,
    ConsoleMessage,
    DomExcerpt,
    NavigationStep,
    ScreenshotMetadata,
)
from agent_llm_wiki_matrix.browser.playwright_runner import PlaywrightBrowserRunner

__all__ = [
    "BrowserEvidence",
    "BrowserRunRequest",
    "BrowserRunResult",
    "BrowserRunner",
    "ConsoleMessage",
    "DomExcerpt",
    "ScreenshotMetadata",
    "MCPBrowserRunner",
    "FileBrowserRunner",
    "MockBrowserRunner",
    "NavigationStep",
    "PlaywrightBrowserRunner",
    "create_browser_runner",
    "evidence_to_prompt_block",
    "load_browser_evidence",
]
