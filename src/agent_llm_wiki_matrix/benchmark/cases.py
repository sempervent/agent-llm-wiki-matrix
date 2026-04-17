"""Load and validate versioned benchmark case definitions (JSON / YAML)."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from agent_llm_wiki_matrix.artifacts import load_artifact_file, parse_artifact
from agent_llm_wiki_matrix.models import BenchmarkCase


def load_benchmark_case(path: Path) -> BenchmarkCase:
    """Load a benchmark case from JSON or YAML (JSON Schema + Pydantic, like ``alwm validate``)."""
    raw_text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        data = yaml.safe_load(raw_text)
    else:
        data = json.loads(raw_text)
    if not isinstance(data, dict):
        msg = "Benchmark case root must be an object"
        raise TypeError(msg)
    model = parse_artifact("benchmark_case", data)
    if not isinstance(model, BenchmarkCase):
        msg = "Expected BenchmarkCase"
        raise TypeError(msg)
    return model


def validate_benchmark_case_file(path: Path) -> BenchmarkCase:
    """Validate a file with JSON Schema + Pydantic (same as ``alwm validate … benchmark_case``)."""
    model = load_artifact_file(path, "benchmark_case")
    if not isinstance(model, BenchmarkCase):
        msg = "Expected a BenchmarkCase artifact"
        raise TypeError(msg)
    return model
