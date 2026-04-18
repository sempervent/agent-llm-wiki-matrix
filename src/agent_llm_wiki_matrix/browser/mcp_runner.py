"""MCP-labeled browser runner: fixture-backed JSON and optional MCP stdio tool calls."""

from __future__ import annotations

import os
import time
from collections.abc import Mapping
from pathlib import Path

from agent_llm_wiki_matrix.browser.base import BrowserRunner
from agent_llm_wiki_matrix.browser.file_runner import FileBrowserRunner
from agent_llm_wiki_matrix.browser.mcp_stdio import (
    fetch_browser_evidence_via_stdio,
    parse_stdio_server_command,
    stdio_env_cwd,
    stdio_env_tool_name,
    tool_arguments_from_request,
)
from agent_llm_wiki_matrix.browser.models import BrowserRunRequest, BrowserRunResult


class MCPBrowserRunner(BrowserRunner):
    """Browser evidence via ``FileBrowserRunner`` fixtures or an MCP stdio server.

    **Fixture path:** ``scenario_id`` / ``fixture_relpath`` — same JSON as
    ``FileBrowserRunner``, annotated as MCP-labeled.

    **Stdio path:** when ``ALWM_MCP_BROWSER_COMMAND`` is set and the request has
    **no** ``scenario_id`` or ``fixture_relpath``, the runner calls the configured
    MCP tool (default ``alwm_browser_evidence``) and validates JSON as
    ``BrowserEvidence``. Requires the ``mcp`` package (``dev`` extra).

    See ``docs/architecture/browser.md``.
    """

    def __init__(self, repo_root: Path) -> None:
        self._repo_root = repo_root.resolve()
        self._file = FileBrowserRunner(repo_root)

    @property
    def name(self) -> str:
        return "mcp"

    def run(self, request: BrowserRunRequest) -> BrowserRunResult:
        env = os.environ
        if request.scenario_id or request.fixture_relpath:
            return self._run_fixture_bridge(request)

        cmd = parse_stdio_server_command(env)
        if cmd:
            return self._run_stdio(request, cmd, env)

        msg = (
            "MCPBrowserRunner: pass scenario_id or fixture_relpath for fixture-backed evidence, "
            "or set ALWM_MCP_BROWSER_COMMAND for MCP stdio (see docs/architecture/browser.md)."
        )
        raise RuntimeError(msg)

    def _run_fixture_bridge(self, request: BrowserRunRequest) -> BrowserRunResult:
        t0 = time.monotonic()
        inner = self._file.run(request)
        note = (inner.evidence.notes or "").strip()
        bridge = "MCPBrowserRunner: fixture-backed bridge; MCP stdio not used."
        merged_note = f"{note} {bridge}".strip() if note else bridge
        evidence = inner.evidence.model_copy(update={"notes": merged_note})
        duration_ms = int((time.monotonic() - t0) * 1000)
        return BrowserRunResult(
            evidence=evidence,
            runner=self.name,
            duration_ms=max(duration_ms, inner.duration_ms),
        )

    def _run_stdio(
        self,
        request: BrowserRunRequest,
        command: list[str],
        env: Mapping[str, str],
    ) -> BrowserRunResult:
        t0 = time.monotonic()
        tool = stdio_env_tool_name(env)
        cwd = stdio_env_cwd(env, self._repo_root)
        args = tool_arguments_from_request(
            start_url=request.start_url,
            steps=request.steps,
        )
        evidence = fetch_browser_evidence_via_stdio(command, tool, args, cwd=cwd)
        note = (evidence.notes or "").strip()
        bridge = f"MCPBrowserRunner: MCP stdio tool={tool!r}; protocol client."
        merged_note = f"{note} {bridge}".strip() if note else bridge
        evidence = evidence.model_copy(update={"notes": merged_note})
        duration_ms = int((time.monotonic() - t0) * 1000)
        return BrowserRunResult(evidence=evidence, runner=self.name, duration_ms=duration_ms)
