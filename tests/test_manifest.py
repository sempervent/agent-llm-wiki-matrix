"""Benchmark run manifest: JSON Schema + Pydantic validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from jsonschema.exceptions import ValidationError as JSONSchemaValidationError

from agent_llm_wiki_matrix.artifacts import load_artifact_file, parse_artifact
from agent_llm_wiki_matrix.cli import main

_REPO = Path(__file__).resolve().parents[1]


def test_fixture_manifest_validates() -> None:
    load_artifact_file(_REPO / "fixtures" / "v1" / "manifest.json", "benchmark_manifest")


def test_example_manifests_with_optional_provenance_validate() -> None:
    load_artifact_file(
        _REPO / "examples" / "benchmark_runs" / "registry-four-modes" / "manifest.json",
        "benchmark_manifest",
    )


def test_taxonomy_example_run_manifest_validates() -> None:
    load_artifact_file(
        _REPO / "examples" / "benchmark_runs" / "taxonomy-repo-governance" / "manifest.json",
        "benchmark_manifest",
    )
    load_artifact_file(
        _REPO / "examples" / "benchmark_runs" / "taxonomy-runtime-config" / "manifest.json",
        "benchmark_manifest",
    )


def test_manifest_optional_null_provenance_round_trip() -> None:
    path = _REPO / "fixtures" / "v1" / "manifest.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["definition_source_relpath"] = None
    raw["prompt_registry_effective_ref"] = None
    parse_artifact("benchmark_manifest", raw)


def test_manifest_rejects_missing_run_id() -> None:
    path = _REPO / "fixtures" / "v1" / "manifest.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    del raw["run_id"]
    with pytest.raises(JSONSchemaValidationError):
        parse_artifact("benchmark_manifest", raw)


def test_manifest_rejects_extra_top_level_property() -> None:
    path = _REPO / "fixtures" / "v1" / "manifest.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["unexpected"] = "nope"
    with pytest.raises(JSONSchemaValidationError):
        parse_artifact("benchmark_manifest", raw)


def test_manifest_rejects_missing_cell_field() -> None:
    path = _REPO / "fixtures" / "v1" / "manifest.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    del raw["cells"][0]["evaluation_relpath"]
    with pytest.raises(JSONSchemaValidationError):
        parse_artifact("benchmark_manifest", raw)


def test_manifest_schema_error_before_pydantic_extra_field() -> None:
    """Schema rejects unknown cell keys before Pydantic extra=forbid."""
    path = _REPO / "fixtures" / "v1" / "manifest.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["cells"][0]["extra_cell_field"] = "x"
    with pytest.raises(JSONSchemaValidationError):
        parse_artifact("benchmark_manifest", raw)


def test_validate_cli_benchmark_manifest() -> None:
    runner = CliRunner()
    path = _REPO / "fixtures" / "v1" / "manifest.json"
    result = runner.invoke(main, ["validate", str(path), "benchmark_manifest"])
    assert result.exit_code == 0
    assert "ok" in result.output


def test_pydantic_rejects_wrong_schema_version_if_schema_loosened() -> None:
    """Pydantic enforces schema_version == 1; bypass JSON Schema to hit Pydantic."""
    path = _REPO / "fixtures" / "v1" / "manifest.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["schema_version"] = 2
    with pytest.raises(JSONSchemaValidationError):
        parse_artifact("benchmark_manifest", raw)


def test_offline_run_manifest_validates_as_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from agent_llm_wiki_matrix.benchmark import load_benchmark_definition, run_benchmark

    monkeypatch.setenv("ALWM_FIXTURE_MODE", "1")
    dfn = load_benchmark_definition(_REPO / "fixtures" / "benchmarks" / "offline.v1.yaml")
    out = tmp_path / "run"
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
    load_artifact_file(out / "manifest.json", "benchmark_manifest")
