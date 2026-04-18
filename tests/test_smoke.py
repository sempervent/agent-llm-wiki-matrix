"""Smoke tests: CLI, imports, and schema validation."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from agent_llm_wiki_matrix import __version__
from agent_llm_wiki_matrix.artifacts import load_artifact_file
from agent_llm_wiki_matrix.cli import main
from agent_llm_wiki_matrix.schema import validate_file

_REPO = Path(__file__).resolve().parents[1]

_COMPOSE_PROFILES = (
    "dev",
    "test",
    "benchmark",
    "benchmark-offline",
    "benchmark-ollama",
    "benchmark-probe",
    "benchmark-llamacpp",
    "browser-verify",
)


@pytest.mark.smoke
def test_version_matches_package() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["version"])
    assert result.exit_code == 0
    assert result.output.strip() == __version__


@pytest.mark.smoke
def test_info_runs() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["info"])
    assert result.exit_code == 0
    assert "version=" in result.output


@pytest.mark.smoke
def test_sample_note_validates_against_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(_REPO)
    monkeypatch.setenv("ALWM_REPO_ROOT", str(_REPO))
    sample = _REPO / "examples" / "sample-note.json"
    validate_file(sample, "schemas/v1/note.schema.json")


@pytest.mark.smoke
def test_schema_missing_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ALWM_REPO_ROOT", str(tmp_path))
    missing = tmp_path / "nope.json"
    missing.write_text("{}", encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        validate_file(missing, "schemas/v1/note.schema.json")


@pytest.mark.smoke
def test_validate_cli_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(_REPO)
    monkeypatch.setenv("ALWM_REPO_ROOT", str(_REPO))
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["validate", str(_REPO / "examples" / "v1" / "evaluation.json"), "evaluation"],
    )
    assert result.exit_code == 0
    assert "ok:" in result.output


@pytest.mark.smoke
def test_benchmark_campaign_plan_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(_REPO)
    monkeypatch.setenv("ALWM_REPO_ROOT", str(_REPO))
    out = tmp_path / "campaign-plan"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "benchmark",
            "campaign",
            "plan",
            "--definition",
            str(_REPO / "examples/campaigns/v1/minimal_offline.v1.yaml"),
            "--output-dir",
            str(out),
            "--created-at",
            "2026-04-17T00:00:00Z",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "planned" in result.output
    assert (out / "campaign-dry-run.json").is_file()
    assert (out / "manifest.json").is_file()
    load_artifact_file(out / "manifest.json", "benchmark_campaign_manifest")
    load_artifact_file(out / "campaign-summary.json", "campaign_summary")


@pytest.mark.smoke
def test_docker_compose_profiles_validate() -> None:
    """Ensure every documented Compose profile still parses (requires ``docker`` on PATH)."""
    if not shutil.which("docker"):
        pytest.skip("docker not on PATH")
    for profile in _COMPOSE_PROFILES:
        proc = subprocess.run(
            ["docker", "compose", "--profile", profile, "config", "--quiet"],
            cwd=_REPO,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        assert proc.returncode == 0, f"profile={profile!r} stderr={proc.stderr!r}"
