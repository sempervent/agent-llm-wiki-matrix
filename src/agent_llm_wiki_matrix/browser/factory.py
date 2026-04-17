"""Construct built-in browser runners (mock / file / optional Playwright)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from agent_llm_wiki_matrix.browser.base import BrowserRunner
from agent_llm_wiki_matrix.browser.file_runner import FileBrowserRunner
from agent_llm_wiki_matrix.browser.mock import MockBrowserRunner
from agent_llm_wiki_matrix.browser.playwright_runner import PlaywrightBrowserRunner


def create_browser_runner(
    kind: Literal["mock", "file", "playwright"],
    *,
    repo_root: Path,
    evidence_dir: Path | None = None,
    headless: bool = True,
) -> BrowserRunner:
    """Instantiate a runner. Mock/file are CI-safe; playwright needs the ``[browser]`` extra."""
    if kind == "mock":
        return MockBrowserRunner()
    if kind == "file":
        return FileBrowserRunner(repo_root, evidence_dir=evidence_dir)
    if kind == "playwright":
        return PlaywrightBrowserRunner(headless=headless)
    msg = f"Unsupported browser runner kind: {kind}"
    raise ValueError(msg)
