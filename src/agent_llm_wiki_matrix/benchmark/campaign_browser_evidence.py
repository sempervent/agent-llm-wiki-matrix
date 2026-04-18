"""Aggregate browser evidence across succeeded campaign member runs."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from agent_llm_wiki_matrix.artifacts import load_artifact_file
from agent_llm_wiki_matrix.browser.formatting import (
    BrowserEvidenceReportRow,
    browser_evidence_report_row_from_evidence,
    extension_digest_short,
    render_browser_evidence_detail_markdown,
    render_campaign_browser_evidence_table_only,
    screenshot_primary_viewport_summary,
    signals_digest_line,
)
from agent_llm_wiki_matrix.browser.models import BrowserEvidence
from agent_llm_wiki_matrix.models import BenchmarkCampaignManifest, BenchmarkRunManifest


def _request_browser_runner(run_root: Path, request_relpath: str) -> str | None:
    req_path = run_root / request_relpath
    if not req_path.is_file():
        return None
    raw = json.loads(req_path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        br = raw.get("browser_runner")
        return str(br) if br else None
    return None


def iter_campaign_browser_evidence(
    *,
    campaign_dir: Path,
    manifest: object,
) -> list[tuple[str, str, str, str, str, BrowserEvidence]]:
    """``(run_id, benchmark_id, suite_ref, cell_id, runner, evidence)`` per browser cell."""
    if not isinstance(manifest, BenchmarkCampaignManifest):
        msg = "manifest must be BenchmarkCampaignManifest"
        raise TypeError(msg)

    out: list[tuple[str, str, str, str, str, BrowserEvidence]] = []
    for entry in manifest.runs:
        if entry.status != "succeeded":
            continue
        run_root = (campaign_dir / entry.output_relpath).resolve()
        mf_path = run_root / "manifest.json"
        if not mf_path.is_file():
            continue
        mf = BenchmarkRunManifest.model_validate(
            json.loads(mf_path.read_text(encoding="utf-8")),
        )
        for cell in mf.cells:
            if not cell.browser_evidence_relpath:
                continue
            ev_path = run_root / cell.browser_evidence_relpath
            if not ev_path.is_file():
                continue
            ev = load_artifact_file(ev_path, "browser_evidence")
            if not isinstance(ev, BrowserEvidence):
                continue
            runner = _request_browser_runner(run_root, cell.request_relpath) or "—"
            out.append(
                (
                    entry.run_id,
                    entry.benchmark_id,
                    entry.suite_ref,
                    cell.cell_id,
                    runner,
                    ev,
                ),
            )
    return out


def render_campaign_browser_cross_run_comparison(
    items: list[tuple[str, str, str, str, str, BrowserEvidence]],
) -> str:
    """Short interpretation tables when multiple member runs carry browser evidence."""
    if len(items) < 2:
        return ""
    seen: list[str] = []
    for rid, *_rest in items:
        if rid not in seen:
            seen.append(rid)
    if len(seen) < 2:
        return ""
    by_run: dict[str, list[tuple[str, str, str, str, str, BrowserEvidence]]] = defaultdict(list)
    for t in items:
        by_run[t[0]].append(t)

    lines = [
        "### Cross-run contrast (deterministic fixtures)",
        "",
        "**Aggregate coverage** (sums across **browser_mock** cells in that member run). "
        "**Screenshot metadata** uses the first capture’s viewport when present. "
        "**Extensions** may include **network** / **accessibility** / **performance** "
        "summaries and a **trace_digest**; when **`extensions.runner`** is **`mcp_stdio`**, "
        "the trace came through the **local MCP stdio** JSON bridge "
        "(not a remote browser session). "
        "**Playwright** remains optional for live capture. See `docs/architecture/browser.md`.",
        "",
        "#### Coverage by member run",
        "",
        "| run_id | suite_ref | Cells | Σ DOM excerpts | Σ screenshots | Primary viewport | "
        "| Ext. keys (union) |",
        "| --- | --- | ---: | ---: | ---: | --- | ---: |",
    ]
    for rid in seen:
        group = by_run[rid]
        _r0, _b0, suite_ref, _c0, _runner0, ev0 = group[0]
        sum_dom = sum(len(t[5].dom_excerpts) for t in group)
        sum_shot = sum(len(t[5].screenshots) for t in group)
        vp = screenshot_primary_viewport_summary(group[0][5])
        keys_u: set[str] = set()
        for t in group:
            keys_u |= set((t[5].extensions or {}).keys())
        lines.append(
            f"| `{rid}` | `{suite_ref}` | {len(group)} | {sum_dom} | {sum_shot} | `{vp}` | "
            f"{len(keys_u)} |",
        )
    lines.append("")
    lines.extend(
        [
            "#### Signals & extension digest (first cell per run)",
            "",
            "Quick read on **navigation/console/DOM/screenshot counts** and compact "
            "**extensions**.",
            "",
            "| run_id | suite_ref | Signals | Extension digest |",
            "| --- | --- | --- | --- |",
        ],
    )
    for rid in seen:
        first = next(t for t in items if t[0] == rid)
        _r, _b, suite_ref, _c, _runner, ev = first
        lines.append(
            f"| `{rid}` | `{suite_ref}` | {signals_digest_line(ev)} | "
            f"{extension_digest_short(ev.extensions)} |",
        )
    lines.append("")
    return "\n".join(lines)


def campaign_browser_evidence_json_rows(
    *,
    campaign_dir: Path,
    manifest: object,
) -> list[dict[str, Any]]:
    """Rows for ``campaign-analysis.json``."""
    rows: list[dict[str, Any]] = []
    for run_id, bench_id, suite_ref, cell_id, runner, ev in iter_campaign_browser_evidence(
        campaign_dir=campaign_dir,
        manifest=manifest,
    ):
        rows.append(
            {
                "run_id": run_id,
                "benchmark_id": bench_id,
                "suite_ref": suite_ref,
                "cell_id": cell_id,
                "browser_runner": runner,
                "evidence_id": ev.id,
                "evidence_title": ev.title,
                "dom_excerpt_count": len(ev.dom_excerpts),
                "screenshot_count": len(ev.screenshots),
                "has_dom_snapshot_ref": bool(ev.dom_snapshot_ref),
                "extension_keys": sorted((ev.extensions or {}).keys()),
                "signals_digest": signals_digest_line(ev),
                "extension_digest": extension_digest_short(ev.extensions),
            },
        )
    return rows


def render_campaign_browser_evidence_markdown(
    *,
    campaign_dir: Path,
    manifest: object,
) -> str:
    """Markdown section for ``reports/campaign-report.md``."""
    from agent_llm_wiki_matrix.benchmark.campaign_reporting import (
        suite_ref_benchmark_id_partition_coincide,
    )

    items = iter_campaign_browser_evidence(campaign_dir=campaign_dir, manifest=manifest)
    if not items:
        return ""

    coincide = False
    if isinstance(manifest, BenchmarkCampaignManifest):
        coincide = suite_ref_benchmark_id_partition_coincide(manifest)

    table_rows: list[BrowserEvidenceReportRow] = []
    for run_id, _b, _s, cell_id, runner, ev in items:
        rid = f"{run_id} / {cell_id}"
        table_rows.append(
            browser_evidence_report_row_from_evidence(
                cell_id=rid,
                runner=runner,
                evidence=ev,
            ),
        )

    cross = render_campaign_browser_cross_run_comparison(items).rstrip()
    table_md = render_campaign_browser_evidence_table_only(table_rows).rstrip()
    lines = [
        "## Browser evidence (member runs)",
        "",
        "**browser_mock** file-backed traces (`fixtures/browser_evidence/v1/`). "
        "**Playwright** is optional (`[browser]` + env). **MCP** stdio is a **local** JSON bridge "
        "to a subprocess — not IDE-hosted or remote capture (`docs/architecture/browser.md`).",
        "",
    ]
    if cross:
        lines.append(cross)
        lines.append("")
    lines.append(table_md)
    lines.extend(
        [
            "",
            "### Per-cell traces",
            "",
        ],
    )
    for run_id, bench_id, suite_ref, cell_id, runner, ev in items:
        if coincide:
            label = f"`{run_id}` · `{cell_id}`"
        else:
            label = f"`{run_id}` · `{bench_id}` · `{cell_id}`"
        lines.append(
            render_browser_evidence_detail_markdown(
                heading_label=label,
                suite_ref=suite_ref,
                runner=runner,
                evidence=ev,
            ).rstrip(),
        )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
