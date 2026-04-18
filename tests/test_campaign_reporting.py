"""Campaign comparative reporting (aggregates member runs)."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_llm_wiki_matrix.benchmark.campaign_fingerprint_compare import (
    FINGERPRINT_COMPARE_AXES,
    build_fingerprint_axis_groups,
    build_fingerprint_axis_insights,
    build_fingerprint_axis_interpretation,
    render_fingerprint_axis_interpretation_markdown,
)
from agent_llm_wiki_matrix.benchmark.campaign_reporting import (
    aggregate_backend_performance,
    build_campaign_analysis_dict,
    mean_score_extremes_by_sweep_axis,
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


def test_fingerprint_compare_axes_cover_requested_keys() -> None:
    keys = {k for k, _ in FINGERPRINT_COMPARE_AXES}
    assert "provider_config_fingerprint" in keys
    assert "scoring_config_fingerprint" in keys
    assert "execution_mode" in keys
    assert "prompt_registry_state_fingerprint" in keys
    assert "browser_config_fingerprint" in keys


def test_build_fingerprint_groups_matches_group_snapshots_by() -> None:
    from datetime import UTC, datetime

    from agent_llm_wiki_matrix.models import BenchmarkComparisonFingerprints
    from agent_llm_wiki_matrix.pipelines.longitudinal import (
        CellSnapshot,
        RunSnapshot,
        analyze_longitudinal,
        group_snapshots_by,
    )

    dt = datetime(1970, 1, 1, tzinfo=UTC)
    fp_a = BenchmarkComparisonFingerprints(
        suite_definition="sha256:" + "a" * 64,
        prompt_set="sha256:" + "b" * 64,
        provider_config="sha256:" + "p" * 64,
        scoring_config="sha256:" + "s" * 64,
        browser_config="sha256:" + "w" * 64,
        prompt_registry_state="sha256:" + "r" * 64,
    )
    fp_b = fp_a.model_copy(update={"provider_config": "sha256:" + "q" * 64})

    def _snap(rid: str, fp: BenchmarkComparisonFingerprints) -> RunSnapshot:
        return RunSnapshot(
            run_root=Path(f"/r/{rid}"),
            run_relpath=f"runs/{rid}",
            manifest_path=f"runs/{rid}/m.json",
            run_id=rid,
            benchmark_id="b",
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
                    total_score=0.5,
                    criterion_scores={},
                    scoring_backend="deterministic",
                    eval_relpath="e.json",
                ),
            ),
            grid=None,
            comparison_fingerprints=fp,
        )

    snaps = [_snap("run-a", fp_a), _snap("run-b", fp_b)]
    analysis = analyze_longitudinal(
        snaps,
        regression_delta=0.03,
        low_score=0.1,
        min_recurring=2,
        mode_gap_threshold=0.5,
    )
    buckets = group_snapshots_by(snaps, "provider_config_fingerprint")
    assert len(buckets) == 2
    rows = build_fingerprint_axis_groups(snaps, analysis)
    prov_rows = [r for r in rows if r.axis_key == "provider_config_fingerprint"]
    assert len(prov_rows) == 2
    insights = build_fingerprint_axis_insights(snaps, analysis)
    prov_ins = next(i for i in insights if i["axis_key"] == "provider_config_fingerprint")
    assert prov_ins["varied"] is True
    assert prov_ins["pooled_mean_score_spread"] == 0.0
    interp = build_fingerprint_axis_interpretation(snaps, analysis, insights)
    assert interp["schema_version"] == 1
    assert "score_spread_ranking" in interp
    assert "instability_hotspots" in interp
    assert "drift_correlation_hints" in interp
    attr_pf = next(
        a for a in interp["attribution_by_axis"] if a["axis_key"] == "provider_config_fingerprint"
    )
    assert "evidence_strength" in attr_pf
    assert "uncertainty_notes" in attr_pf
    assert "attribution_label" in attr_pf
    assert attr_pf["metrics"].get("min_bucket_cell_count") is not None
    rank_pf = next(
        r
        for r in interp["score_spread_ranking"]
        if r["axis_key"] == "provider_config_fingerprint"
    )
    assert rank_pf["pooled_mean_score_spread"] == 0.0
    md = render_fingerprint_axis_interpretation_markdown(interp)
    assert "| Pattern |" in md
    assert "Limit:_" in md or "weak" in md.lower()


def test_build_campaign_analysis_includes_fingerprint_blocks() -> None:
    from datetime import UTC, datetime

    from agent_llm_wiki_matrix.pipelines.longitudinal import (
        CellSnapshot,
        RunSnapshot,
        analyze_longitudinal,
    )

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
    analysis = analyze_longitudinal(
        [snap],
        regression_delta=0.03,
        low_score=0.55,
        min_recurring=2,
        mode_gap_threshold=0.12,
    )
    m = BenchmarkCampaignManifest(
        schema_version=1,
        campaign_id="c",
        title="t",
        created_at="1970-01-01T00:00:00Z",
        definition_source_relpath="x.yaml",
        fixture_mode_force_mock=True,
        dry_run=False,
        runs=[],
    )
    d = build_campaign_analysis_dict(m, [snap], analysis)
    assert "fingerprint_compare_axes" in d
    assert "fingerprint_axis_insights" in d
    assert "fingerprint_axis_interpretation" in d
    fi = d["fingerprint_axis_interpretation"]
    assert fi["schema_version"] == 1
    assert "attribution_by_axis" in fi
    assert "differentiation_overview" in fi
    assert "interpretation_caveats" in fi
    assert len(d["fingerprint_compare_axes"]) >= 5
    assert "mean_score_extremes_by_sweep_axis" in d
    assert "member_mean_score_by_dimension" in d


def test_mean_score_extremes_two_runs_varied_suite() -> None:
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
    ext = mean_score_extremes_by_sweep_axis(m)
    assert ext["comparable"] is True
    sf = ext["axes"]["suite_ref"]
    assert sf["varied"] is True
    assert sf["best"]["label"] == "a.yaml"
    assert sf["worst"]["label"] == "b.yaml"


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
    paths, bundle = write_campaign_comparative_artifacts(_REPO, tmp_path, m)
    assert paths is None
    assert bundle is None


def test_fingerprint_axes_probe_campaign_two_scoring_config_buckets(tmp_path: Path) -> None:
    import json

    from agent_llm_wiki_matrix.benchmark.campaign_definitions import (
        load_benchmark_campaign_definition,
    )
    from agent_llm_wiki_matrix.benchmark.campaign_runner import run_benchmark_campaign

    campaign_path = _REPO / "examples/campaigns/v1/fingerprint_axes_probe.v1.yaml"
    campaign = load_benchmark_campaign_definition(campaign_path)
    out = tmp_path / "probe"
    run_benchmark_campaign(
        repo_root=_REPO,
        campaign=campaign,
        campaign_definition_path=campaign_path,
        output_dir=out,
        created_at="2026-04-17T00:00:00Z",
        fixture_mode_force_mock=True,
    )
    data = json.loads((out / "reports" / "campaign-analysis.json").read_text(encoding="utf-8"))
    assert "fingerprint_compare_axes" in data
    sc = [
        x
        for x in data["fingerprint_compare_axes"]
        if x["axis_key"] == "scoring_config_fingerprint"
    ]
    assert len(sc) == 2
    sc_ins = next(
        i
        for i in data["fingerprint_axis_insights"]
        if i["axis_key"] == "scoring_config_fingerprint"
    )
    assert sc_ins["varied"] is True
    assert "fingerprint_axis_interpretation" in data
    assert data["fingerprint_axis_interpretation"]["schema_version"] == 1
    cr = (out / "reports" / "campaign-report.md").read_text(encoding="utf-8")
    assert "Fingerprint axes (longitudinal grouping keys)" in cr
    assert "Axis interpretation (why buckets differ)" in cr
    assert "Per-axis attribution (heuristic)" in cr


def test_campaign_run_writes_comparative_report(tmp_path: Path) -> None:
    import json

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
    report_md = (out / "reports" / "campaign-report.md").read_text(encoding="utf-8")
    assert "## At a glance" in report_md
    analysis_path = out / "reports" / "campaign-analysis.json"
    assert analysis_path.is_file()
    analysis_json = json.loads(analysis_path.read_text(encoding="utf-8"))
    assert "member_mean_score_by_dimension" in analysis_json
    raw = (out / "manifest.json").read_text(encoding="utf-8")
    assert "campaign-report.md" in raw
    assert "campaign-analysis.json" in raw
