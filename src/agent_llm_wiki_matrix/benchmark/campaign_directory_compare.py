"""Compare two completed campaign output directories (first-class workflow)."""

from __future__ import annotations

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
from agent_llm_wiki_matrix.benchmark.campaign_reporting import summarize_campaign_dimensions
from agent_llm_wiki_matrix.benchmark.persistence import write_json_sorted, write_utf8_text
from agent_llm_wiki_matrix.models import BenchmarkCampaignManifest, CampaignCompareV1
from agent_llm_wiki_matrix.schema import load_schema, validate_json

CAMPAIGN_ARTIFACT_RELPATHS: tuple[tuple[str, str], ...] = (
    ("campaign_manifest", "manifest.json"),
    ("campaign_summary_json", "campaign-summary.json"),
    ("campaign_summary_md", "campaign-summary.md"),
    ("campaign_semantic_summary_json", "campaign-semantic-summary.json"),
    ("campaign_semantic_summary_md", "campaign-semantic-summary.md"),
    ("campaign_comparative_report_md", "reports/campaign-report.md"),
    ("campaign_analysis_json", "reports/campaign-analysis.json"),
)


def _utc_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _display_path(root: Path, repo_root: Path | None) -> str:
    resolved = root.resolve()
    if repo_root is None:
        return str(resolved)
    try:
        return str(resolved.relative_to(repo_root.resolve()))
    except ValueError:
        return str(resolved)


@dataclass(frozen=True)
class LoadedCampaignSide:
    """Completed campaign tree: manifest plus optional analysis mirrors."""

    root: Path
    label: str
    manifest: BenchmarkCampaignManifest
    analysis: dict[str, Any] | None
    semantic: dict[str, Any] | None


def load_campaign_directory_side(campaign_dir: Path, *, label: str) -> LoadedCampaignSide:
    root = campaign_dir.resolve()
    mp = root / "manifest.json"
    if not mp.is_file():
        msg = f"missing campaign manifest: {mp}"
        raise FileNotFoundError(msg)
    parsed = load_artifact_file(mp, "campaign_manifest")
    manifest = BenchmarkCampaignManifest.model_validate(parsed.model_dump(mode="json"))
    analysis = read_json_optional(root / "reports" / "campaign-analysis.json")
    semantic = read_json_optional(root / "campaign-semantic-summary.json")
    return LoadedCampaignSide(
        root=root,
        label=label,
        manifest=manifest,
        analysis=analysis,
        semantic=semantic,
    )


def build_sweep_dimensions_diff(
    left_m: BenchmarkCampaignManifest,
    right_m: BenchmarkCampaignManifest,
) -> dict[str, Any]:
    """Contrast sweep-axis coverage using :func:`summarize_campaign_dimensions`."""
    ld = summarize_campaign_dimensions(left_m)
    rd = summarize_campaign_dimensions(right_m)
    lj = dict(ld)
    rj = dict(rd)
    keys = sorted(set(lj) | set(rj))
    rows: list[dict[str, Any]] = []
    varied_differ: list[str] = []
    for k in keys:
        lsub = lj.get(k) or {}
        rsub = rj.get(k) or {}
        lv = lsub.get("varied")
        rv = rsub.get("varied")
        if lv != rv:
            varied_differ.append(k)
        rows.append(
            {
                "axis": k,
                "left_varied": lv,
                "right_varied": rv,
                "left_distinct_count": lsub.get("distinct_count"),
                "right_distinct_count": rsub.get("distinct_count"),
                "values_match": lsub.get("values") == rsub.get("values"),
            },
        )
    return {
        "left_dimensions": lj,
        "right_dimensions": rj,
        "per_axis": rows,
        "varied_flags_differ_on_axes": varied_differ,
    }


def build_fingerprint_insights_diff(
    left_analysis: dict[str, Any] | None,
    right_analysis: dict[str, Any] | None,
) -> dict[str, Any]:
    """Diff ``fingerprint_axis_insights`` blocks from each ``campaign-analysis.json``."""
    la = left_analysis.get("fingerprint_axis_insights") if left_analysis else None
    ra = right_analysis.get("fingerprint_axis_insights") if right_analysis else None
    if not isinstance(la, list):
        la = None
    if not isinstance(ra, list):
        ra = None
    li = {
        str(x.get("axis_key")): x
        for x in (la or [])
        if isinstance(x, dict) and x.get("axis_key") is not None
    }
    ri = {
        str(x.get("axis_key")): x
        for x in (ra or [])
        if isinstance(x, dict) and x.get("axis_key") is not None
    }
    keys = sorted(set(li) | set(ri))
    rows: list[dict[str, Any]] = []
    for k in keys:
        left_axis = li.get(k, {})
        r = ri.get(k, {})
        lsp = left_axis.get("pooled_mean_score_spread")
        rsp = r.get("pooled_mean_score_spread")
        d = None
        if isinstance(lsp, (int, float)) and isinstance(rsp, (int, float)):
            d = round(float(rsp) - float(lsp), 6)
        rows.append(
            {
                "axis_key": k,
                "left_varied": left_axis.get("varied"),
                "right_varied": r.get("varied"),
                "left_pooled_mean_score_spread": lsp,
                "right_pooled_mean_score_spread": rsp,
                "spread_delta_right_minus_left": d,
            },
        )
    return {
        "left_present": la is not None,
        "right_present": ra is not None,
        "per_axis_key": rows,
    }


def build_campaign_artifact_entries(root: Path) -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for key, rel in CAMPAIGN_ARTIFACT_RELPATHS:
        p = root / rel
        out[key] = rel if p.is_file() else None
    return out


def build_campaign_artifact_diff(left_root: Path, right_root: Path) -> list[dict[str, Any]]:
    la = build_campaign_artifact_entries(left_root)
    ra = build_campaign_artifact_entries(right_root)
    keys = sorted(set(la) | set(ra))
    rows: list[dict[str, Any]] = []
    for k in keys:
        lv, rv = la.get(k), ra.get(k)
        rows.append(
            {
                "artifact_key": k,
                "left": lv,
                "right": rv,
                "both_present": lv is not None and rv is not None,
                "same_relative_path": lv == rv,
            },
        )
    return rows


def build_campaign_directory_comparison(
    left: Path,
    right: Path,
    *,
    left_label: str | None = None,
    right_label: str | None = None,
    repo_root: Path | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Structured diff for ``campaign-compare.json`` (kind ``campaign_compare``)."""
    ls = load_campaign_directory_side(left, label=left_label or str(left))
    rs = load_campaign_directory_side(right, label=right_label or str(right))
    lm, rm = ls.manifest, rs.manifest

    lcef = experiment_fingerprint_axes(lm.campaign_experiment_fingerprints)
    rcef = experiment_fingerprint_axes(rm.campaign_experiment_fingerprints)
    all_axes = sorted(set(lcef) | set(rcef))
    fp_rows: list[dict[str, Any]] = []
    for axis in all_axes:
        lv, rv = lcef.get(axis), rcef.get(axis)
        fp_rows.append({"axis": axis, "left": lv, "right": rv, "match": lv == rv})

    sweep = build_sweep_dimensions_diff(lm, rm)
    fp_insights = build_fingerprint_insights_diff(ls.analysis, rs.analysis)
    artifact_entries = build_campaign_artifact_diff(ls.root, rs.root)

    l_run_ids = {r.run_id for r in lm.runs}
    r_run_ids = {r.run_id for r in rm.runs}

    ts = created_at or _utc_iso()
    analysis_block = build_analysis_comparison_block(ls.analysis, rs.analysis)
    semantic_block = build_semantic_comparison_block(ls.semantic, rs.semantic)
    tags_block = build_failure_tag_comparison_block(ls.analysis, rs.analysis)
    browser_block = build_browser_evidence_member_cells_comparison_block(ls.analysis, rs.analysis)
    members_block = member_run_ids_diff(l_run_ids, r_run_ids)

    identity_block = {
        "same_campaign_id": lm.campaign_id == rm.campaign_id,
        "left_campaign_id": lm.campaign_id,
        "right_campaign_id": rm.campaign_id,
        "campaign_definition_fingerprint": {
            "left": lm.campaign_definition_fingerprint,
            "right": rm.campaign_definition_fingerprint,
            "match": lm.campaign_definition_fingerprint == rm.campaign_definition_fingerprint,
        },
        "campaign_experiment_fingerprints": fp_rows,
        "definition_source_relpath": {
            "left": lm.definition_source_relpath,
            "right": rm.definition_source_relpath,
            "match": lm.definition_source_relpath == rm.definition_source_relpath,
        },
    }

    reader_interpretation = build_reader_interpretation(
        identity=identity_block,
        comparative_analysis=analysis_block,
        failure_tags=tags_block,
        semantic_summary_totals=semantic_block,
        member_runs=members_block,
        kind="campaign_directory",
        sweep_dimensions=sweep,
        fingerprint_insights_diff=fp_insights,
    )

    return {
        "schema_version": 1,
        "created_at": ts,
        "left": {
            "path": _display_path(ls.root, repo_root),
            "label": ls.label,
            "campaign_id": lm.campaign_id,
            "title": lm.title,
            "definition_source_relpath": lm.definition_source_relpath,
        },
        "right": {
            "path": _display_path(rs.root, repo_root),
            "label": rs.label,
            "campaign_id": rm.campaign_id,
            "title": rm.title,
            "definition_source_relpath": rm.definition_source_relpath,
        },
        "identity": identity_block,
        "sweep_dimensions": sweep,
        "fingerprint_axis_insights": fp_insights,
        "artifacts": {"entries": artifact_entries},
        "comparative_analysis": analysis_block,
        "semantic_summary_totals": semantic_block,
        "failure_tags": tags_block,
        "browser_evidence": browser_block,
        "member_runs": members_block,
        "run_health": {
            "left": {"dry_run": lm.dry_run, "manifest_run_count": lm.run_count},
            "right": {"dry_run": rm.dry_run, "manifest_run_count": rm.run_count},
        },
        "reader_interpretation": reader_interpretation,
    }


def render_campaign_compare_markdown(data: dict[str, Any]) -> str:
    """Human-readable campaign-vs-campaign report."""
    left = data["left"]
    right = data["right"]
    ident = data["identity"]
    lines = [
        "# Campaign directory comparison",
        "",
        "Compares two completed **campaign output directories** (manifest + standard artifacts). "
        "**Δ** columns use **right − left** when both sides are numeric. "
        "Structured mirror: **`campaign-compare.json`**.",
        "",
        f"- **Left:** `{left['label']}` — `{left['path']}`",
        f"- **Right:** `{right['label']}` — `{right['path']}`",
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
    cdf = ident["campaign_definition_fingerprint"]
    lines.append(
        f"| **campaign_definition_fingerprint** match | "
        f"{'yes' if cdf['match'] else '**no**'} |",
    )
    dsp = ident["definition_source_relpath"]
    lines.append(
        f"| **definition_source_relpath** match | "
        f"{'yes' if dsp['match'] else '**no**'} |",
    )
    lines.extend(
        [
            "",
            "### campaign_experiment_fingerprints (per axis)",
            "",
            "| Axis | Left | Right | Match |",
            "| --- | --- | --- | --- |",
        ],
    )
    for row in ident["campaign_experiment_fingerprints"]:
        m = "yes" if row["match"] else "no"
        lv = row.get("left") or "—"
        rv = row.get("right") or "—"
        lines.append(f"| `{row['axis']}` | `{lv}` | `{rv}` | {m} |")

    sw = data["sweep_dimensions"]
    lines.extend(
        [
            "",
            "## Sweep dimensions (manifest members)",
            "",
            "Which axes vary across member runs (`varied`), and whether value sets match.",
            "",
            "| Axis | L varied | R varied | Values match |",
            "| --- | --- | --- | --- |",
        ],
    )
    for row in sw["per_axis"]:
        vm = "yes" if row.get("values_match") else "no"
        lines.append(
            f"| `{row['axis']}` | {row.get('left_varied')} | {row.get('right_varied')} | {vm} |",
        )
    if sw["varied_flags_differ_on_axes"]:
        axes = ", ".join(f"`{a}`" for a in sw["varied_flags_differ_on_axes"])
        lines.extend(["", f"- **Varied flags differ on:** {axes}", ""])

    fpi = data["fingerprint_axis_insights"]
    lines.extend(
        [
            "## Fingerprint axis interpretation (from campaign-analysis)",
            "",
            "| axis_key | L varied | R varied | Δ spread (R−L) |",
            "| --- | --- | --- | --- |",
        ],
    )
    for row in fpi["per_axis_key"]:
        d = row.get("spread_delta_right_minus_left")
        ds = f"{d:.6f}" if isinstance(d, (int, float)) else "—"
        lines.append(
            f"| `{row['axis_key']}` | {row.get('left_varied')} | {row.get('right_varied')} | "
            f"{ds} |",
        )

    lines.extend(
        [
            "",
            "## Standard artifact paths",
            "",
            "| Key | Left | Right |",
            "| --- | --- | --- |",
        ],
    )
    for row in data["artifacts"]["entries"]:
        lv = row.get("left") or "—"
        rv = row.get("right") or "—"
        lines.append(f"| `{row['artifact_key']}` | `{lv}` | `{rv}` |")

    ca = data["comparative_analysis"]
    lines.extend(
        [
            "",
            "## Score movement (pooled backend means)",
            "",
            f"- **Left analysis present:** {ca['left_present']}",
            f"- **Right analysis present:** {ca['right_present']}",
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
        lines.append(f"| `{row['backend_kind']}` | {lms} | {rms} | {ds} |")

    lines.extend(
        [
            "",
            "## Instability movement (semantic instability by scoring_backend)",
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
        data.get("browser_evidence"),
        top_heading_level=2,
    )
    if be_md:
        lines.extend(["", be_md.rstrip()])

    ft = data["failure_tags"]
    lines.extend(["", "## Failure-tag changes (FT-*)", ""])
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

    sem = data["semantic_summary_totals"]
    lines.extend(["", "## Semantic summary totals (selected)", ""])
    if sem["left_totals"] is None and sem["right_totals"] is None:
        lines.append("_No `campaign-semantic-summary.json` on both sides (or empty totals)._")
    else:
        lines.append("Numeric Δ = right − left when both numeric.")
        for k, v in sem.get("numeric_deltas_right_minus_left", {}).items():
            lines.append(f"- **`{k}`:** {v}")

    mr = data["member_runs"]
    rh = data["run_health"]
    lines.extend(
        [
            "",
            "## Member runs",
            "",
            f"- **Left count:** {mr['left_count']} · **Right count:** {mr['right_count']}",
            (
                f"- **Left dry_run:** `{rh['left']['dry_run']}` · **Right dry_run:** "
                f"`{rh['right']['dry_run']}`"
            ),
            (
                "- **Only in left:** "
                f"{', '.join(f'`{x}`' for x in mr['run_ids_only_in_left']) or '—'}"
            ),
            (
                "- **Only in right:** "
                f"{', '.join(f'`{x}`' for x in mr['run_ids_only_in_right']) or '—'}"
            ),
            "",
            "_Machine-readable summary: `campaign-compare.json` (kind `campaign_compare`)._",
        ],
    )
    return "\n".join(lines)


def write_campaign_compare_artifacts(
    output_dir: Path,
    data: dict[str, Any],
) -> tuple[Path, Path]:
    """Write ``campaign-compare.json`` and ``campaign-compare-report.md``."""
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "campaign-compare.json"
    md_path = output_dir / "campaign-compare-report.md"
    validate_json(data, load_schema("schemas/v1/campaign_compare.schema.json"))
    CampaignCompareV1.model_validate(data)
    write_json_sorted(json_path, data)
    write_utf8_text(md_path, render_campaign_compare_markdown(data))
    return json_path, md_path


def compare_campaign_directories_cli(
    left: Path,
    right: Path,
    *,
    output_dir: Path,
    left_label: str | None,
    right_label: str | None,
    repo_root: Path | None = None,
    created_at: str | None = None,
) -> tuple[Path, Path]:
    """Build comparison dict, validate, write Markdown + JSON."""
    data = build_campaign_directory_comparison(
        left,
        right,
        left_label=left_label,
        right_label=right_label,
        repo_root=repo_root,
        created_at=created_at,
    )
    return write_campaign_compare_artifacts(output_dir.resolve(), data)
