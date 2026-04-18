"""Compare two campaign result pack directories (identity, artifacts, metrics, tags)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agent_llm_wiki_matrix.artifacts import load_artifact_file
from agent_llm_wiki_matrix.benchmark.campaign_compare_core import (
    build_analysis_comparison_block,
    build_browser_evidence_member_cells_comparison_block,
    build_failure_tag_comparison_block,
    build_reader_interpretation,
    build_semantic_comparison_block,
    experiment_fingerprint_axes,
    format_reader_interpretation_markdown,
    member_run_ids_diff,
    read_json_optional,
    render_browser_evidence_member_cells_comparison_markdown,
)
from agent_llm_wiki_matrix.benchmark.campaign_result_pack import (
    validate_campaign_result_pack_directory,
)
from agent_llm_wiki_matrix.benchmark.persistence import write_json_sorted, write_utf8_text
from agent_llm_wiki_matrix.models import (
    CampaignResultPackArtifacts,
    CampaignResultPackComparisonV1,
    CampaignResultPackV1,
)
from agent_llm_wiki_matrix.schema import load_schema, validate_json


def _utc_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _artifact_entries(art: CampaignResultPackArtifacts) -> dict[str, Any]:
    return art.model_dump(mode="json", exclude_none=False)


@dataclass(frozen=True)
class LoadedPackSide:
    """Resolved pack on disk + optional parsed JSON mirrors."""

    root: Path
    label: str
    pack: CampaignResultPackV1
    analysis: dict[str, Any] | None
    semantic: dict[str, Any] | None
    validation_errors: list[str]
    validation_warnings: list[str]


def load_campaign_result_pack_side(
    pack_dir: Path,
    *,
    label: str,
) -> LoadedPackSide:
    """Load pack manifest and optional analysis/semantic JSON from artifact paths."""
    root = pack_dir.resolve()
    pj = root / "campaign-result-pack.json"
    if not pj.is_file():
        msg = f"missing campaign-result-pack.json under {root}"
        raise FileNotFoundError(msg)
    pack = CampaignResultPackV1.model_validate(json.loads(pj.read_text(encoding="utf-8")))
    load_artifact_file(pj, "campaign_result_pack")
    art = pack.artifacts
    analysis_path = (root / art.campaign_analysis_json) if art.campaign_analysis_json else None
    sem_path = (
        (root / art.campaign_semantic_summary_json) if art.campaign_semantic_summary_json else None
    )
    analysis = read_json_optional(analysis_path) if analysis_path else None
    semantic = read_json_optional(sem_path) if sem_path else None
    vr = validate_campaign_result_pack_directory(root, strict_portability=False)
    return LoadedPackSide(
        root=root,
        label=label,
        pack=pack,
        analysis=analysis,
        semantic=semantic,
        validation_errors=list(vr.errors),
        validation_warnings=list(vr.warnings),
    )


def build_campaign_result_pack_comparison(
    left: Path,
    right: Path,
    *,
    left_label: str | None = None,
    right_label: str | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Structured diff for JSON output (schema ``campaign_result_pack_comparison``)."""
    ls = load_campaign_result_pack_side(
        left,
        label=left_label or str(left),
    )
    rs = load_campaign_result_pack_side(
        right,
        label=right_label or str(right),
    )
    lp, rp = ls.pack, rs.pack

    lcef = experiment_fingerprint_axes(lp.campaign_experiment_fingerprints)
    rcef = experiment_fingerprint_axes(rp.campaign_experiment_fingerprints)
    all_axes = sorted(set(lcef) | set(rcef))

    fp_rows: list[dict[str, Any]] = []
    for axis in all_axes:
        lv, rv = lcef.get(axis), rcef.get(axis)
        match = lv == rv
        fp_rows.append(
            {
                "axis": axis,
                "left": lv,
                "right": rv,
                "match": match,
            },
        )

    l_art = _artifact_entries(lp.artifacts)
    r_art = _artifact_entries(rp.artifacts)
    art_keys = sorted(set(l_art) | set(r_art))
    artifact_diffs: list[dict[str, Any]] = []
    for k in art_keys:
        lv, rv = l_art.get(k), r_art.get(k)
        artifact_diffs.append(
            {
                "artifact_key": k,
                "left": lv,
                "right": rv,
                "both_present": lv is not None and rv is not None,
                "same_relative_path": lv == rv,
            },
        )

    analysis_block = build_analysis_comparison_block(ls.analysis, rs.analysis)
    analysis_block["browser_evidence_comparison"] = (
        build_browser_evidence_member_cells_comparison_block(ls.analysis, rs.analysis)
    )
    semantic_block = build_semantic_comparison_block(ls.semantic, rs.semantic)
    tags_block = build_failure_tag_comparison_block(ls.analysis, rs.analysis)
    members_block = member_run_ids_diff(
        {m.run_id for m in lp.member_runs},
        {m.run_id for m in rp.member_runs},
    )

    portability = {
        "left": _portability_slice(lp, ls),
        "right": _portability_slice(rp, rs),
    }

    identity_block = {
        "same_campaign_id": lp.campaign_id == rp.campaign_id,
        "left_campaign_id": lp.campaign_id,
        "right_campaign_id": rp.campaign_id,
        "pack_identity_fingerprint": {
            "left": lp.pack_identity_fingerprint,
            "right": rp.pack_identity_fingerprint,
            "match": lp.pack_identity_fingerprint == rp.pack_identity_fingerprint,
        },
        "campaign_definition_fingerprint": {
            "left": lp.campaign_definition_fingerprint,
            "right": rp.campaign_definition_fingerprint,
            "match": lp.campaign_definition_fingerprint == rp.campaign_definition_fingerprint,
        },
        "campaign_experiment_fingerprints": fp_rows,
    }

    reader_interpretation = build_reader_interpretation(
        identity=identity_block,
        comparative_analysis=analysis_block,
        failure_tags=tags_block,
        semantic_summary_totals=semantic_block,
        member_runs=members_block,
        kind="pack",
    )

    return {
        "schema_version": 1,
        "created_at": _utc_iso(),
        "left": _side_header(ls, repo_root=repo_root),
        "right": _side_header(rs, repo_root=repo_root),
        "identity": identity_block,
        "artifacts": {
            "entries": artifact_diffs,
        },
        "comparative_analysis": analysis_block,
        "semantic_summary_totals": semantic_block,
        "failure_tags": tags_block,
        "member_runs": members_block,
        "portability": portability,
        "reader_interpretation": reader_interpretation,
    }


def _display_path(root: Path, repo_root: Path | None) -> str:
    resolved = root.resolve()
    if repo_root is None:
        return str(resolved)
    try:
        return str(resolved.relative_to(repo_root.resolve()))
    except ValueError:
        return str(resolved)


def _side_header(side: LoadedPackSide, *, repo_root: Path | None) -> dict[str, Any]:
    return {
        "path": _display_path(side.root, repo_root),
        "label": side.label,
        "pack_id": side.pack.pack_id,
        "title": side.pack.title,
        "campaign_id": side.pack.campaign_id,
    }


def _portability_slice(pack: CampaignResultPackV1, side: LoadedPackSide) -> dict[str, Any]:
    crc = None
    if pack.campaign_run_count is not None and pack.included_member_count is not None:
        crc = f"{pack.included_member_count}/{pack.campaign_run_count}"
    return {
        "member_depth": pack.member_depth,
        "longitudinal_member_glob": pack.longitudinal_member_glob,
        "has_source_campaign_dir": pack.source_campaign_dir is not None,
        "included_vs_campaign_run_count": crc,
        "pack_check_errors": side.validation_errors,
        "pack_check_warnings": side.validation_warnings,
    }


def render_campaign_result_pack_compare_markdown(data: dict[str, Any]) -> str:
    """Markdown-first comparison report."""
    left = data["left"]
    right = data["right"]
    ident = data["identity"]
    lines = [
        "# Campaign result pack comparison",
        "",
        "Side-by-side view of two **`campaign_result_pack`** trees (published bundles). "
        "**Δ** columns use **right − left** when both sides are numeric. "
        "See **`pack-compare.json`** for the full structured diff.",
        "",
        f"- **Left:** `{left['label']}` — `{left['path']}` (`pack_id`: `{left['pack_id']}`)",
        f"- **Right:** `{right['label']}` — `{right['path']}` (`pack_id`: `{right['pack_id']}`)",
        f"- **Generated:** `{data['created_at']}`",
        "",
    ]
    ri = data.get("reader_interpretation")
    if isinstance(ri, dict) and ri:
        lines.append(format_reader_interpretation_markdown(ri).rstrip())
        lines.append("")
    lines.extend(
        [
            "## Identity & fingerprints",
            "",
            "| Check | Value |",
            "| --- | --- |",
            f"| Same **campaign_id** | {'yes' if ident['same_campaign_id'] else '**no**'} |",
        ],
    )
    pip = ident["pack_identity_fingerprint"]
    match_s = "yes" if pip["match"] else "**no**"
    lines.append(f"| **pack_identity_fingerprint** match | {match_s} |")
    cdf = ident["campaign_definition_fingerprint"]
    lines.append(
        f"| **campaign_definition_fingerprint** match | "
        f"{'yes' if cdf['match'] else '**no**'} |",
    )
    lines.append("")
    lines.append("### campaign_experiment_fingerprints (per axis)")
    lines.append("")
    lines.append("| Axis | Left | Right | Match |")
    lines.append("| --- | --- | --- | --- |")
    for row in ident["campaign_experiment_fingerprints"]:
        m = "yes" if row["match"] else "no"
        lv = row.get("left") or "—"
        rv = row.get("right") or "—"
        lines.append(f"| `{row['axis']}` | `{lv}` | `{rv}` | {m} |")
    lines.append("")
    lines.append("## Included artifacts (paths in pack)")
    lines.append("")
    lines.append("| Artifact key | Left | Right | Same path |")
    lines.append("| --- | --- | --- | --- |")
    for row in data["artifacts"]["entries"]:
        sp = "yes" if row["same_relative_path"] else "no"
        lv = row.get("left") or "—"
        rv = row.get("right") or "—"
        lines.append(f"| `{row['artifact_key']}` | `{lv}` | `{rv}` | {sp} |")

    ca = data["comparative_analysis"]
    lines.extend(
        [
            "",
            "## Comparative analysis (`campaign-analysis.json`)",
            "",
            f"- **Left file present:** {ca['left_present']}",
            f"- **Right file present:** {ca['right_present']}",
            "",
            "### Backend mean scores (pooled cells)",
            "",
            "| backend_kind | Left | Right | Δ (R−L) |",
            "| --- | ---: | ---: | ---: |",
        ],
    )
    for row in ca["backend_performance"]:
        d = row["delta_right_minus_left"]
        ds = f"{d:.6f}" if isinstance(d, (int, float)) else "—"
        lm = row["left_mean_score"]
        rm = row["right_mean_score"]
        lms = f"{lm:.6f}" if isinstance(lm, (int, float)) else "—"
        rms = f"{rm:.6f}" if isinstance(rm, (int, float)) else "—"
        lines.append(
            f"| `{row['backend_kind']}` | {lms} | {rms} | {ds} |",
        )

    lines.extend(
        [
            "",
            "### Semantic instability (longitudinal counts by scoring_backend)",
            "",
            "| scoring_backend | Left events | Right events | Δ |",
            "| --- | ---: | ---: | ---: |",
        ],
    )
    for row in ca["semantic_instability_by_scoring_backend"]:
        d = row["delta_right_minus_left"]
        ds = str(d) if d is not None else "—"
        lines.append(
            f"| `{row['scoring_backend']}` | {row['left_unstable_events']} | "
            f"{row['right_unstable_events']} | {ds} |",
        )

    be_md = render_browser_evidence_member_cells_comparison_markdown(
        ca.get("browser_evidence_comparison"),
    )
    if be_md:
        lines.extend(["", be_md.rstrip(), ""])

    lines.extend(["", "## Failure tags (FT-*)", ""])
    ft = data["failure_tags"]
    if not ft["codes_compared"] or all(
        x.get("left_signal_count") in (None, 0) and x.get("right_signal_count") in (None, 0)
        for x in ft["codes_compared"]
    ):
        lines.append("_No FT-* signal counts on either side (or analysis missing)._")
    else:
        lines.extend(
            [
                "| Code | Left signals | Right signals | Δ |",
                "| --- | ---: | ---: | ---: |",
            ],
        )
        for row in ft["codes_compared"]:
            if row.get("left_signal_count") is None and row.get("right_signal_count") is None:
                continue
            d = row["delta_right_minus_left"]
            ds = str(d) if d is not None else "—"
            lines.append(
                f"| `{row['code']}` | {row['left_signal_count']} | "
                f"{row['right_signal_count']} | {ds} |",
            )
    if ft["only_in_left"]:
        lines.append("")
        lines.append(f"- **Only left:** {', '.join(f'`{c}`' for c in ft['only_in_left'])}")
    if ft["only_in_right"]:
        lines.append(f"- **Only right:** {', '.join(f'`{c}`' for c in ft['only_in_right'])}")

    lines.extend(["", "## Semantic summary totals (selected fields)", ""])
    sem = data["semantic_summary_totals"]
    if sem["left_totals"] is None and sem["right_totals"] is None:
        lines.append("_No `campaign-semantic-summary.json` on both sides (or empty totals)._")
    else:
        lines.append("See JSON for full totals; numeric Δ = right − left when both numeric.")
        for k, v in sem.get("numeric_deltas_right_minus_left", {}).items():
            lines.append(f"- **`{k}`:** {v}")

    mr = data["member_runs"]
    lines.extend(
        [
            "",
            "## Member runs",
            "",
            f"- **Left count:** {mr['left_count']} · **Right count:** {mr['right_count']}",
            (
                "- **Only in left:** "
                f"{', '.join(f'`{x}`' for x in mr['run_ids_only_in_left']) or '—'}"
            ),
            (
                "- **Only in right:** "
                f"{', '.join(f'`{x}`' for x in mr['run_ids_only_in_right']) or '—'}"
            ),
            "",
            "## Portability & completeness",
            "",
        ],
    )
    for side_name in ("left", "right"):
        p = data["portability"][side_name]
        lines.append(f"### {side_name.title()} pack")
        lines.append("")
        lines.append(f"- **member_depth:** `{p['member_depth']}`")
        lines.append(f"- **longitudinal_member_glob:** `{p['longitudinal_member_glob']}`")
        lines.append(
            f"- **source_campaign_dir set:** {'yes' if p['has_source_campaign_dir'] else 'no'} "
            "(absolute paths reduce portability)",
        )
        if p["included_vs_campaign_run_count"]:
            crc = p["included_vs_campaign_run_count"]
            lines.append(f"- **included / campaign_run_count:** `{crc}`")
        if p["pack_check_warnings"]:
            lines.append("- **pack-check warnings:**")
            for w in p["pack_check_warnings"]:
                lines.append(f"  - {w}")
        if p["pack_check_errors"]:
            lines.append("- **pack-check errors:**")
            for w in p["pack_check_errors"]:
                lines.append(f"  - {w}")
        lines.append("")
    lines.append(
        "_Machine-readable summary: `pack-compare.json` (kind `campaign_result_pack_comparison`)._",
    )
    return "\n".join(lines)


def write_campaign_result_pack_compare_artifacts(
    output_dir: Path,
    data: dict[str, Any],
) -> tuple[Path, Path]:
    """Write ``pack-compare.json`` and ``pack-compare-report.md``; validate JSON kind."""
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "pack-compare.json"
    md_path = output_dir / "pack-compare-report.md"
    validate_json(data, load_schema("schemas/v1/campaign_result_pack_comparison.schema.json"))
    CampaignResultPackComparisonV1.model_validate(data)
    write_json_sorted(json_path, data)
    write_utf8_text(md_path, render_campaign_result_pack_compare_markdown(data))
    return json_path, md_path


def compare_campaign_result_packs_cli(
    left: Path,
    right: Path,
    *,
    output_dir: Path,
    left_label: str | None,
    right_label: str | None,
    repo_root: Path | None = None,
) -> tuple[Path, Path]:
    """Build comparison dict, validate, write Markdown + JSON."""
    data = build_campaign_result_pack_comparison(
        left,
        right,
        left_label=left_label,
        right_label=right_label,
        repo_root=repo_root,
    )
    return write_campaign_result_pack_compare_artifacts(output_dir.resolve(), data)
