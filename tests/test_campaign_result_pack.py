"""Campaign result pack assembly and validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_llm_wiki_matrix.artifacts import load_artifact_file
from agent_llm_wiki_matrix.benchmark.campaign_result_pack import (
    assemble_campaign_result_pack,
    compute_pack_identity_fingerprint,
    validate_campaign_result_pack_directory,
)

_REPO = Path(__file__).resolve().parents[1]
_MINIMAL_CAMPAIGN = _REPO / "examples" / "campaign_runs" / "minimal_offline"


@pytest.fixture
def minimal_campaign_dir(tmp_path: Path) -> Path:
    """Isolated copy so tests never mutate committed examples."""
    import shutil

    dest = tmp_path / "minimal_offline"
    shutil.copytree(_MINIMAL_CAMPAIGN, dest)
    return dest


def test_assemble_full_pack_validates_and_copies_runs(
    minimal_campaign_dir: Path,
    tmp_path: Path,
) -> None:
    pack_dir = tmp_path / "pack"
    pack = assemble_campaign_result_pack(
        campaign_dir=minimal_campaign_dir,
        pack_dir=pack_dir,
        pack_id="test-pack-full",
        created_at="2026-04-18T12:00:00Z",
        source_campaign_relpath="examples/campaign_runs/minimal_offline",
        record_source_abspath=False,
    )
    assert pack.pack_id == "test-pack-full"
    assert pack.member_depth == "full"
    assert pack.member_runs
    assert (pack_dir / "campaign-result-pack.json").is_file()
    assert (pack_dir / "INDEX.md").is_file()
    assert (pack_dir / "runs" / "run0000" / "manifest.json").is_file()
    assert (pack_dir / "runs" / "run0000" / "cells").is_dir()
    load_artifact_file(pack_dir / "campaign-result-pack.json", "campaign_result_pack")
    assert pack.pack_identity_fingerprint
    assert pack.pack_identity_fingerprint.startswith("sha256:")
    assert pack.membership_scope == "all_runs"
    assert "semantic_summary" in (pack.optional_layers_present or [])
    chk = validate_campaign_result_pack_directory(pack_dir)
    assert chk.ok(strict_portability=False)
    assert not chk.errors
    index_text = (pack_dir / "INDEX.md").read_text(encoding="utf-8")
    assert "For reviewers (read this first)" in index_text
    assert "What is included" in index_text
    assert "membership_scope" in index_text
    assert "Publish-ready checklist" in index_text


def test_pack_identity_fingerprint_stable_across_pack_ids(
    minimal_campaign_dir: Path,
    tmp_path: Path,
) -> None:
    a = tmp_path / "pa"
    b = tmp_path / "pb"
    p1 = assemble_campaign_result_pack(
        campaign_dir=minimal_campaign_dir,
        pack_dir=a,
        pack_id="pack-one",
        created_at="2026-04-18T12:00:00Z",
    )
    p2 = assemble_campaign_result_pack(
        campaign_dir=minimal_campaign_dir,
        pack_dir=b,
        pack_id="pack-two",
        created_at="2026-04-19T12:00:00Z",
    )
    assert p1.pack_id != p2.pack_id
    assert compute_pack_identity_fingerprint(p1) == compute_pack_identity_fingerprint(p2)


def test_pack_check_fails_when_index_missing(minimal_campaign_dir: Path, tmp_path: Path) -> None:
    pack_dir = tmp_path / "pack"
    assemble_campaign_result_pack(
        campaign_dir=minimal_campaign_dir,
        pack_dir=pack_dir,
        pack_id="x",
        created_at="2026-04-18T12:00:00Z",
    )
    (pack_dir / "INDEX.md").unlink()
    chk = validate_campaign_result_pack_directory(pack_dir)
    assert chk.errors


def test_pack_check_strict_flags_manifest_depth(minimal_campaign_dir: Path, tmp_path: Path) -> None:
    pack_dir = tmp_path / "pack-m"
    assemble_campaign_result_pack(
        campaign_dir=minimal_campaign_dir,
        pack_dir=pack_dir,
        pack_id="strict",
        member_depth="manifest",
        created_at="2026-04-18T12:00:00Z",
    )
    loose = validate_campaign_result_pack_directory(pack_dir)
    assert loose.ok(strict_portability=False)
    assert loose.warnings
    strict = validate_campaign_result_pack_directory(pack_dir, strict_portability=True)
    assert not strict.ok(strict_portability=True)


def test_pack_records_dry_run_artifact_when_present(
    minimal_campaign_dir: Path,
    tmp_path: Path,
) -> None:
    (minimal_campaign_dir / "campaign-dry-run.json").write_text(
        '{"schema_version":1,"planned_run_count":1}\n',
        encoding="utf-8",
    )
    pack_dir = tmp_path / "pack-dry"
    pack = assemble_campaign_result_pack(
        campaign_dir=minimal_campaign_dir,
        pack_dir=pack_dir,
        pack_id="with-dry",
        created_at="2026-04-18T12:00:00Z",
    )
    assert pack.artifacts.campaign_dry_run_json == "campaign-dry-run.json"
    assert (pack_dir / "campaign-dry-run.json").is_file()
    chk = validate_campaign_result_pack_directory(pack_dir)
    assert chk.ok(strict_portability=False)


def test_assemble_manifest_depth_skips_cells(minimal_campaign_dir: Path, tmp_path: Path) -> None:
    pack_dir = tmp_path / "pack-m"
    assemble_campaign_result_pack(
        campaign_dir=minimal_campaign_dir,
        pack_dir=pack_dir,
        pack_id="test-pack-m",
        member_depth="manifest",
        created_at="2026-04-18T12:00:00Z",
    )
    assert (pack_dir / "runs" / "run0000" / "manifest.json").is_file()
    assert not (pack_dir / "runs" / "run0000" / "cells").exists()


def test_cli_pack_invocation_smoke(minimal_campaign_dir: Path, tmp_path: Path) -> None:
    from click.testing import CliRunner

    from agent_llm_wiki_matrix.cli import main

    out = tmp_path / "cli_pack"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "benchmark",
            "campaign",
            "pack",
            str(minimal_campaign_dir),
            "--output-dir",
            str(out),
            "--pack-id",
            "cli-smoke",
            "--title",
            "CLI smoke title",
            "--source-label",
            "examples/campaign_runs/minimal_offline",
        ],
    )
    assert result.exit_code == 0, result.output
    raw = (out / "campaign-result-pack.json").read_text(encoding="utf-8")
    assert "CLI smoke title" in raw
    load_artifact_file(out / "campaign-result-pack.json", "campaign_result_pack")

    r2 = runner.invoke(
        main,
        ["benchmark", "campaign", "pack-check", str(out)],
    )
    assert r2.exit_code == 0, r2.output
    assert "ok" in r2.output
