"""Opt-in live benchmark verification (Ollama + OpenAI-compatible). Skips when unavailable."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from agent_llm_wiki_matrix.artifacts import load_artifact_file
from agent_llm_wiki_matrix.benchmark import load_benchmark_definition, run_benchmark
from agent_llm_wiki_matrix.benchmark.definitions import BenchmarkDefinitionV1
from agent_llm_wiki_matrix.benchmark.live_probe import (
    ollama_model_available,
    probe_ollama_api,
    probe_openai_compatible_api,
)
from agent_llm_wiki_matrix.models import BenchmarkResponse

_REPO = Path(__file__).resolve().parents[2]


def _definition_with_backend_model(dfn: BenchmarkDefinitionV1, model: str) -> BenchmarkDefinitionV1:
    new_variants = []
    for v in dfn.variants:
        nb = v.backend.model_copy(update={"model": model})
        new_variants.append(v.model_copy(update={"backend": nb}))
    return dfn.model_copy(update={"variants": new_variants})


@pytest.mark.integration
@pytest.mark.live_ollama
def test_live_benchmark_ollama_end_to_end(tmp_path: Path) -> None:
    if os.environ.get("ALWM_LIVE_BENCHMARK_OLLAMA") != "1":
        pytest.skip("Set ALWM_LIVE_BENCHMARK_OLLAMA=1 for live Ollama verification")
    host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
    model = os.environ.get("OLLAMA_MODEL", "llama3.2")
    if not probe_ollama_api(host):
        pytest.skip(f"Ollama API not reachable at {host}")
    if not ollama_model_available(host, model):
        pytest.skip(
            f"Ollama has no model matching {model!r}; pull it first (e.g. ollama pull {model})",
        )
    dfn = _definition_with_backend_model(
        load_benchmark_definition(_REPO / "benchmarks" / "v1" / "ollama.v1.yaml"),
        model,
    )
    out = tmp_path / "live-ollama"
    env = {**os.environ, "ALWM_FIXTURE_MODE": "0", "OLLAMA_HOST": host}
    run_benchmark(
        dfn,
        repo_root=_REPO,
        output_dir=out,
        created_at="1970-01-01T00:00:00Z",
        run_id="integration-live-ollama",
        provider_yaml=None,
        environ=env,
        fixture_mode_force_mock=False,
    )
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["benchmark_id"] == "bench.ollama.v1"
    assert len(manifest["cells"]) >= 1
    br_path = out / manifest["cells"][0]["aggregate_response_relpath"]
    raw = load_artifact_file(br_path, "benchmark_response")
    assert isinstance(raw, BenchmarkResponse)
    assert len(raw.response_text) > 0


@pytest.mark.integration
@pytest.mark.live_llamacpp
def test_live_benchmark_openai_compatible_end_to_end(tmp_path: Path) -> None:
    if os.environ.get("ALWM_LIVE_BENCHMARK_LLAMACPP") != "1":
        pytest.skip("Set ALWM_LIVE_BENCHMARK_LLAMACPP=1 for live OpenAI-compatible verification")
    base = os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:8080/v1")
    model = os.environ.get("OPENAI_MODEL", "gpt-oss")
    if not probe_openai_compatible_api(base):
        pytest.skip(f"OpenAI-compatible API not reachable at {base}/models")
    dfn = _definition_with_backend_model(
        load_benchmark_definition(_REPO / "benchmarks" / "v1" / "llamacpp.v1.yaml"),
        model,
    )
    out = tmp_path / "live-llamacpp"
    env = {
        **os.environ,
        "ALWM_FIXTURE_MODE": "0",
        "OPENAI_BASE_URL": base,
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", "not-needed-local"),
    }
    run_benchmark(
        dfn,
        repo_root=_REPO,
        output_dir=out,
        created_at="1970-01-01T00:00:00Z",
        run_id="integration-live-llamacpp",
        provider_yaml=None,
        environ=env,
        fixture_mode_force_mock=False,
    )
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["benchmark_id"] == "bench.llamacpp.v1"
    assert len(manifest["cells"]) >= 1
    br_path = out / manifest["cells"][0]["aggregate_response_relpath"]
    raw = load_artifact_file(br_path, "benchmark_response")
    assert isinstance(raw, BenchmarkResponse)
    assert len(raw.response_text) > 0
