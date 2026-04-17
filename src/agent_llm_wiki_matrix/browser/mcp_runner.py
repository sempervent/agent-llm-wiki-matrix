"""MCP-labeled browser runner: fixture-backed evidence until remote MCP tools are wired."""

from __future__ import annotations

import time
from pathlib import Path

from agent_llm_wiki_matrix.browser.base import BrowserRunner
from agent_llm_wiki_matrix.browser.file_runner import FileBrowserRunner
from agent_llm_wiki_matrix.browser.models import BrowserRunRequest, BrowserRunResult


class MCPBrowserRunner(BrowserRunner):
    """Load browser evidence from committed JSON (same as ``FileBrowserRunner``).

    **Capability boundary:** remote MCP tool calls are **not** implemented. Use
    ``scenario_id`` or ``fixture_relpath`` on the request for deterministic
    fixture-backed runs; see ``docs/architecture/browser.md``.
    """

    def __init__(self, repo_root: Path) -> None:
        self._repo_root = repo_root.resolve()
        self._file = FileBrowserRunner(repo_root)

    @property
    def name(self) -> str:
        return "mcp"

    def run(self, request: BrowserRunRequest) -> BrowserRunResult:
        if not request.scenario_id and not request.fixture_relpath:
            msg = (
                "MCPBrowserRunner: remote MCP browser tools are not implemented. "
                "Pass scenario_id or fixture_relpath for fixture-backed evidence, "
                "or use FileBrowserRunner/MockBrowserRunner explicitly."
            )
            raise RuntimeError(msg)
        t0 = time.monotonic()
        inner = self._file.run(request)
        note = (inner.evidence.notes or "").strip()
        bridge = "MCPBrowserRunner: fixture-backed bridge; live MCP not wired."
        merged_note = f"{note} {bridge}".strip() if note else bridge
        evidence = inner.evidence.model_copy(update={"notes": merged_note})
        duration_ms = int((time.monotonic() - t0) * 1000)
        return BrowserRunResult(
            evidence=evidence,
            runner=self.name,
            duration_ms=max(duration_ms, inner.duration_ms),
        )
