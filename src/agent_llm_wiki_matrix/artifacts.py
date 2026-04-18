"""Validate structured artifacts against JSON Schema and Pydantic models."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from agent_llm_wiki_matrix.benchmark.campaign_definitions import BenchmarkCampaignDefinitionV1
from agent_llm_wiki_matrix.browser.models import BrowserEvidence
from agent_llm_wiki_matrix.models import (
    BenchmarkCampaignManifest,
    BenchmarkCase,
    BenchmarkRequestRecord,
    BenchmarkResponse,
    BenchmarkRunManifest,
    CampaignCompareV1,
    CampaignResultPackComparisonV1,
    CampaignResultPackV1,
    CampaignSemanticSummaryV1,
    CampaignSummaryV1,
    ComparisonMatrix,
    Evaluation,
    EvaluationJudgeProvenance,
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
    "evaluation_judge_provenance": (
        EvaluationJudgeProvenance,
        "schemas/v1/evaluation_judge_provenance.schema.json",
    ),
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
    "benchmark_campaign_definition": (
        BenchmarkCampaignDefinitionV1,
        "schemas/v1/benchmark_campaign.schema.json",
    ),
    "benchmark_campaign_manifest": (
        BenchmarkCampaignManifest,
        "schemas/v1/benchmark_campaign_manifest.schema.json",
    ),
    "campaign_definition": (
        BenchmarkCampaignDefinitionV1,
        "schemas/v1/benchmark_campaign.schema.json",
    ),
    "campaign_manifest": (
        BenchmarkCampaignManifest,
        "schemas/v1/benchmark_campaign_manifest.schema.json",
    ),
    "campaign_summary": (CampaignSummaryV1, "schemas/v1/campaign_summary.schema.json"),
    "campaign_semantic_summary": (
        CampaignSemanticSummaryV1,
        "schemas/v1/campaign_semantic_summary.schema.json",
    ),
    "campaign_result_pack": (
        CampaignResultPackV1,
        "schemas/v1/campaign_result_pack.schema.json",
    ),
    "campaign_result_pack_comparison": (
        CampaignResultPackComparisonV1,
        "schemas/v1/campaign_result_pack_comparison.schema.json",
    ),
    "campaign_compare": (
        CampaignCompareV1,
        "schemas/v1/campaign_compare.schema.json",
    ),
}


def _benchmark_run_context_model() -> tuple[type[BaseModel], str]:
    """Lazy import to keep ``artifacts`` import graph small."""
    from agent_llm_wiki_matrix.pipelines.benchmark_run_context import BenchmarkRunContextV1

    return BenchmarkRunContextV1, "schemas/v1/benchmark_run_context.schema.json"


def parse_artifact(kind: str, data: dict[str, Any]) -> BaseModel:
    """Validate `data` with JSON Schema then parse with the matching Pydantic model."""
    if kind == "benchmark_run_context":
        model_cls, schema_path = _benchmark_run_context_model()
    elif kind not in _ARTIFACTS:
        msg = f"Unknown artifact kind: {kind}"
        raise KeyError(msg)
    else:
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
    return tuple(sorted((*_ARTIFACTS.keys(), "benchmark_run_context")))
