"""Runtime observability on benchmark and campaign manifests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_llm_wiki_matrix.artifacts import load_artifact_file
from agent_llm_wiki_matrix.benchmark import run_benchmark
from agent_llm_wiki_matrix.benchmark.definitions import BenchmarkDefinitionV1
from agent_llm_wiki_matrix.models import BenchmarkRunManifest

_REPO = Path(__file__).resolve().parents[1]


def test_benchmark_manifest_includes_runtime_and_retry_summaries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALWM_FIXTURE_MODE", "1")
    dfn = BenchmarkDefinitionV1.model_validate(
        {
            "schema_version": 1,
            "id": "bench.obs.v1",
            "title": "observability fixture",
            "rubric_ref": "fixtures/v1/rubric.json",
            "prompts": [{"id": "p1", "text": "Hi."}],
            "variants": [
                {
                    "id": "v1",
                    "agent_stack": "alwm-cli",
                    "execution_mode": "cli",
                    "backend": {"kind": "mock", "model": "mock-model"},
                },
            ],
            "retry_policy": {"max_attempts": 3, "backoff_seconds": 0.1},
        },
    )
    out = tmp_path / "run"
    run_benchmark(
        dfn,
        repo_root=_REPO,
        output_dir=out,
        created_at="1970-01-01T00:00:00Z",
        run_id="obs1",
        provider_yaml=None,
        environ={"ALWM_FIXTURE_MODE": "1"},
        fixture_mode_force_mock=True,
    )
    raw = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    mf = BenchmarkRunManifest.model_validate(raw)
    assert mf.runtime_summary is not None
    assert mf.runtime_summary.duration_seconds >= 0.0
    assert mf.runtime_summary.started_at_utc
    assert mf.runtime_summary.finished_at_utc
    assert mf.retry_summary is not None
    assert mf.retry_summary.retry_policy_max_attempts == 3
    assert mf.retry_summary.total_judge_invocations == 0
    assert mf.cells[0].runtime is not None
    assert mf.cells[0].runtime.provider_seconds is not None
    report_md = (out / "reports" / "report.md").read_text(encoding="utf-8")
    assert "## Runtime observability" in report_md
    assert "duration_seconds" in report_md


def test_semantic_benchmark_increments_judge_invocation_count(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALWM_FIXTURE_MODE", "1")
    dfn = BenchmarkDefinitionV1.model_validate(
        {
            "schema_version": 1,
            "id": "bench.obs.sem.v1",
            "title": "semantic observability",
            "rubric_ref": "fixtures/v1/rubric.json",
            "prompts": [{"id": "p1", "text": "Hi."}],
            "variants": [
                {
                    "id": "v1",
                    "agent_stack": "alwm-cli",
                    "execution_mode": "cli",
                    "backend": {"kind": "mock", "model": "mock-model"},
                },
            ],
            "eval_scoring": {
                "backend": "semantic_judge",
                "judge_repeats": 2,
                "semantic_aggregation": "mean",
            },
        },
    )
    out = tmp_path / "run_sem"
    run_benchmark(
        dfn,
        repo_root=_REPO,
        output_dir=out,
        created_at="1970-01-01T00:00:00Z",
        run_id="obs-sem",
        provider_yaml=None,
        environ={"ALWM_FIXTURE_MODE": "1"},
        fixture_mode_force_mock=True,
    )
    mf = load_artifact_file(out / "manifest.json", "benchmark_manifest")
    assert isinstance(mf, BenchmarkRunManifest)
    assert mf.retry_summary is not None
    assert mf.retry_summary.total_judge_invocations == 2
    assert mf.runtime_summary is not None
    assert mf.runtime_summary.judge_phase_seconds >= 0.0


def test_old_manifest_without_runtime_still_loads() -> None:
    """Backward compatibility: fixtures without runtime_summary validate."""
    p = _REPO / "examples" / "v1" / "manifest.json"
    load_artifact_file(p, "benchmark_manifest")
