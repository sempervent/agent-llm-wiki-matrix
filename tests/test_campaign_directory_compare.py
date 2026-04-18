"""Campaign directory vs directory comparison (campaign-compare.json)."""

from __future__ import annotations

from pathlib import Path

from agent_llm_wiki_matrix.artifacts import load_artifact_file
from agent_llm_wiki_matrix.benchmark.campaign_directory_compare import (
    build_campaign_directory_comparison,
    load_campaign_directory_side,
    render_campaign_compare_markdown,
    write_campaign_compare_artifacts,
)

_REPO = Path(__file__).resolve().parents[1]
_MIN = _REPO / "examples" / "campaign_runs" / "minimal_offline"
_MULTI = _REPO / "examples" / "campaign_runs" / "multi_suite"


def test_build_compare_minimal_vs_multi(tmp_path: Path) -> None:
    data = build_campaign_directory_comparison(
        _MIN,
        _MULTI,
        left_label="minimal",
        right_label="multi",
        created_at="1970-01-01T00:00:00Z",
    )
    assert data["schema_version"] == 1
    assert data["identity"]["same_campaign_id"] is False
    assert data["sweep_dimensions"]["per_axis"]
    ri = data["reader_interpretation"]
    assert ri["schema_version"] == 1
    assert ri["comparison_kind"] == "campaign_directory"
    assert ri["evidence_strength"] in {"weak", "moderate"}
    bec = data["comparative_analysis"]["browser_evidence_comparison"]
    assert bec["right_row_count"] >= 1
    assert bec["aggregate"]["delta_dom_excerpts_right_minus_left"] >= 1
    md = render_campaign_compare_markdown(data)
    assert md.startswith("# Campaign directory comparison")
    assert "## Reader interpretation" in md
    assert "right − left" in md
    assert "## Browser evidence (`browser_evidence_member_cells`)" in md
    assert "local MCP" in md
    jp, mp = write_campaign_compare_artifacts(tmp_path, data)
    assert jp.is_file() and mp.is_file()
    load_artifact_file(jp, "campaign_compare")


def test_load_campaign_side_roundtrip() -> None:
    s = load_campaign_directory_side(_MIN, label="m")
    assert s.manifest.campaign_id
    assert s.manifest.runs


def test_cli_compare_smoke(tmp_path: Path) -> None:
    from click.testing import CliRunner

    from agent_llm_wiki_matrix.cli import main

    out = tmp_path / "cmp"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "benchmark",
            "campaign",
            "compare",
            str(_MIN),
            str(_MULTI),
            "-o",
            str(out),
            "--created-at",
            "1970-01-01T00:00:00Z",
        ],
    )
    assert result.exit_code == 0, result.output
    load_artifact_file(out / "campaign-compare.json", "campaign_compare")
