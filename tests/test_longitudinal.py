"""Tests for longitudinal / weekly analysis from benchmark manifests."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_llm_wiki_matrix.pipelines.longitudinal import (
    analysis_to_summary_dict,
    analyze_longitudinal,
    discover_manifest_paths,
    group_snapshots_by,
    load_run_snapshot,
    load_run_snapshots,
    render_failure_atlas,
    render_failure_taxonomy_reference,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_discover_manifest_paths_fixture_pair() -> None:
    repo = _repo_root()
    paths = discover_manifest_paths(repo, "fixtures/longitudinal/paired/*/manifest.json")
    assert len(paths) == 2
    assert all(p.name == "manifest.json" for p in paths)


def test_load_run_snapshots_orders_by_created_at() -> None:
    repo = _repo_root()
    paths = discover_manifest_paths(repo, "fixtures/longitudinal/paired/*/manifest.json")
    snaps = load_run_snapshots(repo, paths)
    assert [s.run_id for s in snaps] == ["longitudinal-w02", "longitudinal-w03"]


def test_analyze_fixture_pair_regression() -> None:
    repo = _repo_root()
    paths = discover_manifest_paths(repo, "fixtures/longitudinal/paired/*/manifest.json")
    snaps = load_run_snapshots(repo, paths)
    analysis = analyze_longitudinal(
        snaps,
        regression_delta=0.03,
        low_score=0.55,
        min_recurring=2,
        mode_gap_threshold=0.12,
    )
    assert len(analysis.regressions) == 1
    r = analysis.regressions[0]
    assert r.benchmark_id == "bench.fixtures.longitudinal.v1"
    assert r.cell_id == "v-cli__p-one"
    assert r.delta == pytest.approx(-0.12)
    assert len(analysis.criterion_drops) == 4
    assert "FT-RUN-REG" in analysis.failure_tags
    tags = analysis.failure_tags["FT-RUN-REG"]
    needle = "bench.fixtures.longitudinal.v1::v-cli__p-one"
    assert any(needle in t for t in tags)


def test_analyze_no_regression_above_threshold() -> None:
    repo = _repo_root()
    paths = discover_manifest_paths(repo, "fixtures/longitudinal/paired/*/manifest.json")
    snaps = load_run_snapshots(repo, paths)
    analysis = analyze_longitudinal(
        snaps,
        regression_delta=0.20,
        low_score=0.55,
        min_recurring=2,
        mode_gap_threshold=0.12,
    )
    assert analysis.regressions == []


def test_render_failure_atlas_and_taxonomy() -> None:
    repo = _repo_root()
    paths = discover_manifest_paths(repo, "fixtures/longitudinal/paired/*/manifest.json")
    snaps = load_run_snapshots(repo, paths)
    analysis = analyze_longitudinal(
        snaps,
        regression_delta=0.03,
        low_score=0.55,
        min_recurring=2,
        mode_gap_threshold=0.12,
    )
    atlas = render_failure_atlas(analysis)
    assert "# Failure atlas" in atlas
    assert "FT-RUN-REG" in atlas
    ref = render_failure_taxonomy_reference()
    assert "FT-ABS-LOW" in ref
    assert "| `FT-RUN-REG` |" in ref


def test_group_snapshots_by_task_family() -> None:
    repo = _repo_root()
    paths = discover_manifest_paths(repo, "fixtures/longitudinal/paired/*/manifest.json")
    snaps = load_run_snapshots(repo, paths)
    grouped = group_snapshots_by(snaps, "task_family")
    assert grouped["documentation"] == snaps


def test_group_snapshots_by_suite_definition_fingerprint() -> None:
    repo = _repo_root()
    paths = discover_manifest_paths(repo, "fixtures/longitudinal/paired/*/manifest.json")
    snaps = load_run_snapshots(repo, paths)
    grouped = group_snapshots_by(snaps, "suite_definition_fingerprint")
    assert len(grouped) == 1
    assert len(next(iter(grouped.values()))) == 2


def test_group_snapshots_by_prompt_registry_state_fingerprint() -> None:
    repo = _repo_root()
    paths = discover_manifest_paths(repo, "fixtures/longitudinal/paired/*/manifest.json")
    snaps = load_run_snapshots(repo, paths)
    grouped = group_snapshots_by(snaps, "prompt_registry_state_fingerprint")
    assert len(grouped) == 1
    k = next(iter(grouped.keys()))
    assert k.startswith("sha256:")


def test_group_snapshots_by_git_ref() -> None:
    repo = _repo_root()
    paths = discover_manifest_paths(repo, "fixtures/longitudinal/paired/*/manifest.json")
    snaps = load_run_snapshots(repo, paths)
    by_ref = group_snapshots_by(snaps, "git_ref")
    assert len(by_ref["fixture-abc123"]) == 1
    assert len(by_ref["fixture-def456"]) == 1


def test_load_run_snapshot_relative_paths(tmp_path: Path) -> None:
    """Manifest outside repo_root still loads when paths resolve."""
    repo = tmp_path / "repo"
    run = repo / "run_a"
    cell = run / "cells" / "v-cli__p-one"
    cell.mkdir(parents=True)
    (run / "manifest.json").write_text(
        """{
  "benchmark_id": "b.x",
  "cells": [{
    "aggregate_response_relpath": "cells/v-cli__p-one/benchmark_response.json",
    "cell_id": "v-cli__p-one",
    "evaluation_relpath": "cells/v-cli__p-one/evaluation.json",
    "normalized_response_relpath": "cells/v-cli__p-one/r.txt",
    "raw_response_relpath": "cells/v-cli__p-one/r2.txt",
    "request_relpath": "cells/v-cli__p-one/request.json"
  }],
  "created_at": "2026-01-01T00:00:00Z",
  "matrix_grid_md_path": "m.md",
  "matrix_grid_path": "g.json",
  "matrix_grid_row_inputs_path": "gri.json",
  "matrix_pairwise_md_path": "p.md",
  "matrix_pairwise_path": "p.json",
  "matrix_pairwise_row_inputs_path": "pri.json",
  "prompt_ids": ["p-one"],
  "report_json_path": "reports/report.json",
  "report_md_path": "reports/report.md",
  "rubric_ref": "r.json",
  "run_id": "r1",
  "schema_version": 1,
  "title": "t",
  "variant_ids": ["v-cli"]
}
""",
        encoding="utf-8",
    )
    (cell / "evaluation.json").write_text(
        """{
  "evaluated_at": "2026-01-01T00:00:00Z",
  "evaluator": "pipeline",
  "id": "e1",
  "rubric_id": "rub",
  "scores": {"a": 0.5},
  "weights": {"a": 1.0},
  "total_weighted_score": 0.5,
  "scoring_backend": "deterministic",
  "subject_ref": "cells/v-cli__p-one/benchmark_response.json",
  "judge_provenance_relpath": null
}
""",
        encoding="utf-8",
    )
    (cell / "benchmark_response.json").write_text(
        """{
  "schema_version": 1,
  "id": "br1",
  "benchmark_id": "b.x",
  "variant_id": "v-cli",
  "prompt_id": "p-one",
  "agent_stack": "s",
  "execution_mode": "cli",
  "backend_kind": "mock",
  "backend_model": "m",
  "prompt_text": "p",
  "response_text": "r",
  "created_at": "2026-01-01T00:00:00Z",
  "prompt_source": "inline"
}
""",
        encoding="utf-8",
    )
    snap = load_run_snapshot(repo, run / "manifest.json")
    assert snap.run_id == "r1"
    assert len(snap.cells) == 1
    assert snap.cells[0].total_score == pytest.approx(0.5)


def test_analysis_summary_includes_fingerprint_axis_interpretation() -> None:
    repo = _repo_root()
    paths = discover_manifest_paths(repo, "fixtures/longitudinal/paired/*/manifest.json")
    snaps = load_run_snapshots(repo, paths)
    analysis = analyze_longitudinal(
        snaps,
        regression_delta=0.03,
        low_score=0.55,
        min_recurring=2,
        mode_gap_threshold=0.12,
    )
    d = analysis_to_summary_dict(analysis)
    fi = d["fingerprint_axis_interpretation"]
    assert fi["schema_version"] == 1
    assert "differentiation_overview" in fi
    assert "attribution_by_axis" in fi
