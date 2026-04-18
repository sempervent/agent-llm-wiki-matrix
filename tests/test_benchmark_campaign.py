"""Benchmark campaign sweep orchestration."""

from __future__ import annotations

from pathlib import Path

from agent_llm_wiki_matrix.artifacts import load_artifact_file
from agent_llm_wiki_matrix.benchmark.campaign_definitions import load_benchmark_campaign_definition
from agent_llm_wiki_matrix.benchmark.campaign_runner import run_benchmark_campaign

_REPO = Path(__file__).resolve().parents[1]


def test_load_minimal_campaign_definition() -> None:
    path = _REPO / "examples/campaigns/v1/minimal_offline.v1.yaml"
    c = load_benchmark_campaign_definition(path)
    assert c.id == "campaign.examples.minimal_offline.v1"
    assert c.suite_refs == ["fixtures/benchmarks/campaign_micro.v1.yaml"]
    assert len(c.provider_config_refs) == 1
    assert c.provider_config_refs[0] is None


def test_campaign_definition_artifact_kind() -> None:
    path = _REPO / "examples/campaigns/v1/minimal_offline.v1.yaml"
    raw = path.read_text(encoding="utf-8")
    import yaml

    data = yaml.safe_load(raw)
    from agent_llm_wiki_matrix.artifacts import parse_artifact

    parse_artifact("campaign_definition", data)


def test_campaign_run_writes_longitudinal_compatible_tree(tmp_path: Path) -> None:
    campaign_path = _REPO / "examples/campaigns/v1/minimal_offline.v1.yaml"
    campaign = load_benchmark_campaign_definition(campaign_path)
    out = tmp_path / "campaign_out"
    manifest = run_benchmark_campaign(
        repo_root=_REPO,
        campaign=campaign,
        campaign_definition_path=campaign_path,
        output_dir=out,
        created_at="2026-04-17T00:00:00Z",
        fixture_mode_force_mock=True,
    )
    assert len(manifest.runs) == 1
    assert (out / "manifest.json").is_file()
    assert (out / "campaign-summary.md").is_file()
    assert (out / "campaign-summary.json").is_file()
    run0 = out / "runs" / "run0000"
    assert (run0 / "manifest.json").is_file()
    load_artifact_file(run0 / "manifest.json", "benchmark_manifest")
    cm = load_artifact_file(out / "manifest.json", "benchmark_campaign_manifest")
    assert cm.campaign_id == campaign.id
    assert len(cm.runs) == 1
    assert cm.runs[0].mean_total_weighted_score is not None
    assert cm.runs[0].comparison_fingerprints is not None
    assert cm.runs[0].comparison_fingerprints.suite_definition.startswith("sha256:")
    fp = cm.campaign_definition_fingerprint
    assert fp and fp.startswith("sha256:")
    assert cm.campaign_experiment_fingerprints is not None
    assert cm.campaign_experiment_fingerprints.campaign_definition == fp
    assert cm.runs[0].comparison_fingerprints is not None
    assert cm.runs[0].comparison_fingerprints.prompt_registry_state.startswith("sha256:")
    assert cm.run_status_summary is not None
    assert cm.run_status_summary.succeeded == 1
    load_artifact_file(out / "campaign-summary.json", "campaign_summary")
    assert "## At a glance" in (out / "campaign-summary.md").read_text(encoding="utf-8")
    assert (out / "campaign-semantic-summary.json").is_file()
    assert (out / "campaign-semantic-summary.md").is_file()
    assert (
        cm.generated_report_paths.campaign_semantic_summary_json == "campaign-semantic-summary.json"
    )
    assert cm.generated_report_paths.campaign_comparative_report_md == "reports/campaign-report.md"
    assert cm.generated_report_paths.campaign_analysis_json == "reports/campaign-analysis.json"
    report_md = (out / "reports" / "campaign-report.md").read_text(encoding="utf-8")
    assert "## At a glance" in report_md
    assert "Fingerprint axes (longitudinal grouping keys)" in report_md
    assert (out / "reports" / "campaign-analysis.json").is_file()
    sem = load_artifact_file(out / "campaign-semantic-summary.json", "campaign_semantic_summary")
    assert sem.totals.cells_total >= 1
    assert sem.totals.cells_semantic_or_hybrid == 0
    assert sem.totals.cells_deterministic >= 1


def test_campaign_semantic_repeats_offline_rollups(tmp_path: Path) -> None:
    campaign_path = _REPO / "examples/campaigns/v1/semantic_repeats_offline.v1.yaml"
    campaign = load_benchmark_campaign_definition(campaign_path)
    out = tmp_path / "campaign_sem"
    manifest = run_benchmark_campaign(
        repo_root=_REPO,
        campaign=campaign,
        campaign_definition_path=campaign_path,
        output_dir=out,
        created_at="2026-04-17T00:00:00Z",
        fixture_mode_force_mock=True,
    )
    assert len(manifest.runs) == 1
    sem_md = (out / "campaign-semantic-summary.md").read_text(encoding="utf-8")
    assert "## Instability hotspots" in sem_md
    sem = load_artifact_file(out / "campaign-semantic-summary.json", "campaign_semantic_summary")
    assert sem.totals.runs_scanned == 1
    assert sem.totals.cells_semantic_or_hybrid >= 1
    assert sem.totals.cells_with_repeat_judge >= 1
    assert len(sem.by_suite) >= 1
    assert len(sem.by_execution_mode) >= 1
    suite_axis = {a.axis_value: a for a in sem.by_suite}
    assert "examples/benchmarks/v1/semantic_repeats.v1.yaml" in suite_axis
    assert suite_axis["examples/benchmarks/v1/semantic_repeats.v1.yaml"].repeat_judge_cells >= 1


def test_multi_suite_campaign_at_a_glance_compare_suites(tmp_path: Path) -> None:
    campaign_path = _REPO / "examples/campaigns/v1/multi_suite.v1.yaml"
    campaign = load_benchmark_campaign_definition(campaign_path)
    out = tmp_path / "multi"
    run_benchmark_campaign(
        repo_root=_REPO,
        campaign=campaign,
        campaign_definition_path=campaign_path,
        output_dir=out,
        created_at="2026-04-17T00:00:00Z",
        fixture_mode_force_mock=True,
    )
    summary_md = (out / "campaign-summary.md").read_text(encoding="utf-8")
    assert "## At a glance" in summary_md
    assert "suite_ref" in summary_md
    assert "Mean score — best / worst by sweep axis" in summary_md


def test_campaign_dry_run_writes_plan_without_member_runs(tmp_path: Path) -> None:
    campaign_path = _REPO / "examples/campaigns/v1/minimal_offline.v1.yaml"
    campaign = load_benchmark_campaign_definition(campaign_path)
    out = tmp_path / "dry"
    manifest = run_benchmark_campaign(
        repo_root=_REPO,
        campaign=campaign,
        campaign_definition_path=campaign_path,
        output_dir=out,
        created_at="2026-04-17T00:00:00Z",
        environ={},
        fixture_mode_force_mock=True,
        dry_run=True,
    )
    assert manifest.dry_run is True
    assert manifest.run_count == 1
    assert not (out / "runs").exists()
    assert (out / "campaign-dry-run.json").is_file()
    load_artifact_file(out / "manifest.json", "campaign_manifest")
    load_artifact_file(out / "campaign-summary.json", "campaign_summary")
