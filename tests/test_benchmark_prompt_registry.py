"""Benchmark prompt registry resolution and artifact fields."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from agent_llm_wiki_matrix.artifacts import load_artifact_file
from agent_llm_wiki_matrix.benchmark import (
    BenchmarkPromptResolutionError,
    load_benchmark_definition,
    resolve_benchmark_prompts,
    run_benchmark,
)
from agent_llm_wiki_matrix.benchmark.definitions import (
    BackendSpec,
    BenchmarkDefinitionV1,
    PromptItem,
    VariantSpec,
)
from agent_llm_wiki_matrix.models import BenchmarkRequestRecord, BenchmarkResponse

_REPO = Path(__file__).resolve().parents[1]


def test_resolve_inline_and_registry_mixed() -> None:
    dfn = load_benchmark_definition(_REPO / "fixtures" / "benchmarks" / "registry_mixed.v1.yaml")
    resolved = resolve_benchmark_prompts(_REPO, dfn)
    assert len(resolved) == 2
    assert resolved[0].prompt_source == "inline"
    assert resolved[0].prompt_registry_id is None
    assert "INLINE-OK" in resolved[0].rendered_text
    assert resolved[1].prompt_source == "registry"
    assert resolved[1].prompt_registry_id == "scaffold.echo.v1"
    assert resolved[1].registry_document_version is not None
    assert resolved[1].prompt_source_relpath == "prompts/versions/scaffold.echo.v1.txt"
    assert "OK" in resolved[1].rendered_text


def test_registry_version_pin_ok() -> None:
    dfn = load_benchmark_definition(
        _REPO / "fixtures" / "benchmarks" / "registry_version_ok.v1.yaml",
    )
    resolved = resolve_benchmark_prompts(_REPO, dfn)
    assert resolved[0].registry_document_version == "1.0.0"
    assert "fixture pin body" in resolved[0].rendered_text.lower()


def test_registry_version_mismatch_raises() -> None:
    dfn = load_benchmark_definition(
        _REPO / "fixtures" / "benchmarks" / "registry_version_bad.v1.yaml",
    )
    with pytest.raises(BenchmarkPromptResolutionError, match="version mismatch"):
        resolve_benchmark_prompts(_REPO, dfn)


def test_missing_prompt_ref_raises() -> None:
    dfn = load_benchmark_definition(
        _REPO / "fixtures" / "benchmarks" / "registry_missing_ref.v1.yaml",
    )
    with pytest.raises(BenchmarkPromptResolutionError, match="Unknown prompt_ref"):
        resolve_benchmark_prompts(_REPO, dfn)


def test_path_escape_rejected(tmp_path: Path) -> None:
    reg = tmp_path / "bad_registry.yaml"
    reg.write_text(
        yaml.dump(
            {
                "version": "1.0.0",
                "updated_at": "1970-01-01T00:00:00Z",
                "prompts": [
                    {
                        "id": "evil.v1",
                        "description": "",
                        "path": "../../../etc/passwd",
                    },
                ],
            },
        ),
        encoding="utf-8",
    )
    dfn = BenchmarkDefinitionV1(
        schema_version=1,
        id="bench.tmp.escape",
        title="t",
        rubric_ref="fixtures/v1/rubric.json",
        prompt_registry_ref="bad_registry.yaml",
        prompts=[
            PromptItem(id="p1", prompt_ref="evil.v1"),
        ],
        variants=[
            VariantSpec(
                id="v-cli",
                agent_stack="alwm-cli",
                execution_mode="cli",
                backend=BackendSpec(kind="mock", model="mock-model"),
            ),
        ],
    )
    with pytest.raises(BenchmarkPromptResolutionError, match="escape|Prompt path escapes"):
        resolve_benchmark_prompts(tmp_path, dfn, prompt_registry_path=reg)


def test_run_benchmark_mixed_writes_registry_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALWM_FIXTURE_MODE", "1")
    dfn = load_benchmark_definition(_REPO / "fixtures" / "benchmarks" / "registry_mixed.v1.yaml")
    out = tmp_path / "run"
    run_benchmark(
        dfn,
        repo_root=_REPO,
        output_dir=out,
        created_at="1970-01-01T00:00:00Z",
        run_id="reg-test",
        provider_yaml=None,
        environ={"ALWM_FIXTURE_MODE": "1"},
        fixture_mode_force_mock=True,
    )
    inline_req = out / "cells" / "v-cli__p-inline" / "request.json"
    reg_req = out / "cells" / "v-cli__p-reg" / "request.json"
    br_inline = load_artifact_file(
        out / "cells" / "v-cli__p-inline" / "benchmark_response.json",
        "benchmark_response",
    )
    br_reg = load_artifact_file(
        out / "cells" / "v-cli__p-reg" / "benchmark_response.json",
        "benchmark_response",
    )
    assert isinstance(br_inline, BenchmarkResponse)
    assert br_inline.prompt_source == "inline"
    assert br_inline.prompt_registry_id is None
    assert isinstance(br_reg, BenchmarkResponse)
    assert br_reg.prompt_source == "registry"
    assert br_reg.prompt_registry_id == "scaffold.echo.v1"
    assert br_reg.prompt_source_relpath == "prompts/versions/scaffold.echo.v1.txt"

    r_inline = load_artifact_file(inline_req, "benchmark_request")
    r_reg = load_artifact_file(reg_req, "benchmark_request")
    assert isinstance(r_inline, BenchmarkRequestRecord)
    assert isinstance(r_reg, BenchmarkRequestRecord)
    assert r_inline.prompt_text == br_inline.prompt_text
    assert r_reg.prompt_text == br_reg.prompt_text


def test_backward_compat_inline_only_definition() -> None:
    dfn = load_benchmark_definition(_REPO / "fixtures" / "benchmarks" / "offline.v1.yaml")
    resolved = resolve_benchmark_prompts(_REPO, dfn)
    assert all(r.prompt_source == "inline" for r in resolved)
    assert all(r.prompt_registry_id is None for r in resolved)


def test_prompt_registry_path_override(tmp_path: Path) -> None:
    reg = tmp_path / "custom.yaml"
    body = tmp_path / "body.txt"
    body.write_text("CUSTOM\n", encoding="utf-8")
    reg.write_text(
        yaml.dump(
            {
                "version": "2.0.0",
                "updated_at": "1970-01-01T00:00:00Z",
                "prompts": [
                    {
                        "id": "custom.id.v1",
                        "description": "",
                        "path": str(body.relative_to(tmp_path)).replace("\\", "/"),
                    },
                ],
            },
        ),
        encoding="utf-8",
    )
    dfn = BenchmarkDefinitionV1(
        schema_version=1,
        id="bench.tmp.override",
        title="t",
        rubric_ref="fixtures/v1/rubric.json",
        prompts=[PromptItem(id="p1", prompt_ref="custom.id.v1")],
        variants=[
            VariantSpec(
                id="v-cli",
                agent_stack="alwm-cli",
                execution_mode="cli",
                backend=BackendSpec(kind="mock", model="mock-model"),
            ),
        ],
    )
    resolved = resolve_benchmark_prompts(
        tmp_path,
        dfn,
        prompt_registry_path=reg,
    )
    assert resolved[0].rendered_text.strip() == "CUSTOM"
    assert resolved[0].registry_document_version == "2.0.0"


def test_example_registry_mixed_suite_loads() -> None:
    path = _REPO / "examples" / "benchmark_suites" / "v1" / "registry.mixed.v1.yaml"
    dfn = load_benchmark_definition(path)
    assert dfn.id == "bench.examples.registry.mixed.v1"
    resolved = resolve_benchmark_prompts(_REPO, dfn)
    assert resolved[1].prompt_registry_id == "bench.sample.prompt.v1"
    assert "REGISTRY-OK" in resolved[1].rendered_text
