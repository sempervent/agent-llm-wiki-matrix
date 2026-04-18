"""Benchmark harness: browser evidence phase for browser_mock variants."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_llm_wiki_matrix.artifacts import load_artifact_file
from agent_llm_wiki_matrix.benchmark import load_benchmark_definition, run_benchmark
from agent_llm_wiki_matrix.browser.models import BrowserEvidence

_REPO = Path(__file__).resolve().parents[1]


def test_browser_mock_runs_mock_runner_and_writes_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALWM_FIXTURE_MODE", "1")
    dfn = load_benchmark_definition(_REPO / "fixtures" / "benchmarks" / "offline.v1.yaml")
    out = tmp_path / "run"
    run_benchmark(
        dfn,
        repo_root=_REPO,
        output_dir=out,
        created_at="1970-01-01T00:00:00Z",
        run_id="browser-bench",
        provider_yaml=None,
        environ={"ALWM_FIXTURE_MODE": "1"},
        fixture_mode_force_mock=True,
    )
    browser_cell = out / "cells" / "v-browser__p-one"
    assert (browser_cell / "browser_evidence.json").is_file()
    ev_data = json.loads((browser_cell / "browser_evidence.json").read_text(encoding="utf-8"))
    assert ev_data["id"].startswith("mock-evidence-")
    req = load_artifact_file(browser_cell / "request.json", "benchmark_request")
    assert "Browser evidence" in req.prompt_text
    assert req.browser_runner == "mock"
    assert req.browser_evidence_relpath == "cells/v-browser__p-one/browser_evidence.json"


def test_browser_file_runner_benchmark(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALWM_FIXTURE_MODE", "1")
    dfn = load_benchmark_definition(_REPO / "fixtures" / "benchmarks" / "browser_file.v1.yaml")
    out = tmp_path / "run"
    run_benchmark(
        dfn,
        repo_root=_REPO,
        output_dir=out,
        created_at="1970-01-01T00:00:00Z",
        run_id="bf",
        provider_yaml=None,
        environ={"ALWM_FIXTURE_MODE": "1"},
        fixture_mode_force_mock=True,
    )
    cell = out / "cells" / "v-file__p-one"
    ev = load_artifact_file(cell / "browser_evidence.json", "browser_evidence")
    assert ev.id == "evidence.export_flow.v1"
    assert len(ev.dom_excerpts) >= 1
    assert len(ev.screenshots) >= 1
    req = load_artifact_file(cell / "request.json", "benchmark_request")
    assert req.browser_runner == "file"
    assert "export clicked once" in req.prompt_text


def test_playwright_runner_blocked_without_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALWM_FIXTURE_MODE", "1")
    monkeypatch.delenv("ALWM_BENCHMARK_PLAYWRIGHT", raising=False)
    dfn = load_benchmark_definition(
        _REPO / "fixtures" / "benchmarks" / "browser_playwright.v1.yaml",
    )
    out = tmp_path / "run"
    with pytest.raises(RuntimeError, match="ALWM_BENCHMARK_PLAYWRIGHT"):
        run_benchmark(
            dfn,
            repo_root=_REPO,
            output_dir=out,
            created_at="1970-01-01T00:00:00Z",
            run_id="pw",
            provider_yaml=None,
            environ={"ALWM_FIXTURE_MODE": "1"},
            fixture_mode_force_mock=True,
        )


def test_mcp_runner_benchmark_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALWM_FIXTURE_MODE", "1")
    dfn = load_benchmark_definition(_REPO / "fixtures" / "benchmarks" / "browser_mcp.v1.yaml")
    out = tmp_path / "run"
    run_benchmark(
        dfn,
        repo_root=_REPO,
        output_dir=out,
        created_at="1970-01-01T00:00:00Z",
        run_id="mcp-b",
        provider_yaml=None,
        environ={"ALWM_FIXTURE_MODE": "1"},
        fixture_mode_force_mock=True,
    )
    req = load_artifact_file(out / "cells" / "v-mcp__p-one" / "request.json", "benchmark_request")
    assert req.browser_runner == "mcp"
    ev = load_artifact_file(
        out / "cells" / "v-mcp__p-one" / "browser_evidence.json",
        "browser_evidence",
    )
    assert isinstance(ev, BrowserEvidence)
    assert ev.notes is not None
    assert "fixture-backed bridge" in ev.notes
