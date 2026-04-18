"""Rubric scoring backends: deterministic (default), semantic LLM judge, and hybrid blend."""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from agent_llm_wiki_matrix.artifacts import load_artifact_file
from agent_llm_wiki_matrix.benchmark.definitions import EvalHybridWeights
from agent_llm_wiki_matrix.models import (
    Evaluation,
    EvaluationJudgeProvenance,
    JudgeCriterionDisagreement,
    JudgeDisagreementSummary,
    JudgeHybridAggregation,
    JudgeProviderInfo,
    JudgeRepeatAggregation,
    JudgeRepeatConfidence,
    JudgeRepeatRunRecord,
    Rubric,
)
from agent_llm_wiki_matrix.pipelines.evaluate import _evaluate_text_core
from agent_llm_wiki_matrix.pipelines.judge_repeat import (
    SemanticAggregationStrategy,
    aggregate_criterion_scores,
    assess_low_confidence,
    build_disagreement_summary,
)
from agent_llm_wiki_matrix.providers.base import CompletionRequest
from agent_llm_wiki_matrix.providers.config import ProviderConfig
from agent_llm_wiki_matrix.providers.factory import create_provider

ScoringBackendName = Literal["deterministic", "semantic_judge", "hybrid"]


@dataclass
class JudgeRepeatParams:
    """Parameters for repeated semantic judge calls (N≥1)."""

    count: int = 1
    strategy: SemanticAggregationStrategy = "mean"
    trim_fraction: float = 0.1
    max_criterion_range: float | None = None
    max_criterion_stdev: float | None = None
    max_mean_criterion_stdev: float | None = None
    max_total_weighted_stdev: float | None = None

    def __post_init__(self) -> None:
        if self.count < 1 or self.count > 32:
            msg = "judge repeat count must be in [1, 32]"
            raise ValueError(msg)
        if not 0.0 <= self.trim_fraction <= 0.45:
            msg = "trim_fraction must be in [0, 0.45]"
            raise ValueError(msg)


def _provider_model_label(cfg: ProviderConfig) -> str:
    if cfg.kind == "ollama":
        return cfg.ollama.model
    if cfg.kind == "openai_compatible":
        return cfg.openai_compatible.model
    return "mock-model"


JUDGE_SYSTEM_PROMPT = (
    "You are an expert rubric judge. Score the RESPONSE against each criterion in the RUBRIC.\n"
    "Rules:\n"
    "- Output ONLY valid JSON (no markdown fences, no commentary outside JSON).\n"
    '- JSON shape: {"scores": {<criterion_id>: <0..1>, ...}, '
    '"rationale": "<short string>"}\n'
    "- Include every criterion id exactly once. Scores must be floats in [0, 1].\n"
)


def _weighted_total(scores: dict[str, float], weights: dict[str, float]) -> float:
    weight_sum = sum(weights.values())
    if weight_sum <= 0:
        msg = "Rubric weights must sum to a positive value"
        raise ValueError(msg)
    return round(sum(weights[k] * scores[k] for k in scores) / weight_sum, 6)


def _score_byte_hash(text: str, criterion_id: str) -> float:
    digest = hashlib.sha256(f"{criterion_id}\n{text}".encode()).digest()
    return int.from_bytes(digest[:4], "big") / 2**32


def _mock_semantic_scores(text: str, rubric: Rubric, *, run_index: int = 0) -> dict[str, float]:
    """Deterministic stand-in for LLM scores when provider is mock (CI-safe).

    ``run_index`` varies scores across repeated runs so disagreement metrics are testable.
    """
    scores: dict[str, float] = {}
    for c in rubric.criteria:
        digest = hashlib.sha256(
            f"semantic::{c.id}\n{text}\nrun:{run_index}".encode(),
        ).digest()
        scores[c.id] = round(int.from_bytes(digest[:4], "big") / 2**32, 6)
    return scores


def build_judge_user_prompt(*, rubric: Rubric, response_text: str) -> str:
    criteria = [
        {"id": c.id, "weight": c.weight, "description": c.description} for c in rubric.criteria
    ]
    payload = {
        "rubric_id": rubric.id,
        "rubric_title": rubric.title,
        "criteria": criteria,
        "response_text": response_text,
    }
    return (
        "RUBRIC (JSON):\n"
        + json.dumps(payload, indent=2, sort_keys=True)
        + "\n\nRESPONSE TO SCORE:\n"
        + response_text
    )


def parse_judge_json(raw: str) -> tuple[dict[str, float], str | None]:
    """Extract scores map from model output; return (scores, error_message)."""
    text = raw.strip()
    m = re.search(r"\{[\s\S]*\}\s*$", text)
    if m:
        text = m.group(0)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return {}, f"invalid JSON: {e}"
    if not isinstance(data, dict):
        return {}, "top-level JSON must be an object"
    scores_obj = data.get("scores")
    if not isinstance(scores_obj, dict):
        return {}, "missing scores object"
    out: dict[str, float] = {}
    for k, v in scores_obj.items():
        if not isinstance(k, str):
            return {}, f"non-string criterion key: {k!r}"
        try:
            fv = float(v)
        except (TypeError, ValueError):
            return {}, f"non-numeric score for {k!r}"
        if fv < 0 or fv > 1:
            return {}, f"score for {k!r} out of [0,1]"
        out[k] = fv
    return out, None


def _run_semantic_with_repeats(
    *,
    rubric: Rubric,
    text: str,
    provider_cfg: ProviderConfig,
    judge_live: bool,
    repeat: JudgeRepeatParams,
) -> tuple[
    dict[str, float],
    list[JudgeRepeatRunRecord],
    JudgeRepeatAggregation | None,
    str,
    bool,
    str | None,
    bool | None,
]:
    """Execute N semantic judge runs; aggregate scores and optional repeat block.

    Returns:
        aggregated_scores, run_records, repeat_aggregation (None if N==1),
        raw_concat, all_parse_ok, combined_parse_error, low_confidence (None if N==1).
    """
    criterion_ids = [c.id for c in rubric.criteria]
    run_records: list[JudgeRepeatRunRecord] = []
    score_rows: list[dict[str, float]] = []
    parse_notes: list[str] = []
    all_ok = True

    for i in range(repeat.count):
        raw, scores, ok, perr = run_semantic_judge_once(
            rubric=rubric,
            response_text=text,
            provider_cfg=provider_cfg,
            judge_live=judge_live,
            run_index=i,
        )
        if not ok:
            scores = _mock_semantic_scores(text, rubric, run_index=i)
            raw = json.dumps(
                {"scores": scores, "rationale": "fallback after parse failure"},
                indent=2,
                sort_keys=True,
            )
            perr = (perr or "") + "; fallback to mock_semantic_scores"
        run_records.append(
            JudgeRepeatRunRecord(
                run_index=i,
                raw_response_text=raw,
                parsed_criterion_scores=dict(scores),
                parse_ok=ok,
                parse_error=perr,
            ),
        )
        score_rows.append(dict(scores))
        if not ok:
            all_ok = False
        if perr:
            parse_notes.append(f"run {i}: {perr}")

    agg = aggregate_criterion_scores(
        score_rows,
        criterion_ids,
        repeat.strategy,
        repeat.trim_fraction,
    )
    raw_concat = (
        run_records[0].raw_response_text
        if len(run_records) == 1
        else "\n\n--- alwm semantic judge run ---\n\n".join(
            r.raw_response_text for r in run_records
        )
    )
    combined_err = "; ".join(parse_notes) if parse_notes else None

    if repeat.count == 1:
        return agg, run_records, None, raw_concat, all_ok, combined_err, None

    rubric_weights = {c.id: float(c.weight) for c in rubric.criteria}
    disc = build_disagreement_summary(score_rows, criterion_ids, weights=rubric_weights)
    per_models = {
        cid: JudgeCriterionDisagreement(
            min=row["min"],
            max=row["max"],
            score_range=row["score_range"],
            stdev=row["stdev"],
        )
        for cid, row in cast(dict[str, dict[str, float]], disc["per_criterion"]).items()
    }
    low, flags = assess_low_confidence(
        per_criterion_range=cast(dict[str, dict[str, float]], disc["per_criterion"]),
        mean_stdev_across_criteria=float(disc["mean_stdev_across_criteria"]),
        total_weighted_stdev=float(disc["total_weighted_stdev"]),
        max_range_across_criteria=float(disc["max_range_across_criteria"]),
        max_criterion_range=repeat.max_criterion_range,
        max_criterion_stdev=repeat.max_criterion_stdev,
        max_mean_criterion_stdev=repeat.max_mean_criterion_stdev,
        max_total_weighted_stdev=repeat.max_total_weighted_stdev,
    )
    repeat_block = JudgeRepeatAggregation(
        repeat_count=repeat.count,
        strategy=repeat.strategy,
        trim_fraction=repeat.trim_fraction,
        runs=run_records,
        aggregated_semantic_scores=agg,
        disagreement=JudgeDisagreementSummary(
            per_criterion=per_models,
            mean_stdev_across_criteria=float(disc["mean_stdev_across_criteria"]),
            total_weighted_per_run=list(cast(list[float], disc["total_weighted_per_run"])),
            total_weighted_stdev=float(disc["total_weighted_stdev"]),
            max_range_across_criteria=float(disc["max_range_across_criteria"]),
        ),
        confidence=JudgeRepeatConfidence(
            low_confidence=low,
            flags=flags,
            thresholds={
                "max_criterion_range": repeat.max_criterion_range,
                "max_criterion_stdev": repeat.max_criterion_stdev,
                "max_mean_criterion_stdev": repeat.max_mean_criterion_stdev,
                "max_total_weighted_stdev": repeat.max_total_weighted_stdev,
            },
        ),
    )
    return agg, run_records, repeat_block, raw_concat, all_ok, combined_err, low


def run_semantic_judge_once(
    *,
    rubric: Rubric,
    response_text: str,
    provider_cfg: ProviderConfig,
    judge_live: bool,
    run_index: int = 0,
) -> tuple[str, dict[str, float], bool, str | None]:
    """Return (raw_response, scores, parse_ok, parse_error)."""
    user_prompt = build_judge_user_prompt(rubric=rubric, response_text=response_text)
    provider = create_provider(provider_cfg)

    if provider_cfg.kind == "mock" and not judge_live:
        scores = _mock_semantic_scores(response_text, rubric, run_index=run_index)
        raw = json.dumps(
            {"scores": scores, "rationale": "mock-semantic (deterministic hash; no network)"},
            indent=2,
            sort_keys=True,
        )
        return raw, scores, True, None

    req = CompletionRequest(
        prompt=f"{JUDGE_SYSTEM_PROMPT}\n\n{user_prompt}",
        model=_provider_model_label(provider_cfg),
    )
    raw = provider.complete(req)
    scores, err = parse_judge_json(raw)
    ok = err is None and set(scores.keys()) == {c.id for c in rubric.criteria}
    if err is None and not ok:
        missing = {c.id for c in rubric.criteria} - set(scores.keys())
        extra = set(scores.keys()) - {c.id for c in rubric.criteria}
        err = f"criterion mismatch missing={missing!r} extra={extra!r}"
    return raw, scores, err is None and ok, err


def evaluate_with_scoring_backend(
    *,
    subject_ref: str,
    text: str,
    rubric_path: Path,
    evaluation_id: str,
    evaluated_at: str,
    scoring_backend: ScoringBackendName,
    hybrid_weights: EvalHybridWeights | None,
    judge_provider_cfg: ProviderConfig | None,
    judge_live: bool,
    evaluation_json_relpath: str,
    judge_repeat: JudgeRepeatParams | None = None,
) -> tuple[Evaluation, EvaluationJudgeProvenance | None]:
    """Dispatch to deterministic, semantic_judge, or hybrid scoring."""
    rubric_model = load_artifact_file(rubric_path, "rubric")
    if not isinstance(rubric_model, Rubric):
        msg = "Expected a Rubric artifact"
        raise TypeError(msg)

    weights = {c.id: float(c.weight) for c in rubric_model.criteria}

    if scoring_backend == "deterministic":
        ev = _evaluate_text_core(
            subject_ref=subject_ref,
            text=text,
            rubric_model=rubric_model,
            evaluation_id=evaluation_id,
            evaluated_at=evaluated_at,
            evaluator="pipeline",
            notes_markdown="Deterministic pipeline evaluation (byte-hash scores).",
        )
        ev2 = ev.model_copy(
            update={"scoring_backend": "deterministic", "judge_provenance_relpath": None},
        )
        return ev2, None

    if judge_provider_cfg is None:
        msg = "semantic_judge and hybrid require judge_provider_cfg"
        raise ValueError(msg)
    pinfo = JudgeProviderInfo(
        kind=cast(
            Literal["mock", "ollama", "openai_compatible"],
            judge_provider_cfg.kind,
        ),
        model=_provider_model_label(judge_provider_cfg),
    )

    if scoring_backend == "semantic_judge":
        repeat = judge_repeat or JudgeRepeatParams()
        sem_scores, _, repeat_block, raw, all_ok, perr, low_conf = _run_semantic_with_repeats(
            rubric=rubric_model,
            text=text,
            provider_cfg=judge_provider_cfg,
            judge_live=judge_live,
            repeat=repeat,
        )
        total = _weighted_total(sem_scores, weights)
        notes = "Semantic judge scoring (see evaluation_judge_provenance.json)."
        if perr:
            notes += f" Parse note: {perr}"
        if repeat.count > 1 and low_conf:
            notes += " Low confidence: repeated semantic runs exceeded disagreement thresholds."
        ev = Evaluation(
            id=evaluation_id,
            subject_ref=subject_ref,
            rubric_id=rubric_model.id,
            scores=sem_scores,
            weights=weights,
            total_weighted_score=total,
            evaluated_at=evaluated_at,
            evaluator="agent",
            notes_markdown=notes,
            scoring_backend="semantic_judge",
            judge_provenance_relpath=None,
            judge_repeat_count=repeat.count if repeat.count > 1 else None,
            judge_semantic_aggregation=repeat.strategy if repeat.count > 1 else None,
            judge_low_confidence=low_conf if repeat.count > 1 else None,
        )
        prov = EvaluationJudgeProvenance(
            schema_version=1,
            evaluation_id=evaluation_id,
            evaluation_ref=evaluation_json_relpath,
            subject_ref=subject_ref,
            rubric_id=rubric_model.id,
            scoring_backend="semantic_judge",
            judge_system_prompt=JUDGE_SYSTEM_PROMPT,
            judge_user_prompt=build_judge_user_prompt(rubric=rubric_model, response_text=text),
            provider=pinfo,
            raw_response_text=raw,
            parsed_criterion_scores=sem_scores,
            parse_ok=all_ok,
            parse_error=perr,
            hybrid_aggregation=None,
            aggregation_notes=None,
            repeat_aggregation=repeat_block,
        )
        return ev, prov

    # hybrid
    if hybrid_weights is None:
        msg = "hybrid scoring requires hybrid_weights"
        raise ValueError(msg)
    repeat = judge_repeat or JudgeRepeatParams()
    det_ev = _evaluate_text_core(
        subject_ref=subject_ref,
        text=text,
        rubric_model=rubric_model,
        evaluation_id=evaluation_id,
        evaluated_at=evaluated_at,
        evaluator="pipeline",
        notes_markdown="Deterministic component for hybrid scoring.",
    )
    det_scores = dict(det_ev.scores)
    sem_scores, _, repeat_block, raw, all_ok, perr, low_conf = _run_semantic_with_repeats(
        rubric=rubric_model,
        text=text,
        provider_cfg=judge_provider_cfg,
        judge_live=judge_live,
        repeat=repeat,
    )
    wd = hybrid_weights.deterministic_weight
    ws = hybrid_weights.semantic_weight
    blended: dict[str, float] = {}
    for c in rubric_model.criteria:
        blended[c.id] = round(wd * det_scores[c.id] + ws * sem_scores[c.id], 6)
    total = _weighted_total(blended, weights)
    notes = (
        f"Hybrid scoring: {wd:g} deterministic + {ws:g} semantic per criterion "
        "(see evaluation_judge_provenance.json)."
    )
    if repeat.count > 1 and low_conf:
        notes += " Low confidence: repeated semantic runs exceeded disagreement thresholds."
    ev = Evaluation(
        id=evaluation_id,
        subject_ref=subject_ref,
        rubric_id=rubric_model.id,
        scores=blended,
        weights=weights,
        total_weighted_score=total,
        evaluated_at=evaluated_at,
        evaluator="agent",
        notes_markdown=notes,
        scoring_backend="hybrid",
        judge_provenance_relpath=None,
        judge_repeat_count=repeat.count if repeat.count > 1 else None,
        judge_semantic_aggregation=repeat.strategy if repeat.count > 1 else None,
        judge_low_confidence=low_conf if repeat.count > 1 else None,
    )
    hybrid_meta = JudgeHybridAggregation(
        deterministic_weight=wd,
        semantic_weight=ws,
        deterministic_scores=det_scores,
        semantic_scores=sem_scores,
        semantic_repeat_count=repeat.count,
    )
    agg_notes = f"final_scores[c] = {wd:g}*det[c] + {ws:g}*sem[c]"
    if repeat.count > 1:
        trim_note = ""
        if repeat.strategy == "trimmed_mean":
            trim_note = f" (trim_fraction={repeat.trim_fraction:g})"
        agg_notes += (
            f"; semantic aggregated across {repeat.count} runs via {repeat.strategy}{trim_note}"
        )
    prov = EvaluationJudgeProvenance(
        schema_version=1,
        evaluation_id=evaluation_id,
        evaluation_ref=evaluation_json_relpath,
        subject_ref=subject_ref,
        rubric_id=rubric_model.id,
        scoring_backend="hybrid",
        judge_system_prompt=JUDGE_SYSTEM_PROMPT,
        judge_user_prompt=build_judge_user_prompt(rubric=rubric_model, response_text=text),
        provider=pinfo,
        raw_response_text=raw,
        parsed_criterion_scores=sem_scores,
        parse_ok=all_ok,
        parse_error=perr,
        hybrid_aggregation=hybrid_meta,
        aggregation_notes=agg_notes,
        repeat_aggregation=repeat_block,
    )
    return ev, prov


def judge_live_enabled(environ: Mapping[str, str] | None) -> bool:
    """Opt-in live judge: ALWM_JUDGE_LIVE=1."""
    env: Mapping[str, str] = environ if environ is not None else os.environ
    return env.get("ALWM_JUDGE_LIVE", "").strip() in {"1", "true", "yes"}
