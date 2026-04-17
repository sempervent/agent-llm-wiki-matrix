"""Benchmark harness: deterministic offline runs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_llm_wiki_matrix.artifacts import load_artifact_file
from agent_llm_wiki_matrix.benchmark import load_benchmark_definition, run_benchmark
from agent_llm_wiki_matrix.models import (
    BenchmarkRequestRecord,
    BenchmarkResponse,
    ComparisonMatrix,
    MatrixGridInputs,
    MatrixPairwiseInputs,
    Report,
)

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
    g1 = (out / "matrices" / "grid.json").read_text(encoding="utf-8")
    g2 = (run2 / "matrices" / "grid.json").read_text(encoding="utf-8")
    assert g1 == g2

    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["benchmark_id"] == "bench.offline.v1"
    assert len(manifest["cells"]) == 6

    first = manifest["cells"][0]
    assert "request_relpath" in first
    assert (out / first["request_relpath"]).is_file()
    assert (out / first["raw_response_relpath"]).is_file()
    assert (out / first["normalized_response_relpath"]).is_file()
    assert (out / first["aggregate_response_relpath"]).is_file()
    assert (out / first["evaluation_relpath"]).is_file()

    sample = load_artifact_file(out / first["aggregate_response_relpath"], "benchmark_response")
    assert isinstance(sample, BenchmarkResponse)
    req = load_artifact_file(out / first["request_relpath"], "benchmark_request")
    assert isinstance(req, BenchmarkRequestRecord)
    assert req.prompt_source == "inline"
    assert req.prompt_registry_id is None

    grid = load_artifact_file(out / "matrices" / "grid.json", "matrix")
    assert isinstance(grid, ComparisonMatrix)
    g_in = load_artifact_file(
        out / "matrices" / "grid.row_inputs.json",
        "matrix_grid_inputs",
    )
    assert isinstance(g_in, MatrixGridInputs)
    pw = load_artifact_file(out / "matrices" / "pairwise.json", "matrix")
    assert isinstance(pw, ComparisonMatrix)
    assert pw.matrix_kind == "pairwise"
    pw_in = load_artifact_file(
        out / "matrices" / "pairwise.row_inputs.json",
        "matrix_pairwise_inputs",
    )
    assert isinstance(pw_in, MatrixPairwiseInputs)

    rep = load_artifact_file(out / "reports" / "report.json", "report")
    assert isinstance(rep, Report)
    assert (out / "reports" / "report.md").read_text(encoding="utf-8")
    assert (out / "markdown" / "matrix.grid.md").read_text(encoding="utf-8")
