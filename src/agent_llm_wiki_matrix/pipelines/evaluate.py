"""Deterministic rubric evaluation (no live network)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

from agent_llm_wiki_matrix.artifacts import load_artifact_file
from agent_llm_wiki_matrix.models import Evaluation, Rubric, Thought


def _score_byte_hash(text: str, criterion_id: str) -> float:
    """Map (text, criterion) to a stable score in ``[0, 1]``."""
    digest = hashlib.sha256(f"{criterion_id}\n{text}".encode()).digest()
    return int.from_bytes(digest[:4], "big") / 2**32


def _load_subject_text(path: Path) -> tuple[str, str]:
    """Return ``(subject_ref, text)`` for a Markdown file or Thought JSON."""
    suffix = path.suffix.lower()
    if suffix == ".json":
        model = load_artifact_file(path, "thought")
        if not isinstance(model, Thought):
            msg = "Expected a Thought artifact"
            raise TypeError(msg)
        subject_ref = str(path.as_posix())
        return subject_ref, model.body_markdown
    if suffix in {".md", ".markdown"}:
        return str(path.as_posix()), path.read_text(encoding="utf-8")
    msg = f"Unsupported subject type: {path}"
    raise ValueError(msg)


def evaluate_subject(
    subject_path: Path,
    rubric_path: Path,
    *,
    evaluation_id: str,
    evaluated_at: str,
    evaluator: Literal["human", "agent", "pipeline"] = "pipeline",
) -> Evaluation:
    """Score ``subject_path`` against ``rubric_path`` using deterministic hashes."""
    rubric_model = load_artifact_file(rubric_path, "rubric")
    if not isinstance(rubric_model, Rubric):
        msg = "Expected a Rubric artifact"
        raise TypeError(msg)
    subject_ref, text = _load_subject_text(subject_path)

    scores: dict[str, float] = {}
    weights: dict[str, float] = {}
    for c in rubric_model.criteria:
        scores[c.id] = round(_score_byte_hash(text, c.id), 6)
        weights[c.id] = float(c.weight)

    weight_sum = sum(weights.values())
    if weight_sum <= 0:
        msg = "Rubric weights must sum to a positive value"
        raise ValueError(msg)
    total = sum(weights[k] * scores[k] for k in scores) / weight_sum

    return Evaluation(
        id=evaluation_id,
        subject_ref=subject_ref,
        rubric_id=rubric_model.id,
        scores=scores,
        weights=weights,
        total_weighted_score=round(total, 6),
        evaluated_at=evaluated_at,
        evaluator=evaluator,
        notes_markdown="Deterministic pipeline evaluation (byte-hash scores).",
    )


def evaluation_to_json(evaluation: Evaluation) -> str:
    """Serialize evaluation for stable file output."""
    return json.dumps(evaluation.model_dump(exclude_none=True), indent=2, sort_keys=True) + "\n"
