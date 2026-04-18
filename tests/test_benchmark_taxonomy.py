"""Benchmark taxonomy metadata, optional budgets, and manifest round-trip."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_llm_wiki_matrix.benchmark import (
    load_benchmark_definition,
    run_benchmark,
)

_REPO = Path(__file__).resolve().parents[1]

_TAXONOMY_SUITES = (
    "examples/benchmark_suites/v1/suite.taxonomy.repo_governance.v1.yaml",
    "examples/benchmark_suites/v1/suite.taxonomy.runtime_config.v1.yaml",
    "examples/benchmark_suites/v1/suite.taxonomy.documentation.v1.yaml",
    "examples/benchmark_suites/v1/suite.taxonomy.browser_evidence.v1.yaml",
    "examples/benchmark_suites/v1/suite.taxonomy.browser_checkout.v1.yaml",
    "examples/benchmark_suites/v1/suite.taxonomy.browser_form.v1.yaml",
    "examples/benchmark_suites/v1/suite.taxonomy.browser_traces_compare.v1.yaml",
    "examples/benchmark_suites/v1/suite.taxonomy.matrix_reasoning.v1.yaml",
    "examples/benchmark_suites/v1/suite.taxonomy.multi_agent_coordination.v1.yaml",
    "examples/benchmark_suites/v1/suite.taxonomy.campaign_coordination.v1.yaml",
    "examples/benchmark_suites/v1/suite.taxonomy.integration_stress.v1.yaml",
)


@pytest.mark.parametrize("relpath", _TAXONOMY_SUITES)
def test_taxonomy_example_suite_loads(relpath: str) -> None:
    path = _REPO / relpath
    dfn = load_benchmark_definition(path)
    assert dfn.taxonomy is not None
    assert dfn.taxonomy.taxonomy_version == 1
    assert dfn.taxonomy.task_family
    assert dfn.taxonomy.difficulty
    assert dfn.taxonomy.determinism


def test_legacy_definition_has_no_taxonomy() -> None:
    dfn = load_benchmark_definition(_REPO / "fixtures" / "benchmarks" / "offline.v1.yaml")
    assert dfn.taxonomy is None
    assert dfn.tags == []
    assert dfn.expected_artifact_kinds == []


def test_expected_artifact_kind_unknown_raises() -> None:
    raw = {
        "schema_version": 1,
        "id": "bench.bad.kinds",
        "title": "x",
        "rubric_ref": "fixtures/v1/rubric.json",
        "prompts": [{"id": "p", "text": "ok"}],
        "variants": [
            {
                "id": "v",
                "agent_stack": "a",
                "execution_mode": "cli",
                "backend": {"kind": "mock", "model": "m"},
            }
        ],
        "expected_artifact_kinds": ["not_a_real_kind"],
    }
    from agent_llm_wiki_matrix.benchmark.definitions import BenchmarkDefinitionV1

    with pytest.raises(ValueError, match="Unknown expected artifact kind"):
        BenchmarkDefinitionV1.model_validate(raw)


def test_run_copies_taxonomy_to_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALWM_FIXTURE_MODE", "1")
    rel = "examples/benchmark_suites/v1/suite.taxonomy.repo_governance.v1.yaml"
    dfn = load_benchmark_definition(_REPO / rel)
    out = tmp_path / "run"
    run_benchmark(
        dfn,
        repo_root=_REPO,
        output_dir=out,
        created_at="1970-01-01T00:00:00Z",
        run_id="tax-test",
        provider_yaml=None,
        environ={"ALWM_FIXTURE_MODE": "1"},
        fixture_mode_force_mock=True,
        definition_source_relpath=rel,
    )
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["taxonomy"]["task_family"] == "repo_governance"
    assert manifest["taxonomy"]["difficulty"] == "medium"
    assert manifest["time_budget_seconds"] == 120
    assert manifest["token_budget"] == 2048
    assert manifest["retry_policy"] == {"max_attempts": 2, "backoff_seconds": 1.5}
    assert manifest["tags"] == ["taxonomy", "repo_governance", "v1"]
    assert "benchmark_request" in manifest["expected_artifact_kinds"]


def test_fixture_minimal_runs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALWM_FIXTURE_MODE", "1")
    dfn = load_benchmark_definition(
        _REPO / "fixtures" / "benchmarks" / "suite_taxonomy_minimal.v1.yaml",
    )
    out = tmp_path / "run"
    run_benchmark(
        dfn,
        repo_root=_REPO,
        output_dir=out,
        created_at="1970-01-01T00:00:00Z",
        run_id="min",
        provider_yaml=None,
        environ={"ALWM_FIXTURE_MODE": "1"},
        fixture_mode_force_mock=True,
        definition_source_relpath=None,
    )
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["taxonomy"]["task_family"] == "scaffolding"
    assert len(manifest["cells"]) == 1
