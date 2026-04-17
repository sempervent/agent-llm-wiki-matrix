"""Offline-first ingest → evaluate → compare → report pipelines."""

from agent_llm_wiki_matrix.pipelines.compare import evaluations_to_matrix
from agent_llm_wiki_matrix.pipelines.evaluate import evaluate_subject
from agent_llm_wiki_matrix.pipelines.ingest import ingest_markdown_pages
from agent_llm_wiki_matrix.pipelines.reporting import (
    build_report_from_matrix,
    render_matrix_markdown,
    render_report_markdown,
)

__all__ = [
    "build_report_from_matrix",
    "evaluate_subject",
    "evaluations_to_matrix",
    "ingest_markdown_pages",
    "render_matrix_markdown",
    "render_report_markdown",
]
