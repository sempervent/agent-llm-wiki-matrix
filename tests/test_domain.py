"""Domain models, JSON Schemas, and fixture validation."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner
from pydantic import ValidationError

from agent_llm_wiki_matrix.artifacts import load_artifact_file, parse_artifact
from agent_llm_wiki_matrix.cli import main

_REPO = Path(__file__).resolve().parents[1]
_FIXTURES = _REPO / "fixtures" / "v1"


@pytest.mark.parametrize(
    ("filename", "kind"),
    [
        ("thought.json", "thought"),
        ("event.json", "event"),
        ("experiment.json", "experiment"),
        ("evaluation.json", "evaluation"),
        ("matrix.json", "matrix"),
        ("report.json", "report"),
        ("rubric.json", "rubric"),
        ("benchmark_response.json", "benchmark_response"),
    ],
)
def test_fixture_validates(filename: str, kind: str) -> None:
    path = _FIXTURES / filename
    load_artifact_file(path, kind)


def test_matrix_rejects_ragged_rows() -> None:
    bad = {
        "id": "bad-matrix",
        "title": "bad",
        "matrix_kind": "grid",
        "row_labels": ["a", "b"],
        "col_labels": ["x", "y"],
        "scores": [[1.0, 2.0], [3.0]],
        "metric": "m",
        "created_at": "2026-04-17T12:00:00Z",
    }
    with pytest.raises(ValidationError):
        parse_artifact("matrix", bad)


def test_validate_cli_ok() -> None:
    runner = CliRunner()
    path = _FIXTURES / "thought.json"
    result = runner.invoke(main, ["validate", str(path), "thought"])
    assert result.exit_code == 0
    assert "ok" in result.output
