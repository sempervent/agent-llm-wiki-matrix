"""End-to-end pipeline tests (deterministic; no network)."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from agent_llm_wiki_matrix.artifacts import load_artifact_file
from agent_llm_wiki_matrix.cli import main
from agent_llm_wiki_matrix.models import ComparisonMatrix, Evaluation
from agent_llm_wiki_matrix.pipelines.compare import evaluations_to_matrix
from agent_llm_wiki_matrix.pipelines.evaluate import evaluate_subject
from agent_llm_wiki_matrix.pipelines.ingest import ingest_markdown_pages
from agent_llm_wiki_matrix.pipelines.reporting import (
    build_report_from_matrix,
    render_matrix_markdown,
)

_REPO = Path(__file__).resolve().parents[1]


def test_ingest_writes_thoughts(tmp_path: Path) -> None:
    src = tmp_path / "pages"
    src.mkdir()
    (src / "a.md").write_text("# Title A\n\nbody\n", encoding="utf-8")
    out = tmp_path / "thoughts"
    written = ingest_markdown_pages(src, out, created_at="1970-01-01T00:00:00Z")
    assert len(written) == 1
    t = load_artifact_file(written[0], "thought")
    assert t.title == "Title A"


def test_evaluate_is_deterministic(tmp_path: Path) -> None:
    rubric = _REPO / "fixtures" / "v1" / "rubric.json"
    subj = tmp_path / "p.md"
    subj.write_text("hello world", encoding="utf-8")
    a = evaluate_subject(
        subj,
        rubric,
        evaluation_id="e1",
        evaluated_at="1970-01-01T00:00:00Z",
    )
    b = evaluate_subject(
        subj,
        rubric,
        evaluation_id="e1",
        evaluated_at="1970-01-01T00:00:00Z",
    )
    assert a.scores == b.scores
    assert a.total_weighted_score == b.total_weighted_score


def test_compare_builds_matrix(tmp_path: Path) -> None:
    rubric = _REPO / "fixtures" / "v1" / "rubric.json"
    s1 = tmp_path / "one.md"
    s2 = tmp_path / "two.md"
    s1.write_text("aaa", encoding="utf-8")
    s2.write_text("bbb", encoding="utf-8")
    e1 = evaluate_subject(s1, rubric, evaluation_id="e1", evaluated_at="1970-01-01T00:00:00Z")
    e2 = evaluate_subject(s2, rubric, evaluation_id="e2", evaluated_at="1970-01-01T00:00:00Z")
    p1 = tmp_path / "e1.json"
    p2 = tmp_path / "e2.json"
    p1.write_text(e1.model_dump_json(), encoding="utf-8")
    p2.write_text(e2.model_dump_json(), encoding="utf-8")
    m = evaluations_to_matrix(
        [p1, p2],
        matrix_id="m",
        title="t",
        metric="m",
        created_at="1970-01-01T00:00:00Z",
    )
    assert len(m.row_labels) == 2
    assert "clarity" in m.col_labels


def test_report_renders_from_matrix() -> None:
    m = ComparisonMatrix(
        id="mid",
        title="mt",
        matrix_kind="grid",
        row_labels=["a"],
        col_labels=["c"],
        scores=[[0.5]],
        metric="x",
        created_at="1970-01-01T00:00:00Z",
    )
    r = build_report_from_matrix(
        m,
        report_id="rid",
        period_start="1970-01-01",
        period_end="1970-01-07",
    )
    assert "mt" in r.body_markdown
    md = render_matrix_markdown(m)
    assert "0.5" in md


def test_pipeline_cli(tmp_path: Path) -> None:
    rubric = _REPO / "fixtures" / "v1" / "rubric.json"
    page = tmp_path / "page.md"
    page.write_text("# Hi\n", encoding="utf-8")
    ev_out = tmp_path / "e.json"
    runner = CliRunner()
    r = runner.invoke(
        main,
        [
            "evaluate",
            "--subject",
            str(page),
            "--rubric",
            str(rubric),
            "--out",
            str(ev_out),
            "--id",
            "cli-eval",
        ],
    )
    assert r.exit_code == 0, r.output
    ev = load_artifact_file(ev_out, "evaluation")
    assert isinstance(ev, Evaluation)


@pytest.mark.parametrize(
    ("path", "kind"),
    [
        ("examples/generated/wiki_matrix.json", "matrix"),
        ("examples/generated/wiki_report.json", "report"),
    ],
)
def test_example_generated_validates(path: str, kind: str) -> None:
    load_artifact_file(_REPO / path, kind)
