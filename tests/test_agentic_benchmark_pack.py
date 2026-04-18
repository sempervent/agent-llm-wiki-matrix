"""Agentic cross-system benchmark pack: definitions and manifest metadata."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_llm_wiki_matrix.benchmark import load_benchmark_definition, run_benchmark

_REPO = Path(__file__).resolve().parents[1]

_AGENTIC_SUITES = (
    "examples/benchmark_suites/v1/agentic/suite.agentic.repo_implementation.v1.yaml",
    "examples/benchmark_suites/v1/agentic/suite.agentic.docs_drift_repair.v1.yaml",
    "examples/benchmark_suites/v1/agentic/suite.agentic.benchmark_authoring.v1.yaml",
    "examples/benchmark_suites/v1/agentic/suite.agentic.browser_interpretation.v1.yaml",
    "examples/benchmark_suites/v1/agentic/suite.agentic.multi_agent_coordination.v1.yaml",
)


@pytest.mark.parametrize("relpath", _AGENTIC_SUITES)
def test_agentic_suite_loads_with_comparison_metadata(relpath: str) -> None:
    path = _REPO / relpath
    dfn = load_benchmark_definition(path)
    assert dfn.taxonomy is not None
    assert dfn.taxonomy.determinism == "deterministic_fixture"
    assert "agentic_pack" in dfn.tags
    assert len(dfn.success_criteria) >= 1
    assert len(dfn.failure_taxonomy_hints) >= 1
    assert dfn.expected_artifact_kinds


def test_agentic_example_manifest_includes_new_fields() -> None:
    mpath = (
        _REPO
        / "examples"
        / "benchmark_runs"
        / "agentic-pack-repo-implementation"
        / "manifest.json"
    )
    raw = json.loads(mpath.read_text(encoding="utf-8"))
    assert raw["success_criteria"]
    assert raw["failure_taxonomy_hints"]
    assert raw["taxonomy"]["determinism"] == "deterministic_fixture"


def test_agentic_pack_run_round_trip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALWM_FIXTURE_MODE", "1")
    rel = _AGENTIC_SUITES[0]
    dfn = load_benchmark_definition(_REPO / rel)
    out = tmp_path / "run"
    run_benchmark(
        dfn,
        repo_root=_REPO,
        output_dir=out,
        created_at="1970-01-01T00:00:00Z",
        run_id="agentic-pack-rt",
        provider_yaml=None,
        environ={"ALWM_FIXTURE_MODE": "1"},
        fixture_mode_force_mock=True,
        definition_source_relpath=rel,
    )
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["success_criteria"] == [s for s in dfn.success_criteria]
    assert manifest["failure_taxonomy_hints"] == [h for h in dfn.failure_taxonomy_hints]
