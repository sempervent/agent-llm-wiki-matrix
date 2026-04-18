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
