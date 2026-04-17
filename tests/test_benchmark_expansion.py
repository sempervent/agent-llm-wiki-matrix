"""Registry-backed benchmark suites (examples), manifest provenance, rubric wiring."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_llm_wiki_matrix.benchmark import (
    load_benchmark_definition,
    resolve_benchmark_prompts,
    resolve_registry_yaml_path,
    run_benchmark,
)
from agent_llm_wiki_matrix.prompt_registry import load_prompt_registry_yaml

_REPO = Path(__file__).resolve().parents[1]

_EXAMPLE_SUITES = (
    "examples/benchmark_suites/v1/suite.registry.four_modes.v1.yaml",
    "examples/benchmark_suites/v1/suite.registry.strict_duo.v1.yaml",
    "examples/benchmark_suites/v1/suite.registry.generous_duo.v1.yaml",
)


@pytest.mark.parametrize("relpath", _EXAMPLE_SUITES)
def test_example_registry_suite_loads_and_resolves(relpath: str) -> None:
    path = _REPO / relpath
    dfn = load_benchmark_definition(path)
    resolved = resolve_benchmark_prompts(_REPO, dfn)
    reg_ver = load_prompt_registry_yaml(_REPO / "prompts" / "registry.yaml").version
    assert len(resolved) == len(dfn.prompts)
    assert all(r.prompt_source == "registry" for r in resolved)
    assert all(r.prompt_registry_id is not None for r in resolved)
    assert all(r.registry_document_version == reg_ver for r in resolved)


def test_resolve_registry_yaml_path_default_registry() -> None:
    path = _REPO / _EXAMPLE_SUITES[0]
    dfn = load_benchmark_definition(path)
    reg = resolve_registry_yaml_path(repo_root=_REPO, definition=dfn, prompt_registry_path=None)
    assert reg == (_REPO / "prompts" / "registry.yaml").resolve()


def test_run_four_modes_writes_manifest_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALWM_FIXTURE_MODE", "1")
    dfn = load_benchmark_definition(_REPO / _EXAMPLE_SUITES[0])
    out = tmp_path / "run"
    def_rel = "examples/benchmark_suites/v1/suite.registry.four_modes.v1.yaml"
    run_benchmark(
        dfn,
        repo_root=_REPO,
        output_dir=out,
        created_at="1970-01-01T00:00:00Z",
        run_id="exp-four-modes",
        provider_yaml=None,
        environ={"ALWM_FIXTURE_MODE": "1"},
        fixture_mode_force_mock=True,
        definition_source_relpath=def_rel,
    )
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["definition_source_relpath"] == def_rel
    assert manifest["prompt_registry_effective_ref"] == "prompts/registry.yaml"
    assert manifest["benchmark_id"] == "bench.examples.suite.registry.four_modes.v1"
    assert len(manifest["cells"]) == 4


def test_fixture_four_modes_loads() -> None:
    dfn = load_benchmark_definition(_REPO / "fixtures" / "benchmarks" / "suite_four_modes.v1.yaml")
    assert dfn.id == "bench.fixtures.suite.four_modes.v1"
    resolved = resolve_benchmark_prompts(_REPO, dfn)
    assert len(resolved) == 4
    ids = {r.prompt_registry_id for r in resolved}
    assert ids == {
        "bench.task.repo_governed.v1",
        "bench.task.markdown_synthesis.v1",
        "bench.task.matrix_reasoning.v1",
        "bench.task.browser_evidence.v1",
    }


def test_run_inline_only_manifest_optional_provenance_none(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALWM_FIXTURE_MODE", "1")
    dfn = load_benchmark_definition(_REPO / "fixtures" / "benchmarks" / "offline.v1.yaml")
    out = tmp_path / "run"
    run_benchmark(
        dfn,
        repo_root=_REPO,
        output_dir=out,
        created_at="1970-01-01T00:00:00Z",
        run_id="inline-only",
        provider_yaml=None,
        environ={"ALWM_FIXTURE_MODE": "1"},
        fixture_mode_force_mock=True,
    )
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest.get("definition_source_relpath") is None
    assert manifest.get("prompt_registry_effective_ref") is None
