"""Validate structured artifacts against JSON Schema and Pydantic models."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from agent_llm_wiki_matrix.browser.models import BrowserEvidence
from agent_llm_wiki_matrix.models import (
    BenchmarkCase,
    BenchmarkRequestRecord,
    BenchmarkResponse,
    BenchmarkRunManifest,
    ComparisonMatrix,
    Evaluation,
    Event,
    Experiment,
    MatrixGridInputs,
    MatrixPairwiseInputs,
    Report,
    Rubric,
    Thought,
)
from agent_llm_wiki_matrix.schema import load_schema, validate_json

_ARTIFACTS: dict[str, tuple[type[BaseModel], str]] = {
    "thought": (Thought, "schemas/v1/thought.schema.json"),
    "event": (Event, "schemas/v1/event.schema.json"),
    "experiment": (Experiment, "schemas/v1/experiment.schema.json"),
    "evaluation": (Evaluation, "schemas/v1/evaluation.schema.json"),
    "matrix": (ComparisonMatrix, "schemas/v1/matrix.schema.json"),
    "report": (Report, "schemas/v1/report.schema.json"),
    "rubric": (Rubric, "schemas/v1/rubric.schema.json"),
    "benchmark_response": (BenchmarkResponse, "schemas/v1/benchmark_response.schema.json"),
    "benchmark_case": (BenchmarkCase, "schemas/v1/benchmark_case.schema.json"),
    "benchmark_request": (BenchmarkRequestRecord, "schemas/v1/benchmark_request.schema.json"),
    "matrix_grid_inputs": (MatrixGridInputs, "schemas/v1/matrix_grid_inputs.schema.json"),
    "matrix_pairwise_inputs": (
        MatrixPairwiseInputs,
        "schemas/v1/matrix_pairwise_inputs.schema.json",
    ),
    "browser_evidence": (BrowserEvidence, "schemas/v1/browser_evidence.schema.json"),
    "benchmark_manifest": (BenchmarkRunManifest, "schemas/v1/manifest.schema.json"),
}


def parse_artifact(kind: str, data: dict[str, Any]) -> BaseModel:
    """Validate `data` with JSON Schema then parse with the matching Pydantic model."""
    if kind not in _ARTIFACTS:
        msg = f"Unknown artifact kind: {kind}"
        raise KeyError(msg)
    model_cls, schema_path = _ARTIFACTS[kind]
    schema = load_schema(schema_path)
    validate_json(data, schema)
    return model_cls.model_validate(data)


def load_artifact_file(path: Path, kind: str) -> BaseModel:
    """Load JSON from disk and validate as `kind`."""
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        msg = "Artifact JSON must be an object at the top level"
        raise TypeError(msg)
    return parse_artifact(kind, data)


def list_artifact_kinds() -> tuple[str, ...]:
    """Return supported artifact kinds."""
    return tuple(sorted(_ARTIFACTS.keys()))
