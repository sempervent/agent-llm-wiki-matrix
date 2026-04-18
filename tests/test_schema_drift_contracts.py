"""Deterministic schema ↔ Pydantic drift checks for committed trees.

Scans ``examples/`` and ``fixtures/`` (including emitted campaign outputs under
``examples/campaign_runs/`` and ``examples/campaign_result_packs/``) and validates
JSON files against registered ``alwm`` kinds (JSON Schema + Pydantic via
``load_artifact_file``).

Canonical host command: ``just validate-artifacts`` (or ``uv run pytest`` on this module).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_llm_wiki_matrix.artifacts import load_artifact_file

_REPO = Path(__file__).resolve().parents[1]
_SCAN_ROOTS = (_REPO / "examples", _REPO / "fixtures")


def _classify_manifest(path: Path) -> str | None:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        return None
    if "campaign_id" in data and "runs" in data and "benchmark_id" not in data:
        return "benchmark_campaign_manifest"
    if "benchmark_id" in data and "cells" in data:
        return "benchmark_manifest"
    return None


def collect_committed_artifact_drift_errors() -> list[str]:
    """Return human-readable error lines; empty means success."""
    errors: list[str] = []

    for root in _SCAN_ROOTS:
        if not root.is_dir():
            errors.append(f"missing scan root: {root.relative_to(_REPO)}")
            continue

        for path in sorted(root.rglob("manifest.json")):
            kind = _classify_manifest(path)
            if kind is None:
                errors.append(f"unclassified manifest: {path.relative_to(_REPO)}")
                continue
            try:
                load_artifact_file(path, kind)
            except Exception as e:
                errors.append(f"{path.relative_to(_REPO)} [{kind}]: {e}")

        for name, kind in (
            ("campaign-summary.json", "campaign_summary"),
            ("campaign-semantic-summary.json", "campaign_semantic_summary"),
            ("campaign-result-pack.json", "campaign_result_pack"),
            ("pack-compare.json", "campaign_result_pack_comparison"),
            ("campaign-compare.json", "campaign_compare"),
        ):
            for path in sorted(root.rglob(name)):
                try:
                    load_artifact_file(path, kind)
                except Exception as e:
                    errors.append(f"{path.relative_to(_REPO)} [{kind}]: {e}")

        for path in sorted(root.rglob("browser_evidence.json")):
            try:
                load_artifact_file(path, "browser_evidence")
            except Exception as e:
                errors.append(f"{path.relative_to(_REPO)} [browser_evidence]: {e}")

        for path in sorted(root.rglob("evaluation.json")):
            try:
                load_artifact_file(path, "evaluation")
            except Exception as e:
                errors.append(f"{path.relative_to(_REPO)} [evaluation]: {e}")

        for path in sorted(root.rglob("benchmark_response.json")):
            try:
                load_artifact_file(path, "benchmark_response")
            except Exception as e:
                errors.append(f"{path.relative_to(_REPO)} [benchmark_response]: {e}")

        for path in sorted(root.rglob("benchmark_request.json")):
            try:
                load_artifact_file(path, "benchmark_request")
            except Exception as e:
                errors.append(f"{path.relative_to(_REPO)} [benchmark_request]: {e}")

        for path in sorted(root.rglob("evaluation_judge_provenance.json")):
            try:
                load_artifact_file(path, "evaluation_judge_provenance")
            except Exception as e:
                errors.append(f"{path.relative_to(_REPO)} [evaluation_judge_provenance]: {e}")

        for path in sorted(root.rglob("reports/report.json")):
            try:
                load_artifact_file(path, "report")
            except Exception as e:
                errors.append(f"{path.relative_to(_REPO)} [report]: {e}")

        for path in sorted(
            (p for p in root.rglob("pairwise.json") if p.parent.name == "matrices"),
        ):
            try:
                load_artifact_file(path, "matrix")
            except Exception as e:
                errors.append(f"{path.relative_to(_REPO)} [matrix/pairwise]: {e}")

        for path in sorted(
            (p for p in root.rglob("grid.json") if p.parent.name == "matrices"),
        ):
            try:
                load_artifact_file(path, "matrix")
            except Exception as e:
                errors.append(f"{path.relative_to(_REPO)} [matrix/grid]: {e}")

        for path in sorted(
            (p for p in root.rglob("grid.row_inputs.json") if p.parent.name == "matrices"),
        ):
            try:
                load_artifact_file(path, "matrix_grid_inputs")
            except Exception as e:
                errors.append(f"{path.relative_to(_REPO)} [matrix_grid_inputs]: {e}")

        for path in sorted(
            (p for p in root.rglob("pairwise.row_inputs.json") if p.parent.name == "matrices"),
        ):
            try:
                load_artifact_file(path, "matrix_pairwise_inputs")
            except Exception as e:
                errors.append(f"{path.relative_to(_REPO)} [matrix_pairwise_inputs]: {e}")

        rubric_dir = root / "dataset" / "rubrics"
        if rubric_dir.is_dir():
            for path in sorted(rubric_dir.glob("*.json")):
                try:
                    load_artifact_file(path, "rubric")
                except Exception as e:
                    errors.append(f"{path.relative_to(_REPO)} [rubric]: {e}")

    return errors


def test_committed_examples_fixtures_and_emitted_campaign_artifacts_validate() -> None:
    """JSON Schema + Pydantic for all committed benchmark/campaign/cell artifacts."""
    errors = collect_committed_artifact_drift_errors()
    assert not errors, "Schema drift:\n" + "\n".join(errors)


def test_example_campaign_member_manifest_observability_blocks_parse() -> None:
    """Regression: nested runtime_summary / retry_summary / cell.runtime match manifest schema."""
    path = (
        _REPO
        / "examples"
        / "campaign_runs"
        / "minimal_offline"
        / "runs"
        / "run0000"
        / "manifest.json"
    )
    m = load_artifact_file(path, "benchmark_manifest")
    assert m.runtime_summary is not None
    assert m.runtime_summary.schema_version == 1
    assert m.runtime_summary.started_at_utc
    assert m.retry_summary is not None
    assert m.retry_summary.schema_version == 1
    cell0 = m.cells[0]
    assert cell0.runtime is not None
    assert cell0.runtime.schema_version == 1


def test_campaign_generated_report_paths_and_semantic_summary_example_parse() -> None:
    camp = _REPO / "examples" / "campaign_runs" / "minimal_offline"
    cm = load_artifact_file(camp / "manifest.json", "benchmark_campaign_manifest")
    assert cm.generated_report_paths is not None
    gp = cm.generated_report_paths
    assert (
        gp.campaign_semantic_summary_json is not None or gp.campaign_semantic_summary_md is not None
    )
    load_artifact_file(camp / "campaign-semantic-summary.json", "campaign_semantic_summary")


@pytest.mark.parametrize(
    "kind",
    [
        "benchmark_manifest",
        "benchmark_campaign_manifest",
        "campaign_summary",
        "campaign_semantic_summary",
        "campaign_result_pack",
        "browser_evidence",
        "evaluation",
        "benchmark_response",
        "benchmark_request",
        "evaluation_judge_provenance",
        "report",
        "matrix",
        "matrix_grid_inputs",
        "matrix_pairwise_inputs",
        "rubric",
    ],
)
def test_drift_suite_covers_registered_kind(kind: str) -> None:
    """Guardrail: when we add a sweep for a kind, keep this list in sync."""
    from agent_llm_wiki_matrix.artifacts import list_artifact_kinds

    kinds = set(list_artifact_kinds())
    assert kind in kinds
