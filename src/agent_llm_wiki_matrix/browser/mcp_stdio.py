"""MCP stdio client: call a server tool and map JSON text to ``BrowserEvidence``.

Requires the ``mcp`` distribution (listed under the ``dev`` optional extra).

Environment (stdio execution path):
- ``ALWM_MCP_BROWSER_COMMAND`` — shell-parsed argv for the MCP server process (required).
- ``ALWM_MCP_BROWSER_TOOL`` — tool name to ``call_tool`` (default: ``alwm_browser_evidence``).
- ``ALWM_MCP_BROWSER_CWD`` — optional working directory for the server process.
"""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from agent_llm_wiki_matrix.browser.models import BrowserEvidence


def evidence_from_call_tool_result(result: Any) -> BrowserEvidence:
    """Extract the first text JSON payload from an MCP ``CallToolResult``."""
    if result.isError:
        msg = "MCP tool returned isError=true"
        raise RuntimeError(msg)
    if not result.content:
        msg = "MCP tool returned empty content"
        raise RuntimeError(msg)
    texts: list[str] = []
    for block in result.content:
        t = getattr(block, "text", None)
        if isinstance(t, str):
            texts.append(t)
    if not texts:
        msg = "MCP tool content had no text blocks"
        raise RuntimeError(msg)
    merged = "\n".join(texts).strip()
    try:
        data = json.loads(merged)
    except json.JSONDecodeError as e:
        msg = f"MCP tool text is not valid JSON: {e}"
        raise RuntimeError(msg) from e
    return BrowserEvidence.model_validate(data)


def parse_stdio_server_command(environ: Mapping[str, str]) -> list[str] | None:
    """Return argv for ``StdioServerParameters`` or ``None`` if unset."""
    raw = environ.get("ALWM_MCP_BROWSER_COMMAND", "").strip()
    if not raw:
        return None
    import shlex

    return shlex.split(raw, posix=os.name != "nt")


async def _call_tool_async(
    command: list[str],
    tool_name: str,
    arguments: dict[str, Any],
    *,
    cwd: Path | None,
) -> BrowserEvidence:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    if not command:
        msg = "MCP server command argv is empty"
        raise RuntimeError(msg)
    params = StdioServerParameters(
        command=command[0],
        args=command[1:],
        env=os.environ.copy(),
        cwd=str(cwd) if cwd is not None else None,
    )
    async with stdio_client(params) as (read, write):  # noqa: SIM117
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            return evidence_from_call_tool_result(result)


def fetch_browser_evidence_via_stdio(
    command: list[str],
    tool_name: str,
    arguments: dict[str, Any],
    *,
    cwd: Path | None = None,
) -> BrowserEvidence:
    """Run an MCP stdio client, call ``tool_name``, return validated ``BrowserEvidence``."""
    try:
        import mcp  # noqa: F401
    except ImportError as e:
        msg = (
            "The 'mcp' package is required for MCP stdio. "
            "Install dev extras: uv pip install -e \".[dev]\""
        )
        raise RuntimeError(msg) from e
    return asyncio.run(_call_tool_async(command, tool_name, arguments, cwd=cwd))


def stdio_env_tool_name(environ: Mapping[str, str]) -> str:
    return (environ.get("ALWM_MCP_BROWSER_TOOL") or "alwm_browser_evidence").strip()


def stdio_env_cwd(environ: Mapping[str, str], repo_root: Path) -> Path | None:
    raw = (environ.get("ALWM_MCP_BROWSER_CWD") or "").strip()
    if not raw:
        return None
    p = Path(raw).expanduser()
    if not p.is_absolute():
        return (repo_root / p).resolve()
    return p.resolve()


def tool_arguments_from_request(
    *,
    start_url: str | None,
    steps: list[str],
) -> dict[str, Any]:
    """Serializable arguments passed to the MCP tool (servers may ignore)."""
    out: dict[str, Any] = {}
    if start_url:
        out["start_url"] = start_url
    if steps:
        out["steps"] = list(steps)
    return out
