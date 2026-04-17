"""Build comparison matrices from benchmark evaluation scores."""

from __future__ import annotations

from agent_llm_wiki_matrix.models import ComparisonMatrix


def grid_matrix_from_scores(
    *,
    matrix_id: str,
    title: str,
    row_labels: list[str],
    col_labels: list[str],
    scores: dict[tuple[str, str], float],
    metric: str,
    created_at: str,
) -> ComparisonMatrix:
    """Grid: rows = variants, columns = prompts; cell = total weighted score."""
    grid: list[list[float]] = []
    for r in row_labels:
        row_scores: list[float] = []
        for c in col_labels:
            row_scores.append(float(scores.get((r, c), 0.0)))
        grid.append(row_scores)
    return ComparisonMatrix(
        id=matrix_id,
        title=title,
        matrix_kind="grid",
        row_labels=row_labels,
        col_labels=col_labels,
        scores=grid,
        metric=metric,
        created_at=created_at,
    )


def pairwise_mean_delta_matrix(
    *,
    matrix_id: str,
    title: str,
    variant_ids: list[str],
    prompt_ids: list[str],
    scores: dict[tuple[str, str], float],
    metric: str,
    created_at: str,
) -> ComparisonMatrix:
    """Pairwise: mean absolute difference in total scores across prompts for each variant pair."""
    n = len(variant_ids)
    mat: list[list[float]] = []
    for i in range(n):
        row: list[float] = []
        for j in range(n):
            if i == j:
                row.append(0.0)
            else:
                vi, vj = variant_ids[i], variant_ids[j]
                deltas = [
                    abs(float(scores[(vi, p)]) - float(scores[(vj, p)])) for p in prompt_ids
                ]
                row.append(sum(deltas) / len(deltas) if deltas else 0.0)
        mat.append(row)
    return ComparisonMatrix(
        id=matrix_id,
        title=title,
        matrix_kind="pairwise",
        row_labels=variant_ids,
        col_labels=variant_ids,
        scores=mat,
        metric=metric,
        created_at=created_at,
    )
