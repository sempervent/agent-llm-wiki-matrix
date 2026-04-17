"""Build comparison matrices from evaluation artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from agent_llm_wiki_matrix.artifacts import load_artifact_file
from agent_llm_wiki_matrix.models import ComparisonMatrix, Evaluation


def evaluations_to_matrix(
    evaluation_paths: list[Path],
    *,
    matrix_id: str,
    title: str,
    metric: str,
    created_at: str,
    matrix_kind: Literal["pairwise", "grid"] = "grid",
) -> ComparisonMatrix:
    """Lay out one row per evaluation file; columns are sorted score keys."""
    if not evaluation_paths:
        msg = "At least one evaluation path is required"
        raise ValueError(msg)
    evaluations: list[Evaluation] = []
    for p in evaluation_paths:
        model = load_artifact_file(p, "evaluation")
        if not isinstance(model, Evaluation):
            msg = "Expected an Evaluation artifact"
            raise TypeError(msg)
        evaluations.append(model)

    col_keys: set[str] = set()
    for ev in evaluations:
        col_keys |= set(ev.scores.keys())

    col_labels = sorted(col_keys)
    row_labels: list[str] = []
    scores: list[list[float]] = []

    for ev in evaluations:
        ref = Path(ev.subject_ref)
        label = ref.stem if ref.suffix else ref.name
        row_labels.append(label or ev.id)
        row_scores = [float(ev.scores.get(c, 0.0)) for c in col_labels]
        scores.append(row_scores)

    return ComparisonMatrix(
        id=matrix_id,
        title=title,
        matrix_kind=matrix_kind,
        row_labels=row_labels,
        col_labels=col_labels,
        scores=scores,
        metric=metric,
        created_at=created_at,
    )
