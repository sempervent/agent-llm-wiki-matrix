"""Benchmark case schema and fixture cases."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from agent_llm_wiki_matrix.artifacts import load_artifact_file, parse_artifact
from agent_llm_wiki_matrix.benchmark.cases import load_benchmark_case
from agent_llm_wiki_matrix.models import BenchmarkCase

_REPO = Path(__file__).resolve().parents[1]
_CASE_FIXTURES = _REPO / "fixtures" / "benchmark_cases" / "v1"


@pytest.mark.parametrize(
    "filename",
    [
        "case.repo.scaffold.v1.json",
        "case.markdown.synthesis.v1.json",
        "case.comparison.matrix.v1.json",
        "case.browser.evidence.v1.json",
    ],
)
def test_benchmark_case_fixture_validates(filename: str) -> None:
    path = _CASE_FIXTURES / filename
    load_artifact_file(path, "benchmark_case")


@pytest.mark.parametrize("filename", ["case.repo.scaffold.v1.json"])
def test_load_benchmark_case_helper(filename: str) -> None:
    bc = load_benchmark_case(_CASE_FIXTURES / filename)
    assert isinstance(bc, BenchmarkCase)
    assert bc.deterministic_fixture_mode is True


def test_benchmark_case_rejects_unknown_expected_kind() -> None:
    bad = {
        "schema_version": 1,
        "id": "bad",
        "title": "bad",
        "task_kind": "repo_scaffolding",
        "prompt": "x",
        "expected_artifact_kinds": ["not_a_real_kind"],
        "rubric_ref": "fixtures/v1/rubric.json",
        "execution": {
            "mode": "cli",
            "agent_stack_label": "x",
            "backend_policy": "mock",
        },
        "deterministic_fixture_mode": True,
    }
    with pytest.raises(ValidationError):
        parse_artifact("benchmark_case", bad)
