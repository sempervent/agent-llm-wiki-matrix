"""Stable benchmark comparison fingerprints (SHA-256 over canonical JSON)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from agent_llm_wiki_matrix.benchmark import (
    load_benchmark_definition,
    resolve_benchmark_prompts,
    run_benchmark,
)
from agent_llm_wiki_matrix.benchmark.fingerprints import (
    build_benchmark_comparison_fingerprints,
    fingerprint_suite_definition,
    sha256_canonical,
)
from agent_llm_wiki_matrix.pipelines.evaluation_backends import JudgeRepeatParams
from agent_llm_wiki_matrix.providers.benchmark_config import (
    load_provider_config_for_benchmark_variant,
)

_REPO = Path(__file__).resolve().parents[1]


def test_sha256_canonical_sorts_keys() -> None:
    a = sha256_canonical({"z": 1, "a": 2})
    b = sha256_canonical({"a": 2, "z": 1})
    assert a == b
    assert a.startswith("sha256:")


def test_suite_definition_excludes_title() -> None:
    d1 = load_benchmark_definition(_REPO / "fixtures/benchmarks/longitudinal.v1.yaml")
    d2 = d1.model_copy(update={"title": "Different title"})
    assert fingerprint_suite_definition(d1) == fingerprint_suite_definition(d2)


def test_run_benchmark_manifest_has_fingerprints(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALWM_FIXTURE_MODE", "1")
    dfn = load_benchmark_definition(_REPO / "fixtures/benchmarks/offline.v1.yaml")
    out = tmp_path / "run"
    run_benchmark(
        dfn,
        repo_root=_REPO,
        output_dir=out,
        created_at="1970-01-01T00:00:00Z",
        run_id="fp-test",
        provider_yaml=None,
        environ={"ALWM_FIXTURE_MODE": "1"},
        fixture_mode_force_mock=True,
    )
    raw = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert "comparison_fingerprints" in raw
    fp = raw["comparison_fingerprints"]
    for k in (
        "suite_definition",
        "prompt_set",
        "provider_config",
        "scoring_config",
        "browser_config",
        "prompt_registry_state",
    ):
        assert k in fp
        assert fp[k].startswith("sha256:")
        assert len(fp[k]) == 7 + 64


def test_longitudinal_fixture_fingerprints_stable() -> None:
    os.environ["ALWM_FIXTURE_MODE"] = "1"
    d = load_benchmark_definition(_REPO / "fixtures/benchmarks/longitudinal.v1.yaml")
    rp = resolve_benchmark_prompts(_REPO, d)
    env = {"ALWM_FIXTURE_MODE": "1"}
    vpc = {
        v.id: load_provider_config_for_benchmark_variant(
            yaml_path=None,
            environ=env,
            backend_kind=v.backend.kind,
            backend_model=v.backend.model,
            fixture_mode_force_mock=True,
        )
        for v in d.variants
    }
    fp = build_benchmark_comparison_fingerprints(
        repo_root=_REPO,
        definition=d,
        resolved_prompts=rp,
        variant_provider_configs=vpc,
        scoring_backend="deterministic",
        hybrid_weights=None,
        judge_repeat_params=JudgeRepeatParams(),
        judge_provider_cfg=None,
        prompt_registry_path=None,
    )
    assert fp.suite_definition == (
        "sha256:4b999adcafe86132a87263d19979bcb48b809ed69ba081ba3e8deb4a6057bb7f"
    )
