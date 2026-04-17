"""Benchmark harness: deterministic offline runs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_llm_wiki_matrix.artifacts import load_artifact_file
from agent_llm_wiki_matrix.benchmark import load_benchmark_definition, run_benchmark
from agent_llm_wiki_matrix.models import BenchmarkResponse, ComparisonMatrix, Report

_REPO = Path(__file__).resolve().parents[1]


def test_offline_benchmark_pipeline_is_deterministic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALWM_FIXTURE_MODE", "1")
    dfn = load_benchmark_definition(_REPO / "fixtures" / "benchmarks" / "offline.v1.yaml")
    out = tmp_path / "run1"
    run_benchmark(
        dfn,
        repo_root=_REPO,
        output_dir=out,
        created_at="1970-01-01T00:00:00Z",
        run_id="test-run",
        provider_yaml=None,
        environ={"ALWM_FIXTURE_MODE": "1"},
        fixture_mode_force_mock=True,
    )
    run2 = tmp_path / "run2"
    run_benchmark(
        dfn,
        repo_root=_REPO,
        output_dir=run2,
        created_at="1970-01-01T00:00:00Z",
        run_id="test-run",
        provider_yaml=None,
        environ={"ALWM_FIXTURE_MODE": "1"},
        fixture_mode_force_mock=True,
    )
    g1 = (out / "matrix.grid.json").read_text(encoding="utf-8")
    g2 = (run2 / "matrix.grid.json").read_text(encoding="utf-8")
    assert g1 == g2

    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["benchmark_id"] == "bench.offline.v1"
    assert len(manifest["response_paths"]) == 6

    sample = load_artifact_file(out / manifest["response_paths"][0], "benchmark_response")
    assert isinstance(sample, BenchmarkResponse)

    grid = load_artifact_file(out / "matrix.grid.json", "matrix")
    assert isinstance(grid, ComparisonMatrix)
    pw = load_artifact_file(out / "matrix.pairwise.json", "matrix")
    assert isinstance(pw, ComparisonMatrix)
    assert pw.matrix_kind == "pairwise"

    rep = load_artifact_file(out / "report.json", "report")
    assert isinstance(rep, Report)
