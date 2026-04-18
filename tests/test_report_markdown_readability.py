"""Markdown report shape: redundancy rules and readable headings (no scoring changes)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from agent_llm_wiki_matrix.benchmark.campaign_reporting import (
    render_campaign_comparative_markdown,
    render_comparative_executive_markdown,
    suite_ref_benchmark_id_partition_coincide,
)
from agent_llm_wiki_matrix.benchmark.campaign_semantic_summary import (
    render_campaign_semantic_summary_markdown,
)
from agent_llm_wiki_matrix.models import (
    BenchmarkCampaignManifest,
    BenchmarkCampaignRunEntry,
    CampaignSemanticInstabilityHighlights,
    CampaignSemanticSummaryV1,
    CampaignSemanticTotals,
)
from agent_llm_wiki_matrix.pipelines.longitudinal import (
    CellSnapshot,
    RunSnapshot,
    analyze_longitudinal,
)


def _snap(
    rid: str,
    bid: str,
    score: float = 0.7,
    scoring_backend: str = "deterministic",
) -> RunSnapshot:
    dt = datetime(1970, 1, 1, tzinfo=UTC)
    return RunSnapshot(
        run_root=Path(f"/r/{rid}"),
        run_relpath=f"runs/{rid}",
        manifest_path=f"runs/{rid}/m.json",
        run_id=rid,
        benchmark_id=bid,
        title="t",
        created_at=dt,
        created_at_raw="1970-01-01T00:00:00Z",
        cells=(
            CellSnapshot(
                cell_id="c1",
                variant_id="v",
                prompt_id="p",
                execution_mode="cli",
                agent_stack="s",
                backend_kind="mock",
                backend_model="m",
                total_score=score,
                criterion_scores={},
                scoring_backend=scoring_backend,
                eval_relpath="e.json",
            ),
        ),
        grid=None,
    )


def test_suite_benchmark_coincide_when_sweep_together() -> None:
    m = BenchmarkCampaignManifest(
        schema_version=1,
        campaign_id="c",
        title="t",
        created_at="1970-01-01T00:00:00Z",
        definition_source_relpath="x.yaml",
        fixture_mode_force_mock=True,
        dry_run=False,
        runs=[
            BenchmarkCampaignRunEntry(
                run_index=0,
                run_id="c__0000",
                suite_ref="a.yaml",
                benchmark_id="b1",
                eval_scoring_label="suite_default",
                browser_config_applied=False,
                output_relpath="runs/run0000",
                manifest_relpath="runs/run0000/manifest.json",
                cell_count=1,
                status="succeeded",
                mean_total_weighted_score=0.9,
                provider_config_ref=None,
                execution_modes_filter=None,
            ),
            BenchmarkCampaignRunEntry(
                run_index=1,
                run_id="c__0001",
                suite_ref="b.yaml",
                benchmark_id="b2",
                eval_scoring_label="suite_default",
                browser_config_applied=False,
                output_relpath="runs/run0001",
                manifest_relpath="runs/run0001/manifest.json",
                cell_count=1,
                status="succeeded",
                mean_total_weighted_score=0.4,
                provider_config_ref=None,
                execution_modes_filter=None,
            ),
        ],
    )
    assert suite_ref_benchmark_id_partition_coincide(m) is True


def test_suite_benchmark_not_coincide_when_benchmark_splits_suite() -> None:
    m = BenchmarkCampaignManifest(
        schema_version=1,
        campaign_id="c",
        title="t",
        created_at="1970-01-01T00:00:00Z",
        definition_source_relpath="x.yaml",
        fixture_mode_force_mock=True,
        dry_run=False,
        runs=[
            BenchmarkCampaignRunEntry(
                run_index=0,
                run_id="c__0000",
                suite_ref="same.yaml",
                benchmark_id="b1",
                eval_scoring_label="suite_default",
                browser_config_applied=False,
                output_relpath="runs/run0000",
                manifest_relpath="runs/run0000/manifest.json",
                cell_count=1,
                status="succeeded",
                mean_total_weighted_score=0.9,
                provider_config_ref=None,
                execution_modes_filter=None,
            ),
            BenchmarkCampaignRunEntry(
                run_index=1,
                run_id="c__0001",
                suite_ref="same.yaml",
                benchmark_id="b2",
                eval_scoring_label="suite_default",
                browser_config_applied=False,
                output_relpath="runs/run0001",
                manifest_relpath="runs/run0001/manifest.json",
                cell_count=1,
                status="succeeded",
                mean_total_weighted_score=0.4,
                provider_config_ref=None,
                execution_modes_filter=None,
            ),
        ],
    )
    assert suite_ref_benchmark_id_partition_coincide(m) is False


def test_executive_markdown_omits_redundant_benchmark_axis_line() -> None:
    m = BenchmarkCampaignManifest(
        schema_version=1,
        campaign_id="c",
        title="t",
        created_at="1970-01-01T00:00:00Z",
        definition_source_relpath="x.yaml",
        fixture_mode_force_mock=True,
        dry_run=False,
        runs=[
            BenchmarkCampaignRunEntry(
                run_index=0,
                run_id="c__0000",
                suite_ref="a.yaml",
                benchmark_id="b1",
                eval_scoring_label="suite_default",
                browser_config_applied=False,
                output_relpath="runs/run0000",
                manifest_relpath="runs/run0000/manifest.json",
                cell_count=1,
                status="succeeded",
                mean_total_weighted_score=0.9,
                provider_config_ref=None,
                execution_modes_filter=None,
            ),
            BenchmarkCampaignRunEntry(
                run_index=1,
                run_id="c__0001",
                suite_ref="b.yaml",
                benchmark_id="b2",
                eval_scoring_label="suite_default",
                browser_config_applied=False,
                output_relpath="runs/run0001",
                manifest_relpath="runs/run0001/manifest.json",
                cell_count=1,
                status="succeeded",
                mean_total_weighted_score=0.4,
                provider_config_ref=None,
                execution_modes_filter=None,
            ),
        ],
    )
    snaps = [_snap("c__0000", "b1"), _snap("c__0001", "b2")]
    analysis = analyze_longitudinal(
        snaps,
        regression_delta=0.03,
        low_score=0.55,
        min_recurring=2,
        mode_gap_threshold=0.12,
    )
    md = render_comparative_executive_markdown(m, snaps, analysis)
    assert "`suite_ref`" in md
    assert "**`benchmark_id`:** best" not in md
    assert "`suite_ref` and `benchmark_id` sweep together" in md


def test_comparative_report_dimensions_table_pairs_suite_benchmark() -> None:
    m = BenchmarkCampaignManifest(
        schema_version=1,
        campaign_id="c",
        title="t",
        created_at="1970-01-01T00:00:00Z",
        definition_source_relpath="x.yaml",
        fixture_mode_force_mock=True,
        dry_run=False,
        runs=[
            BenchmarkCampaignRunEntry(
                run_index=0,
                run_id="c__0000",
                suite_ref="a.yaml",
                benchmark_id="b1",
                eval_scoring_label="suite_default",
                browser_config_applied=False,
                output_relpath="runs/run0000",
                manifest_relpath="runs/run0000/manifest.json",
                cell_count=1,
                status="succeeded",
                mean_total_weighted_score=0.9,
                provider_config_ref=None,
                execution_modes_filter=None,
            ),
            BenchmarkCampaignRunEntry(
                run_index=1,
                run_id="c__0001",
                suite_ref="b.yaml",
                benchmark_id="b2",
                eval_scoring_label="suite_default",
                browser_config_applied=False,
                output_relpath="runs/run0001",
                manifest_relpath="runs/run0001/manifest.json",
                cell_count=1,
                status="succeeded",
                mean_total_weighted_score=0.4,
                provider_config_ref=None,
                execution_modes_filter=None,
            ),
        ],
    )
    snaps = [_snap("c__0000", "b1"), _snap("c__0001", "b2")]
    analysis = analyze_longitudinal(
        snaps,
        regression_delta=0.03,
        low_score=0.55,
        min_recurring=2,
        mode_gap_threshold=0.12,
    )
    full = render_campaign_comparative_markdown(m, snaps, analysis, semantic_summary=None)
    assert "suite_ref (paired with benchmark_id)" in full
    dim_section = full.split("## Which dimensions varied")[1].split("## Member-run mean")[0]
    assert "| `benchmark_id` |" not in dim_section


def test_semantic_summary_markdown_snapshot_shape() -> None:
    summary = CampaignSemanticSummaryV1(
        schema_version=1,
        campaign_id="camp",
        title="T",
        created_at="1970-01-01T00:00:00Z",
        totals=CampaignSemanticTotals(
            runs_scanned=1,
            cells_total=2,
            cells_deterministic=1,
            cells_semantic_or_hybrid=1,
            cells_with_repeat_judge=0,
            low_confidence_cells=0,
            cells_flagged_judge_low_confidence=0,
            cells_flagged_repeat_confidence_low=0,
            max_range_across_campaign=None,
            mean_range_repeat_cells=None,
            mean_total_weighted_stdev_repeat=None,
        ),
        by_suite=[],
        by_provider=[],
        by_execution_mode=[],
        criterion_instability=[],
        instability_highlights=CampaignSemanticInstabilityHighlights(),
        cells=[],
    )
    md = render_campaign_semantic_summary_markdown(summary)
    assert md.startswith("# Judge variance — `camp`")
    assert "## Snapshot" in md
    assert "## Instability hotspots" in md
    assert "## Totals" not in md
    assert "| Runs scanned | 1 |" in md
