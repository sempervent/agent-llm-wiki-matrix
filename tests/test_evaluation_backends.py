"""Semantic / hybrid rubric scoring (mock judge; no live network in default tests)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from agent_llm_wiki_matrix.artifacts import load_artifact_file
from agent_llm_wiki_matrix.benchmark import run_benchmark
from agent_llm_wiki_matrix.benchmark.definitions import BenchmarkDefinitionV1, EvalHybridWeights
from agent_llm_wiki_matrix.models import Evaluation, EvaluationJudgeProvenance
from agent_llm_wiki_matrix.pipelines.evaluation_backends import (
    JudgeRepeatParams,
    evaluate_with_scoring_backend,
    parse_judge_json,
)
from agent_llm_wiki_matrix.providers.benchmark_config import load_judge_provider_config

_REPO = Path(__file__).resolve().parents[1]


def test_parse_judge_json_ok() -> None:
    raw = '{"scores": {"a": 0.25, "b": 1.0}, "rationale": "x"}'
    scores, err = parse_judge_json(raw)
    assert err is None
    assert scores == {"a": 0.25, "b": 1.0}


def test_mock_semantic_single_run_omits_repeat_metadata() -> None:
    rubric_path = _REPO / "fixtures" / "v1" / "rubric.json"
    cfg = load_judge_provider_config(
        yaml_path=None,
        environ={"ALWM_FIXTURE_MODE": "1"},
        judge_live=False,
    )
    ev, prov, _m = evaluate_with_scoring_backend(
        subject_ref="cells/x__y/benchmark_response.json",
        text="hello fixture",
        rubric_path=rubric_path,
        evaluation_id="e1",
        evaluated_at="1970-01-01T00:00:00Z",
        scoring_backend="semantic_judge",
        hybrid_weights=None,
        judge_provider_cfg=cfg,
        judge_live=False,
        evaluation_json_relpath="cells/x__y/evaluation.json",
        judge_repeat=JudgeRepeatParams(count=1),
    )
    assert ev.judge_repeat_count is None
    assert ev.judge_semantic_aggregation is None
    assert ev.judge_low_confidence is None
    assert prov is not None
    assert prov.repeat_aggregation is None


def test_mock_semantic_produces_provenance_and_evaluation() -> None:
    rubric_path = _REPO / "fixtures" / "v1" / "rubric.json"
    cfg = load_judge_provider_config(
        yaml_path=None,
        environ={"ALWM_FIXTURE_MODE": "1"},
        judge_live=False,
    )
    ev, prov, _metrics = evaluate_with_scoring_backend(
        subject_ref="cells/x__y/benchmark_response.json",
        text="hello fixture",
        rubric_path=rubric_path,
        evaluation_id="e1",
        evaluated_at="1970-01-01T00:00:00Z",
        scoring_backend="semantic_judge",
        hybrid_weights=None,
        judge_provider_cfg=cfg,
        judge_live=False,
        evaluation_json_relpath="cells/x__y/evaluation.json",
    )
    assert isinstance(ev, Evaluation)
    assert ev.scoring_backend == "semantic_judge"
    assert isinstance(prov, EvaluationJudgeProvenance)
    assert prov.provider.kind == "mock"
    assert prov.parse_ok is True
    assert set(ev.scores.keys()) == {"clarity", "traceability"}


def test_repeated_semantic_aggregation_provenance_and_low_confidence() -> None:
    rubric_path = _REPO / "fixtures" / "v1" / "rubric.json"
    cfg = load_judge_provider_config(
        yaml_path=None,
        environ={"ALWM_FIXTURE_MODE": "1"},
        judge_live=False,
    )
    ev, prov, _metrics = evaluate_with_scoring_backend(
        subject_ref="subj",
        text="repeat me",
        rubric_path=rubric_path,
        evaluation_id="e-repeat",
        evaluated_at="1970-01-01T00:00:00Z",
        scoring_backend="semantic_judge",
        hybrid_weights=None,
        judge_provider_cfg=cfg,
        judge_live=False,
        evaluation_json_relpath="eval.json",
        judge_repeat=JudgeRepeatParams(
            count=3,
            strategy="mean",
            max_criterion_range=0.0,
        ),
    )
    assert ev.judge_repeat_count == 3
    assert ev.judge_semantic_aggregation == "mean"
    assert ev.judge_low_confidence is True
    assert prov is not None and prov.repeat_aggregation is not None
    assert prov.repeat_aggregation.repeat_count == 3
    assert len(prov.repeat_aggregation.runs) == 3
    assert prov.repeat_aggregation.confidence.low_confidence is True
    assert prov.repeat_aggregation.disagreement.max_range_across_criteria > 0.0


def test_hybrid_differs_from_pure_deterministic() -> None:
    rubric_path = _REPO / "fixtures" / "v1" / "rubric.json"
    cfg = load_judge_provider_config(
        yaml_path=None,
        environ={"ALWM_FIXTURE_MODE": "1"},
        judge_live=False,
    )
    hw = EvalHybridWeights(deterministic_weight=0.5, semantic_weight=0.5)
    _ev, prov, _m = evaluate_with_scoring_backend(
        subject_ref="subj",
        text="hybrid text",
        rubric_path=rubric_path,
        evaluation_id="e2",
        evaluated_at="1970-01-01T00:00:00Z",
        scoring_backend="hybrid",
        hybrid_weights=hw,
        judge_provider_cfg=cfg,
        judge_live=False,
        evaluation_json_relpath="eval.json",
    )
    assert prov is not None and prov.hybrid_aggregation is not None
    assert prov.hybrid_aggregation.deterministic_scores != prov.hybrid_aggregation.semantic_scores


def test_benchmark_run_semantic_mock_writes_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALWM_FIXTURE_MODE", "1")
    dfn = BenchmarkDefinitionV1.model_validate(
        {
            "schema_version": 1,
            "id": "bench.sem.mock.v1",
            "title": "semantic mock",
            "rubric_ref": "fixtures/v1/rubric.json",
            "prompts": [{"id": "p1", "text": "Say hi."}],
            "variants": [
                {
                    "id": "v1",
                    "agent_stack": "alwm-cli",
                    "execution_mode": "cli",
                    "backend": {"kind": "mock", "model": "mock-model"},
                },
            ],
            "eval_scoring": {
                "backend": "semantic_judge",
                "judge_repeats": 2,
                "semantic_aggregation": "median",
            },
        },
    )
    out = tmp_path / "run"
    run_benchmark(
        dfn,
        repo_root=_REPO,
        output_dir=out,
        created_at="1970-01-01T00:00:00Z",
        run_id="sem2",
        provider_yaml=None,
        environ={"ALWM_FIXTURE_MODE": "1"},
        fixture_mode_force_mock=True,
    )
    cell = next((out / "cells").iterdir())
    load_artifact_file(cell / "evaluation.json", "evaluation")
    load_artifact_file(cell / "evaluation_judge_provenance.json", "evaluation_judge_provenance")


def test_live_judge_path_invokes_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    rubric_path = _REPO / "fixtures" / "v1" / "rubric.json"
    cfg = load_judge_provider_config(
        yaml_path=None,
        environ={"ALWM_FIXTURE_MODE": "1"},
        judge_live=True,
    )
    with patch(
        "agent_llm_wiki_matrix.pipelines.evaluation_backends.create_provider",
    ) as m:
        from agent_llm_wiki_matrix.providers.mock import MockProvider

        m.return_value = MockProvider()
        evaluate_with_scoring_backend(
            subject_ref="s",
            text="t",
            rubric_path=rubric_path,
            evaluation_id="e3",
            evaluated_at="1970-01-01T00:00:00Z",
            scoring_backend="semantic_judge",
            hybrid_weights=None,
            judge_provider_cfg=cfg,
            judge_live=True,
            evaluation_json_relpath="e.json",
        )
        m.assert_called_once()
