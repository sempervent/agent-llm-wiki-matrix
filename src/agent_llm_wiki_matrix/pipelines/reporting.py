"""Render Markdown reports from structured matrix and report artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from agent_llm_wiki_matrix.models import ComparisonMatrix, Report

ReportKind = Literal["weekly", "model_comparison", "agent_stack", "browser_evidence"]


def _read_template(name: str) -> str:
    root = Path(__file__).resolve().parents[3]
    path = root / "templates" / name
    return path.read_text(encoding="utf-8")


def render_matrix_markdown(matrix: ComparisonMatrix) -> str:
    """Fill ``templates/matrix.md`` placeholders."""
    tpl = _read_template("matrix.md")
    rows = " | ".join(matrix.row_labels)
    cols = " | ".join(matrix.col_labels)
    table_lines = [
        "| | " + " | ".join(matrix.col_labels) + " |",
        "| --- | " + " | ".join(["---"] * len(matrix.col_labels)) + " |",
    ]
    for i, row_label in enumerate(matrix.row_labels):
        cells = " | ".join(str(x) for x in matrix.scores[i])
        table_lines.append(f"| {row_label} | {cells} |")
    scores_table = "\n".join(table_lines)
    return (
        tpl.replace("TITLE", matrix.title)
        .replace("ID", matrix.id)
        .replace("MATRIX_KIND", matrix.matrix_kind)
        .replace("METRIC", matrix.metric)
        .replace("CREATED_AT", matrix.created_at)
        .replace("ROW_LABELS", rows)
        .replace("COL_LABELS", cols)
        .replace("SCORES_TABLE", scores_table)
    )


def build_report_from_matrix(
    matrix: ComparisonMatrix,
    *,
    report_id: str,
    period_start: str,
    period_end: str,
    kind: ReportKind = "model_comparison",
) -> Report:
    """Create a Report artifact summarizing the matrix (Markdown body)."""
    md_body_lines = [
        f"## {matrix.title}",
        "",
        f"- **metric:** `{matrix.metric}`",
        f"- **shape:** {len(matrix.row_labels)}×{len(matrix.col_labels)} ({matrix.matrix_kind})",
        "",
        "### Highlights",
        "",
        "- See the companion matrix Markdown for the full score grid.",
        "",
    ]
    source_refs = ["matrices/grid.json", "markdown/matrix.grid.md"]
    return Report(
        id=report_id,
        title=f"Report: {matrix.title}",
        kind=kind,
        period_start=period_start,
        period_end=period_end,
        body_markdown="\n".join(md_body_lines),
        source_refs=source_refs,
    )


def render_report_markdown(report: Report) -> str:
    """Fill ``templates/report.md`` placeholders."""
    tpl = _read_template("report.md")
    refs = "\n".join(f"- `{r}`" for r in report.source_refs) if report.source_refs else "_none_"
    return (
        tpl.replace("TITLE", report.title)
        .replace("ID", report.id)
        .replace("REPORT_KIND", report.kind)
        .replace("PERIOD_START", report.period_start)
        .replace("PERIOD_END", report.period_end)
        .replace("BODY_MARKDOWN", report.body_markdown)
        .replace("SOURCE_REFS", refs)
    )
