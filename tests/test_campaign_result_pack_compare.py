"""Compare two campaign result pack directories."""

from __future__ import annotations

import json
from pathlib import Path

from agent_llm_wiki_matrix.artifacts import load_artifact_file
from agent_llm_wiki_matrix.benchmark.campaign_result_pack_compare import (
    build_campaign_result_pack_comparison,
    compare_campaign_result_packs_cli,
    render_campaign_result_pack_compare_markdown,
    write_campaign_result_pack_compare_artifacts,
)

_REPO = Path(__file__).resolve().parents[1]
_MINIMAL_PACK = _REPO / "examples" / "campaign_result_packs" / "minimal_offline"
_MULTI_PACK = _REPO / "examples" / "campaign_result_packs" / "multi_suite"


def test_compare_same_pack_identity_match() -> None:
    data = build_campaign_result_pack_comparison(
        _MINIMAL_PACK,
        _MINIMAL_PACK,
        left_label="a",
        right_label="b",
        repo_root=_REPO,
    )
    assert data["identity"]["same_campaign_id"] is True
    assert data["identity"]["pack_identity_fingerprint"]["match"] is True
    assert data["identity"]["campaign_definition_fingerprint"]["match"] is True
    assert data["member_runs"]["left_count"] == data["member_runs"]["right_count"]
    ri = data["reader_interpretation"]
    assert ri["schema_version"] == 1
    assert ri["comparison_kind"] == "pack"
    assert ri["evidence_strength"] in {"weak", "moderate"}
    md = render_campaign_result_pack_compare_markdown(data)
    assert md.startswith("# Campaign result pack comparison")
    assert "## At a glance" in md
    assert "## Member run overlap" in md
    assert "## Analysis deltas" in md
    assert "Non-causal" in md
    assert "right − left" in md
    assert "pack_identity_fingerprint" in md


def test_compare_minimal_vs_multi_different_campaign_ids() -> None:
    data = build_campaign_result_pack_comparison(
        _MINIMAL_PACK,
        _MULTI_PACK,
        repo_root=_REPO,
    )
    assert data["identity"]["same_campaign_id"] is False
    assert data["identity"]["pack_identity_fingerprint"]["match"] is False
    assert data["member_runs"]["left_count"] == 1
    assert data["member_runs"]["right_count"] == 2
    assert data["member_runs"]["run_ids_only_in_right"]

    bec = data["comparative_analysis"]["browser_evidence_comparison"]
    assert bec["left_row_count"] == 0
    assert bec["right_row_count"] >= 1
    assert bec["aggregate"]["right_total_dom_excerpts"] >= 1
    assert any(r.get("pairing") == "right_only" for r in bec["paired_rows"])
    md = render_campaign_result_pack_compare_markdown(data)
    assert "## At a glance" in md
    assert data["reader_interpretation"]["comparison_kind"] == "pack"
    assert "### Browser evidence (`browser_evidence_member_cells`)" in md
    assert "With movement" in md
    assert "right only" in md


def test_write_compare_validates_kind(tmp_path: Path) -> None:
    data = build_campaign_result_pack_comparison(
        _MINIMAL_PACK,
        _MINIMAL_PACK,
        repo_root=_REPO,
    )
    write_campaign_result_pack_compare_artifacts(tmp_path, data)
    load_artifact_file(tmp_path / "pack-compare.json", "campaign_result_pack_comparison")
    assert (tmp_path / "pack-compare-report.md").read_text(encoding="utf-8")


def test_compare_packs_cli_writes_files(tmp_path: Path) -> None:
    out = tmp_path / "cmp"
    jp, mp = compare_campaign_result_packs_cli(
        _MINIMAL_PACK,
        _MULTI_PACK,
        output_dir=out,
        left_label="L",
        right_label="R",
        repo_root=_REPO,
    )
    assert jp.is_file() and mp.is_file()
    raw = json.loads(jp.read_text(encoding="utf-8"))
    assert raw["schema_version"] == 1
    assert raw["left"]["label"] == "L"
