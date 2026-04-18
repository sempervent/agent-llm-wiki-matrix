"""Aggregate semantic / hybrid judge variance across campaign member runs."""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from agent_llm_wiki_matrix.artifacts import load_artifact_file
from agent_llm_wiki_matrix.models import (
    BenchmarkCampaignManifest,
    BenchmarkCampaignRunEntry,
    BenchmarkCellArtifactPaths,
    BenchmarkResponse,
    BenchmarkRunManifest,
    CampaignGeneratedReportPaths,
    CampaignSemanticAxisRollup,
    CampaignSemanticCellRow,
    CampaignSemanticSummaryV1,
    CampaignSemanticTotals,
    Evaluation,
    EvaluationJudgeProvenance,
)


def _provider_axis_label(ref: str | None) -> str:
    return ref if ref is not None else "(default)"


def _extract_cell_metrics(
    *,
    run_dir: Path,
    cell: BenchmarkCellArtifactPaths,
    run_id: str,
    run_index: int,
    suite_ref: str,
    provider_config_ref: str | None,
    eval_scoring_label: str,
) -> CampaignSemanticCellRow:
    ev_path = run_dir / cell.evaluation_relpath
    br_path = run_dir / cell.aggregate_response_relpath
    ev = load_artifact_file(ev_path, "evaluation")
    if not isinstance(ev, Evaluation):
        msg = "Expected evaluation artifact"
        raise TypeError(msg)
    br = load_artifact_file(br_path, "benchmark_response")
    if not isinstance(br, BenchmarkResponse):
        msg = "Expected benchmark_response artifact"
        raise TypeError(msg)

    jp = cell.judge_provenance_relpath or ev.judge_provenance_relpath
    prov: EvaluationJudgeProvenance | None = None
    if jp:
        p = run_dir / jp
        if p.is_file():
            loaded = load_artifact_file(p, "evaluation_judge_provenance")
            if isinstance(loaded, EvaluationJudgeProvenance):
                prov = loaded

    ra = prov.repeat_aggregation if prov is not None else None
    max_r = ra.disagreement.max_range_across_criteria if ra is not None else None
    tw_stdev = ra.disagreement.total_weighted_stdev if ra is not None else None
    mean_st = ra.disagreement.mean_stdev_across_criteria if ra is not None else None
    conf_low = bool(ev.judge_low_confidence) if ev.judge_low_confidence is not None else False
    flags: list[str] = []
    if ra is not None:
        conf_low = conf_low or bool(ra.confidence.low_confidence)
        flags = list(ra.confidence.flags[:8])

    return CampaignSemanticCellRow(
        run_id=run_id,
        run_index=run_index,
        suite_ref=suite_ref,
        provider_config_ref=provider_config_ref,
        eval_scoring_label=eval_scoring_label,
        benchmark_id=br.benchmark_id,
        cell_id=cell.cell_id,
        variant_id=br.variant_id,
        prompt_id=br.prompt_id,
        execution_mode=br.execution_mode,
        backend_kind=br.backend_kind,
        scoring_backend=ev.scoring_backend,
        judge_repeat_count=ev.judge_repeat_count,
        judge_semantic_aggregation=ev.judge_semantic_aggregation,
        judge_low_confidence=ev.judge_low_confidence,
        repeat_aggregation_present=ra is not None,
        max_range_across_criteria=max_r,
        total_weighted_stdev=tw_stdev,
        mean_stdev_across_criteria=mean_st,
        confidence_low=conf_low,
        confidence_flags=flags,
    )


def _rollup(
    axis_kind: Literal["suite_ref", "provider_config_ref", "execution_mode"],
    rows: list[CampaignSemanticCellRow],
) -> list[CampaignSemanticAxisRollup]:
    buckets: dict[str, list[CampaignSemanticCellRow]] = defaultdict(list)
    for r in rows:
        if axis_kind == "suite_ref":
            k = r.suite_ref
        elif axis_kind == "provider_config_ref":
            k = _provider_axis_label(r.provider_config_ref)
        else:
            k = r.execution_mode
        buckets[k].append(r)

    out: list[CampaignSemanticAxisRollup] = []
    for axis_value in sorted(buckets.keys()):
        bucket = buckets[axis_value]
        sem = [x for x in bucket if x.scoring_backend in ("semantic_judge", "hybrid")]
        rep = [x for x in bucket if x.repeat_aggregation_present]
        low = [x for x in bucket if x.confidence_low]
        ranges = [
            x.max_range_across_criteria for x in rep if x.max_range_across_criteria is not None
        ]
        tws = [x.total_weighted_stdev for x in rep if x.total_weighted_stdev is not None]
        out.append(
            CampaignSemanticAxisRollup(
                axis_kind=axis_kind,
                axis_value=axis_value,
                cell_rows=len(bucket),
                semantic_cells=len(sem),
                repeat_judge_cells=len(rep),
                low_confidence_cells=len(low),
                max_range_observed=max(ranges) if ranges else None,
                mean_range_across_cells=sum(ranges) / len(ranges) if ranges else None,
                mean_total_weighted_stdev=sum(tws) / len(tws) if tws else None,
            ),
        )
    return out


def build_campaign_semantic_summary(
    *,
    campaign_id: str,
    title: str,
    created_at: str,
    repo_root: Path,
    campaign_dir: Path,
    runs: Sequence[BenchmarkCampaignRunEntry],
) -> CampaignSemanticSummaryV1:
    """Scan succeeded member runs and aggregate semantic/hybrid judge instability."""
    rows: list[CampaignSemanticCellRow] = []
    scanned = 0
    for entry in runs:
        if entry.status != "succeeded":
            continue
        run_dir = (campaign_dir / entry.output_relpath).resolve()
        mf_path = run_dir / "manifest.json"
        if not mf_path.is_file():
            continue
        mf = BenchmarkRunManifest.model_validate(
            json.loads(mf_path.read_text(encoding="utf-8")),
        )
        scanned += 1
        for cell in mf.cells:
            rows.append(
                _extract_cell_metrics(
                    run_dir=run_dir,
                    cell=cell,
                    run_id=entry.run_id,
                    run_index=entry.run_index,
                    suite_ref=entry.suite_ref,
                    provider_config_ref=entry.provider_config_ref,
                    eval_scoring_label=entry.eval_scoring_label,
                ),
            )

    det = sum(1 for r in rows if r.scoring_backend == "deterministic")
    sem = sum(1 for r in rows if r.scoring_backend in ("semantic_judge", "hybrid"))
    rep = [r for r in rows if r.repeat_aggregation_present]
    low = [r for r in rows if r.confidence_low]
    ranges = [r.max_range_across_criteria for r in rep if r.max_range_across_criteria is not None]
    tws = [r.total_weighted_stdev for r in rep if r.total_weighted_stdev is not None]

    totals = CampaignSemanticTotals(
        runs_scanned=scanned,
        cells_total=len(rows),
        cells_deterministic=det,
        cells_semantic_or_hybrid=sem,
        cells_with_repeat_judge=len(rep),
        low_confidence_cells=len(low),
        max_range_across_campaign=max(ranges) if ranges else None,
        mean_range_repeat_cells=sum(ranges) / len(ranges) if ranges else None,
        mean_total_weighted_stdev_repeat=sum(tws) / len(tws) if tws else None,
    )

    return CampaignSemanticSummaryV1(
        schema_version=1,
        campaign_id=campaign_id,
        title=title,
        created_at=created_at,
        totals=totals,
        by_suite=_rollup("suite_ref", rows),
        by_provider=_rollup("provider_config_ref", rows),
        by_execution_mode=_rollup("execution_mode", rows),
        cells=rows,
    )


def render_campaign_semantic_summary_markdown(summary: CampaignSemanticSummaryV1) -> str:
    """Markdown view: totals, low-confidence highlights, rollups by suite/provider/mode."""
    t = summary.totals
    mrc = t.max_range_across_campaign
    mrr = t.mean_range_repeat_cells
    mtw = t.mean_total_weighted_stdev_repeat
    lines = [
        f"# Semantic & hybrid scoring — `{summary.campaign_id}`",
        "",
        f"- **title:** {summary.title}",
        f"- **created_at:** `{summary.created_at}`",
        "",
        "## Totals",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Runs scanned | {t.runs_scanned} |",
        f"| Cells total | {t.cells_total} |",
        f"| Deterministic cells | {t.cells_deterministic} |",
        f"| Semantic / hybrid cells | {t.cells_semantic_or_hybrid} |",
        f"| Cells with repeat judge (N>1) | {t.cells_with_repeat_judge} |",
        f"| Low-confidence cells | {t.low_confidence_cells} |",
        f"| Max range across campaign | {mrc if mrc is not None else '—'} |",
        f"| Mean range (repeat cells) | {mrr if mrr is not None else '—'} |",
        (
            f"| Mean σ total weighted (repeat cells) | "
            f"{mtw if mtw is not None else '—'} |"
        ),
        "",
        "## By suite",
        "",
        (
            "| Suite | Cells | Semantic | Repeat judge | Low conf. | "
            "Max range | Mean range | Mean σ_tot |"
        ),
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for a in summary.by_suite:
        lines.append(
            f"| `{a.axis_value}` | {a.cell_rows} | {a.semantic_cells} | {a.repeat_judge_cells} | "
            f"{a.low_confidence_cells} | "
            f"{a.max_range_observed if a.max_range_observed is not None else '—'} | "
            f"{a.mean_range_across_cells if a.mean_range_across_cells is not None else '—'} | "
            f"{a.mean_total_weighted_stdev if a.mean_total_weighted_stdev is not None else '—'} |",
        )
    lines.extend(
        [
            "",
            "## By provider config (campaign axis)",
            "",
            (
                "| Provider ref | Cells | Semantic | Repeat judge | Low conf. | "
                "Max range | Mean range | Mean σ_tot |"
            ),
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ],
    )
    for a in summary.by_provider:
        lines.append(
            f"| `{a.axis_value}` | {a.cell_rows} | {a.semantic_cells} | {a.repeat_judge_cells} | "
            f"{a.low_confidence_cells} | "
            f"{a.max_range_observed if a.max_range_observed is not None else '—'} | "
            f"{a.mean_range_across_cells if a.mean_range_across_cells is not None else '—'} | "
            f"{a.mean_total_weighted_stdev if a.mean_total_weighted_stdev is not None else '—'} |",
        )
    lines.extend(
        [
            "",
            "## By execution mode",
            "",
            (
                "| Mode | Cells | Semantic | Repeat judge | Low conf. | "
                "Max range | Mean range | Mean σ_tot |"
            ),
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ],
    )
    for a in summary.by_execution_mode:
        lines.append(
            f"| `{a.axis_value}` | {a.cell_rows} | {a.semantic_cells} | {a.repeat_judge_cells} | "
            f"{a.low_confidence_cells} | "
            f"{a.max_range_observed if a.max_range_observed is not None else '—'} | "
            f"{a.mean_range_across_cells if a.mean_range_across_cells is not None else '—'} | "
            f"{a.mean_total_weighted_stdev if a.mean_total_weighted_stdev is not None else '—'} |",
        )

    unstable = [
        c for c in summary.cells if c.confidence_low or (c.max_range_across_criteria or 0) > 0
    ]
    lines.extend(
        [
            "",
            "## Low confidence & high disagreement (cells)",
            "",
            "| Run | Cell | Scoring | N | Low conf. | max_range | σ_tot |",
            "| --- | --- | --- | ---: | --- | ---: | ---: |",
        ],
    )
    for c in sorted(unstable, key=lambda x: (x.run_id, x.cell_id))[:80]:
        n = c.judge_repeat_count if c.judge_repeat_count is not None else "—"
        lines.append(
            f"| `{c.run_id}` | `{c.cell_id}` | `{c.scoring_backend}` | {n} | "
            f"{c.confidence_low} | "
            f"{c.max_range_across_criteria if c.max_range_across_criteria is not None else '—'} | "
            f"{c.total_weighted_stdev if c.total_weighted_stdev is not None else '—'} |",
        )
    if len(unstable) > 80:
        lines.append("")
        lines.append(f"_… and {len(unstable) - 80} more unstable/low-confidence cells._")
    lines.append("")
    return "\n".join(lines)


def write_campaign_semantic_summary_artifacts(
    *,
    repo_root: Path,
    campaign_dir: Path,
    manifest: BenchmarkCampaignManifest,
) -> CampaignGeneratedReportPaths:
    """Write campaign-semantic-summary.{json,md}; return paths for generated_report_paths."""
    from agent_llm_wiki_matrix.schema import load_schema, validate_json

    _ = repo_root  # reserved for future repo-relative rewriting
    summary = build_campaign_semantic_summary(
        campaign_id=manifest.campaign_id,
        title=manifest.title,
        created_at=manifest.created_at,
        repo_root=repo_root,
        campaign_dir=campaign_dir,
        runs=manifest.runs,
    )
    data = summary.model_dump(mode="json", exclude_none=True)
    validate_json(data, load_schema("schemas/v1/campaign_semantic_summary.schema.json"))
    from agent_llm_wiki_matrix.benchmark.persistence import write_json_sorted, write_utf8_text

    write_json_sorted(campaign_dir / "campaign-semantic-summary.json", data)
    write_utf8_text(
        campaign_dir / "campaign-semantic-summary.md",
        render_campaign_semantic_summary_markdown(summary),
    )

    return CampaignGeneratedReportPaths(
        campaign_semantic_summary_json="campaign-semantic-summary.json",
        campaign_semantic_summary_md="campaign-semantic-summary.md",
    )
