"""Browser abstraction: mock runner, file fixtures, future runner stubs."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from agent_llm_wiki_matrix.artifacts import load_artifact_file
from agent_llm_wiki_matrix.browser import (
    FileBrowserRunner,
    MockBrowserRunner,
    PlaywrightBrowserRunner,
    evidence_to_prompt_block,
    load_browser_evidence,
)
from agent_llm_wiki_matrix.browser.models import BrowserRunRequest
from agent_llm_wiki_matrix.browser.stubs import MCPBrowserRunner
from agent_llm_wiki_matrix.cli import main

_REPO = Path(__file__).resolve().parents[1]


def test_load_browser_evidence_fixture() -> None:
    path = _REPO / "fixtures" / "browser_evidence" / "v1" / "export_flow.json"
    ev = load_browser_evidence(path)
    assert ev.id == "evidence.export_flow.v1"
    assert len(ev.navigation_sequence) == 3
    block = evidence_to_prompt_block(ev)
    assert "export clicked once" in block
    assert "Home" in block


def test_validate_artifact_kind_browser_evidence() -> None:
    path = _REPO / "fixtures" / "browser_evidence" / "v1" / "export_flow.json"
    load_artifact_file(path, "browser_evidence")


def test_mock_browser_runner_deterministic() -> None:
    r = MockBrowserRunner()
    req = BrowserRunRequest(scenario_id="alpha", steps=["one", "two"])
    a = r.run(req)
    b = r.run(req)
    assert a.evidence.model_dump() == b.evidence.model_dump()
    assert a.runner == "mock"
    assert a.evidence.id == "mock-evidence-alpha"


def test_file_browser_runner_by_scenario_id() -> None:
    runner = FileBrowserRunner(_REPO)
    result = runner.run(BrowserRunRequest(scenario_id="export_flow"))
    assert result.evidence.id == "evidence.export_flow.v1"
    assert result.runner == "file"


def test_file_browser_runner_by_fixture_relpath() -> None:
    runner = FileBrowserRunner(_REPO)
    result = runner.run(
        BrowserRunRequest(fixture_relpath="fixtures/browser_evidence/v1/export_flow.json")
    )
    assert result.evidence.navigation_sequence[0].url.startswith("https://")


def test_file_browser_runner_missing_raises() -> None:
    runner = FileBrowserRunner(_REPO)
    with pytest.raises(FileNotFoundError):
        runner.run(BrowserRunRequest(scenario_id="does_not_exist"))


def test_playwright_runner_requires_start_url() -> None:
    with pytest.raises(ValueError, match="start_url"):
        PlaywrightBrowserRunner().run(BrowserRunRequest())


def test_playwright_runner_missing_package_raises_runtime_error() -> None:
    try:
        import playwright.sync_api  # noqa: F401
    except ImportError:
        with pytest.raises(RuntimeError, match="Playwright is not installed"):
            PlaywrightBrowserRunner().run(BrowserRunRequest(start_url="file:///dev/null"))
    else:
        pytest.skip("playwright is installed; install-path not exercised")


def test_mcp_runner_without_fixture_raises() -> None:
    with pytest.raises(RuntimeError, match="remote MCP"):
        MCPBrowserRunner(_REPO).run(BrowserRunRequest())


def test_mcp_runner_fixture_bridge() -> None:
    runner = MCPBrowserRunner(_REPO)
    result = runner.run(
        BrowserRunRequest(fixture_relpath="fixtures/browser_evidence/v1/export_flow.json")
    )
    assert result.runner == "mcp"
    assert result.evidence.id == "evidence.export_flow.v1"
    assert result.evidence.notes is not None
    assert "fixture-backed bridge" in result.evidence.notes


def test_cli_prompt_block() -> None:
    runner = CliRunner()
    path = _REPO / "fixtures" / "browser_evidence" / "v1" / "export_flow.json"
    result = runner.invoke(main, ["browser", "prompt-block", str(path)])
    assert result.exit_code == 0
    assert "Browser evidence" in result.output


def test_cli_run_mock() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["browser", "run-mock", "--scenario-id", "x"])
    assert result.exit_code == 0
    assert "mock-evidence-x" in result.output
