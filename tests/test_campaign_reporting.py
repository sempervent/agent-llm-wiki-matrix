"""Campaign comparative reporting (aggregates member runs)."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_llm_wiki_matrix.benchmark.campaign_reporting import (
    aggregate_backend_performance,
    summarize_campaign_dimensions,
    write_campaign_comparative_artifacts,
)
from agent_llm_wiki_matrix.models import (
    BenchmarkCampaignManifest,
    BenchmarkCampaignRunEntry,
)

_REPO = Path(__file__).resolve().parents[1]


def test_summarize_dimensions_single_run_not_varied() -> None:
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
                suite_ref="fixtures/benchmarks/campaign_micro.v1.yaml",
                benchmark_id="bench.x",
                eval_scoring_label="suite_default",
                browser_config_applied=False,
                output_relpath="runs/run0000",
                manifest_relpath="runs/run0000/manifest.json",
                cell_count=1,
                status="succeeded",
                provider_config_ref=None,
                execution_modes_filter=None,
            ),
        ],
    )
    dim = summarize_campaign_dimensions(m)
    assert dim["suite_ref"]["varied"] is False
    assert dim["eval_scoring_label"]["distinct_count"] == 1


def test_aggregate_backend_single_kind() -> None:
    from datetime import UTC, datetime

    from agent_llm_wiki_matrix.pipelines.longitudinal import CellSnapshot, RunSnapshot

    dt = datetime(1970, 1, 1, tzinfo=UTC)
    snap = RunSnapshot(
        run_root=Path("/r"),
        run_relpath="runs/run0000",
        manifest_path="m.json",
        run_id="r1",
        benchmark_id="b",
        title="t",
        created_at=dt,
        created_at_raw="1970-01-01T00:00:00Z",
        cells=(
            CellSnapshot(
                cell_id="a",
                variant_id="v",
                prompt_id="p",
                execution_mode="cli",
                agent_stack="s",
                backend_kind="mock",
                backend_model="m",
                total_score=0.8,
                criterion_scores={},
                scoring_backend="deterministic",
                eval_relpath="e.json",
            ),
        ),
        grid=None,
    )
    rows = aggregate_backend_performance([snap])
    assert len(rows) == 1
    assert rows[0].backend_kind == "mock"
    assert rows[0].mean_score == pytest.approx(0.8)


def test_write_comparative_artifacts_skips_dry_run(tmp_path: Path) -> None:
    m = BenchmarkCampaignManifest(
        schema_version=1,
        campaign_id="c",
        title="t",
        created_at="1970-01-01T00:00:00Z",
        definition_source_relpath="x.yaml",
        fixture_mode_force_mock=True,
        dry_run=True,
        runs=[],
    )
    assert write_campaign_comparative_artifacts(_REPO, tmp_path, m) is None


def test_campaign_run_writes_comparative_report(tmp_path: Path) -> None:
    from agent_llm_wiki_matrix.benchmark.campaign_definitions import (
        load_benchmark_campaign_definition,
    )
    from agent_llm_wiki_matrix.benchmark.campaign_runner import run_benchmark_campaign

    campaign_path = _REPO / "examples/campaigns/v1/minimal_offline.v1.yaml"
    campaign = load_benchmark_campaign_definition(campaign_path)
    out = tmp_path / "camp"
    run_benchmark_campaign(
        repo_root=_REPO,
        campaign=campaign,
        campaign_definition_path=campaign_path,
        output_dir=out,
        created_at="2026-04-17T00:00:00Z",
        fixture_mode_force_mock=True,
    )
    assert (out / "reports" / "campaign-report.md").is_file()
    assert (out / "reports" / "campaign-analysis.json").is_file()
    raw = (out / "manifest.json").read_text(encoding="utf-8")
    assert "campaign-report.md" in raw
    assert "campaign-analysis.json" in raw
