"""Smoke tests: CLI, imports, and schema validation."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from agent_llm_wiki_matrix import __version__
from agent_llm_wiki_matrix.cli import main
from agent_llm_wiki_matrix.schema import validate_file


def test_version_matches_package() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["version"])
    assert result.exit_code == 0
    assert result.output.strip() == __version__


def test_info_runs() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["info"])
    assert result.exit_code == 0
    assert "version=" in result.output


def test_sample_note_validates_against_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    repo = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(repo)
    monkeypatch.setenv("ALWM_REPO_ROOT", str(repo))
    sample = repo / "examples" / "sample-note.json"
    validate_file(sample, "schemas/v1/note.schema.json")


def test_schema_missing_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ALWM_REPO_ROOT", str(tmp_path))
    missing = tmp_path / "nope.json"
    missing.write_text("{}", encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        validate_file(missing, "schemas/v1/note.schema.json")
