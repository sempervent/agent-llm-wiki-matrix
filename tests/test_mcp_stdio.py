"""MCP stdio client + fixture server: local subprocess only (no IDE/remote MCP)."""

from __future__ import annotations

import os
import shlex
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

pytest.importorskip("mcp")

from agent_llm_wiki_matrix.browser.mcp_runner import MCPBrowserRunner
from agent_llm_wiki_matrix.browser.models import BrowserRunRequest
from agent_llm_wiki_matrix.cli import main

_REPO = Path(__file__).resolve().parents[1]
_SERVER = _REPO / "fixtures" / "mcp_servers" / "stdio_browser_evidence_server.py"


def _stdio_command_string() -> str:
    return " ".join(shlex.quote(str(x)) for x in [sys.executable, _SERVER])


def test_mcp_stdio_checkout_flow_rich_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stdio path returns multi-screenshot evidence with extensions (same as checkout fixture)."""
    monkeypatch.setenv("ALWM_MCP_BROWSER_COMMAND", _stdio_command_string())
    monkeypatch.delenv("ALWM_MCP_BROWSER_TOOL", raising=False)
    runner = MCPBrowserRunner(_REPO)
    result = runner.run(
        BrowserRunRequest(
            start_url="https://example.test/checkout",
            steps=["alwm:checkout_flow"],
        )
    )
    ev = result.evidence
    assert ev.id == "evidence.checkout_flow.v1"
    assert len(ev.screenshots) == 2
    assert len(ev.dom_excerpts) >= 2
    assert ev.extensions is not None
    assert "network" in ev.extensions
    assert result.evidence.notes is not None
    assert "MCP stdio" in result.evidence.notes


def test_mcp_stdio_form_validation_a11y_and_console(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stdio path can return form + a11y excerpt fixture (explicit step token)."""
    monkeypatch.setenv("ALWM_MCP_BROWSER_COMMAND", _stdio_command_string())
    runner = MCPBrowserRunner(_REPO)
    result = runner.run(
        BrowserRunRequest(
            steps=["alwm:form_validation"],
        )
    )
    ev = result.evidence
    assert ev.id == "evidence.form_validation.v1"
    assert any("validation" in m.text.lower() for m in ev.console_messages)
    assert any(e.aria_role == "alert" for e in ev.dom_excerpts)


def test_cli_run_mcp_stdio_checkout_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    """CLI ``--stdio`` uses the same subprocess MCP path as the runner."""
    monkeypatch.setenv("ALWM_MCP_BROWSER_COMMAND", _stdio_command_string())
    cli = CliRunner()
    result = cli.invoke(
        main,
        [
            "browser",
            "run-mcp",
            "--stdio",
            "--start-url",
            "https://example.test/cart",
            "--step",
            "alwm:checkout_flow",
        ],
        env={**os.environ, "ALWM_MCP_BROWSER_COMMAND": _stdio_command_string()},
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "evidence.checkout_flow.v1" in result.output
    assert "Pay now" in result.output or "checkout_flow" in result.output
