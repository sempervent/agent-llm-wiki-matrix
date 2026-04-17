"""Construct built-in browser runners (mock / file-backed)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from agent_llm_wiki_matrix.browser.base import BrowserRunner
from agent_llm_wiki_matrix.browser.file_runner import FileBrowserRunner
from agent_llm_wiki_matrix.browser.mock import MockBrowserRunner


def create_browser_runner(
    kind: Literal["mock", "file"],
    *,
    repo_root: Path,
    evidence_dir: Path | None = None,
) -> BrowserRunner:
    """Instantiate a deterministic runner suitable for tests and CI."""
    if kind == "mock":
        return MockBrowserRunner()
    if kind == "file":
        return FileBrowserRunner(repo_root, evidence_dir=evidence_dir)
    msg = f"Unsupported browser runner kind: {kind}"
    raise ValueError(msg)
