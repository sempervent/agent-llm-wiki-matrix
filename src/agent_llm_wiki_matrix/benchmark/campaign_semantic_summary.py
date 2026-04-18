"""Aggregate semantic / hybrid judge variance across campaign member runs."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
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
    CampaignAxisInstabilityHighlight,
    CampaignCriterionInstabilityRow,
    CampaignGeneratedReportPaths,
    CampaignSemanticAxisRollup,
    CampaignSemanticCellRow,
    CampaignSemanticInstabilityHighlights,
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
) -> tuple[CampaignSemanticCellRow, EvaluationJudgeProvenance | None]:
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
    eval_jlc = ev.judge_low_confidence
    rep_lc = bool(ra.confidence.low_confidence) if ra is not None else False
    conf_low = bool(eval_jlc) if eval_jlc is not None else False
    conf_low = conf_low or rep_lc
    flags: list[str] = []
    if ra is not None:
        flags = list(ra.confidence.flags[:8])

    row = CampaignSemanticCellRow(
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
        judge_low_confidence=eval_jlc,
        repeat_aggregation_present=ra is not None,
        max_range_across_criteria=max_r,
        total_weighted_stdev=tw_stdev,
        mean_stdev_across_criteria=mean_st,
        confidence_low=conf_low,
        confidence_flags=flags,
        repeat_confidence_low=rep_lc,
    )
    return row, prov


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


def _build_criterion_instability(
    provenances: list[EvaluationJudgeProvenance | None],
) -> list[CampaignCriterionInstabilityRow]:
    acc: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {"sum": 0.0, "max": 0.0, "n": 0},
    )
    for prov in provenances:
        if prov is None or prov.repeat_aggregation is None:
            continue
        ra = prov.repeat_aggregation
        for cid, d in ra.disagreement.per_criterion.items():
            bucket = acc[cid]
            bucket["sum"] = float(bucket["sum"]) + float(d.score_range)
            bucket["max"] = max(float(bucket["max"]), float(d.score_range))
            bucket["n"] = int(bucket["n"]) + 1
    rows: list[CampaignCriterionInstabilityRow] = []
    for cid, v in acc.items():
        n = int(v["n"])
        s = float(v["sum"])
        mx = float(v["max"])
        rows.append(
            CampaignCriterionInstabilityRow(
                criterion_id=cid,
                cells_with_repeat_judge=n,
                sum_score_range=s,
                max_score_range=mx,
                mean_score_range=s / n if n else 0.0,
            ),
        )
    rows.sort(key=lambda x: x.sum_score_range, reverse=True)
    return rows[:40]


def _confidence_flag_counts(rows: list[CampaignSemanticCellRow]) -> dict[str, int]:
    c: Counter[str] = Counter()
    for r in rows:
        for f in r.confidence_flags:
            c[f] += 1
    return dict(sorted(c.items(), key=lambda x: (-x[1], x[0])))


def _build_instability_highlights(
    *,
    by_suite: list[CampaignSemanticAxisRollup],
    by_provider: list[CampaignSemanticAxisRollup],
    by_mode: list[CampaignSemanticAxisRollup],
    rows: list[CampaignSemanticCellRow],
    limit: int = 8,
) -> CampaignSemanticInstabilityHighlights:
    def pack(
        kind: Literal["suite_ref", "provider_config_ref", "execution_mode"],
        rollups: list[CampaignSemanticAxisRollup],
    ) -> list[CampaignAxisInstabilityHighlight]:
        ranked = _sorted_hotspots(list(rollups), limit=limit)
        out: list[CampaignAxisInstabilityHighlight] = []
        for i, a in enumerate(ranked, start=1):
            out.append(
                CampaignAxisInstabilityHighlight(
                    axis_kind=kind,
                    axis_value=a.axis_value,
                    rank=i,
                    instability_score=_rollup_hotspot_score(a),
                    cell_rows=a.cell_rows,
                    semantic_cells=a.semantic_cells,
                    repeat_judge_cells=a.repeat_judge_cells,
                    low_confidence_cells=a.low_confidence_cells,
                    max_range_observed=a.max_range_observed,
                    mean_range_across_cells=a.mean_range_across_cells,
                    mean_total_weighted_stdev=a.mean_total_weighted_stdev,
                ),
            )
        return out

    return CampaignSemanticInstabilityHighlights(
        unstable_suites=pack("suite_ref", by_suite),
        unstable_providers=pack("provider_config_ref", by_provider),
        unstable_execution_modes=pack("execution_mode", by_mode),
        confidence_flag_counts=_confidence_flag_counts(rows),
    )


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
    provenances: list[EvaluationJudgeProvenance | None] = []
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
            row, prov = _extract_cell_metrics(
                run_dir=run_dir,
                cell=cell,
                run_id=entry.run_id,
                run_index=entry.run_index,
                suite_ref=entry.suite_ref,
                provider_config_ref=entry.provider_config_ref,
                eval_scoring_label=entry.eval_scoring_label,
            )
            rows.append(row)
            provenances.append(prov)

    det = sum(1 for r in rows if r.scoring_backend == "deterministic")
    sem = sum(1 for r in rows if r.scoring_backend in ("semantic_judge", "hybrid"))
    rep = [r for r in rows if r.repeat_aggregation_present]
    low = [r for r in rows if r.confidence_low]
    ranges = [r.max_range_across_criteria for r in rep if r.max_range_across_criteria is not None]
    tws = [r.total_weighted_stdev for r in rep if r.total_weighted_stdev is not None]
    cells_jlc = sum(1 for r in rows if r.judge_low_confidence is True)
    cells_rpc = sum(1 for r in rows if r.repeat_confidence_low)

    by_suite = _rollup("suite_ref", rows)
    by_provider = _rollup("provider_config_ref", rows)
    by_mode = _rollup("execution_mode", rows)

    totals = CampaignSemanticTotals(
        runs_scanned=scanned,
        cells_total=len(rows),
        cells_deterministic=det,
        cells_semantic_or_hybrid=sem,
        cells_with_repeat_judge=len(rep),
        low_confidence_cells=len(low),
        cells_flagged_judge_low_confidence=cells_jlc,
        cells_flagged_repeat_confidence_low=cells_rpc,
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
        by_suite=by_suite,
        by_provider=by_provider,
        by_execution_mode=by_mode,
        criterion_instability=_build_criterion_instability(provenances),
        instability_highlights=_build_instability_highlights(
            by_suite=by_suite,
            by_provider=by_provider,
            by_mode=by_mode,
            rows=rows,
        ),
        cells=rows,
    )


def _rollup_hotspot_score(a: CampaignSemanticAxisRollup) -> float:
    """Higher = more judge disagreement / instability on this axis slice."""
    mr = a.mean_range_across_cells
    mx = a.max_range_observed
    candidates = [x for x in (mr, mx) if x is not None]
    return max(candidates) if candidates else -1.0


def _sorted_hotspots(
    rollups: list[CampaignSemanticAxisRollup],
    *,
    limit: int = 8,
) -> list[CampaignSemanticAxisRollup]:
    return sorted(
        rollups,
        key=lambda x: (_rollup_hotspot_score(x), x.axis_value),
        reverse=True,
    )[:limit]


def render_campaign_semantic_judge_section_markdown(summary: CampaignSemanticSummaryV1) -> str:
    """Short block for embedding in ``campaign-report.md`` (comparative narrative)."""
    t = summary.totals
    ih = summary.instability_highlights
    lines = [
        "## Judge variance (abbreviated)",
        "",
        "_Full tables: `campaign-semantic-summary.md`._",
        "",
        "| Signal | Count |",
        "| --- | ---: |",
        f"| Low-confidence (merged) | {t.low_confidence_cells} |",
        f"| `judge_low_confidence` | {t.cells_flagged_judge_low_confidence} |",
        f"| repeat `confidence.low_confidence` | {t.cells_flagged_repeat_confidence_low} |",
        f"| Repeat-judge cells (N>1) | {t.cells_with_repeat_judge} |",
        f"| Max range (campaign) | "
        f"{t.max_range_across_campaign if t.max_range_across_campaign is not None else '—'} |",
        "",
    ]
    if ih.confidence_flag_counts:
        lines.extend(["### Threshold flags", "", "| Flag | Cells |", "| --- | ---: |"])
        for fk, fv in list(ih.confidence_flag_counts.items())[:12]:
            lines.append(f"| `{fk}` | {fv} |")
        lines.append("")
    if summary.criterion_instability:
        lines.extend(
            [
                "### Top criteria (Σ score_range)",
                "",
                "| Criterion | Repeat cells | Σ range | Max range | Mean range |",
                "| --- | ---: | ---: | ---: | ---: |",
            ],
        )
        for c in summary.criterion_instability[:8]:
            lines.append(
                f"| `{c.criterion_id}` | {c.cells_with_repeat_judge} | "
                f"{c.sum_score_range:.6f} | {c.max_score_range:.6f} | {c.mean_score_range:.6f} |",
            )
        lines.append("")
    for title, block in (
        ("### Suites", ih.unstable_suites),
        ("### Provider axis", ih.unstable_providers),
        ("### Execution modes", ih.unstable_execution_modes),
    ):
        lines.extend(
            [
                title,
                "",
                "| # | Axis | Instability | Low-conf. | Repeat cells | mean_range | max_range |",
                "| ---: | --- | ---: | ---: | ---: | ---: | ---: |",
            ],
        )
        for h in block[:6]:
            mr = h.mean_range_across_cells
            mx = h.max_range_observed
            lines.append(
                f"| {h.rank} | `{h.axis_value}` | {h.instability_score:.6f} | "
                f"{h.low_confidence_cells} | {h.repeat_judge_cells} | "
                f"{mr if mr is not None else '—'} | {mx if mx is not None else '—'} |",
            )
        lines.append("")
    lines.append("")
    return "\n".join(lines)


def render_campaign_semantic_summary_markdown(summary: CampaignSemanticSummaryV1) -> str:
    """Markdown view: totals, low-confidence highlights, rollups by suite/provider/mode."""
    t = summary.totals
    mrc = t.max_range_across_campaign
    mrr = t.mean_range_repeat_cells
    mtw = t.mean_total_weighted_stdev_repeat
    ih = summary.instability_highlights
    lines = [
        "# Campaign semantic summary",
        "",
        f"- **Campaign:** `{summary.campaign_id}`",
        f"- **Title:** {summary.title}",
        f"- **Created:** `{summary.created_at}`",
        "",
        "Semantic / hybrid judge rollups from member **evaluation** artifacts (deterministic "
        "cells counted, no spread). Cross-link: **`campaign-summary.md`**, "
        "**`reports/campaign-report.md`**.",
        "",
        "## Executive snapshot",
        "",
        "| Signal | Count |",
        "| --- | ---: |",
        f"| Runs scanned | {t.runs_scanned} |",
        f"| Cells total | {t.cells_total} |",
        f"| Low-confidence (merged) | {t.low_confidence_cells} |",
        "| `judge_low_confidence` | "
        f"{t.cells_flagged_judge_low_confidence} |",
        "| repeat `confidence.low_confidence` | "
        f"{t.cells_flagged_repeat_confidence_low} |",
        f"| Repeat-judge cells (N>1) | {t.cells_with_repeat_judge} |",
        f"| Semantic / hybrid cells | {t.cells_semantic_or_hybrid} |",
        f"| Deterministic cells | {t.cells_deterministic} |",
        f"| Max range (campaign) | {mrc if mrc is not None else '—'} |",
        f"| Mean range (repeat cells) | {mrr if mrr is not None else '—'} |",
        f"| Mean σ total (repeat cells) | {mtw if mtw is not None else '—'} |",
        "",
    ]
    if ih.confidence_flag_counts:
        lines.extend(
            [
                "### Repeat-judge threshold flags",
                "",
                "| Flag | Cells |",
                "| --- | ---: |",
            ],
        )
        for fk, fv in ih.confidence_flag_counts.items():
            lines.append(f"| `{fk}` | {fv} |")
        lines.append("")
    if summary.criterion_instability:
        lines.extend(
            [
                "### Criteria (Σ score_range)",
                "",
                "| Criterion | Repeat cells | Σ range | Max range | Mean range |",
                "| --- | ---: | ---: | ---: | ---: |",
            ],
        )
        for crit in summary.criterion_instability[:20]:
            sr = crit.sum_score_range
            xr = crit.max_score_range
            mr = crit.mean_score_range
            lines.append(
                f"| `{crit.criterion_id}` | {crit.cells_with_repeat_judge} | "
                f"{sr:.6f} | {xr:.6f} | {mr:.6f} |",
            )
        lines.append("")
    lines.extend(
        [
            "## Instability hotspots",
            "",
            "Ranked by **`mean_range_across_cells`** and **`max_range_observed`** "
            "(repeat-judge cells).",
            "",
        ],
    )
    if t.cells_semantic_or_hybrid > 0:
        lines.extend(
            [
                "### By suite",
                "",
                "| Rank | Suite | Mean range | Max range | Low-conf. cells |",
                "| ---: | --- | ---: | ---: | ---: |",
            ],
        )
        for i, a in enumerate(_sorted_hotspots(list(summary.by_suite)), start=1):
            lines.append(
                f"| {i} | `{a.axis_value}` | "
                f"{a.mean_range_across_cells if a.mean_range_across_cells is not None else '—'} | "
                f"{a.max_range_observed if a.max_range_observed is not None else '—'} | "
                f"{a.low_confidence_cells} |",
            )
        lines.extend(
            [
                "",
                "### By provider axis",
                "",
                "| Rank | Provider | Mean range | Max range | Low-conf. cells |",
                "| ---: | --- | ---: | ---: | ---: |",
            ],
        )
        for i, a in enumerate(_sorted_hotspots(list(summary.by_provider)), start=1):
            lines.append(
                f"| {i} | `{a.axis_value}` | "
                f"{a.mean_range_across_cells if a.mean_range_across_cells is not None else '—'} | "
                f"{a.max_range_observed if a.max_range_observed is not None else '—'} | "
                f"{a.low_confidence_cells} |",
            )
        lines.extend(
            [
                "",
                "### By execution mode",
                "",
                "| Rank | Mode | Mean range | Max range | Low-conf. cells |",
                "| ---: | --- | ---: | ---: | ---: |",
            ],
        )
        for i, a in enumerate(_sorted_hotspots(list(summary.by_execution_mode)), start=1):
            lines.append(
                f"| {i} | `{a.axis_value}` | "
                f"{a.mean_range_across_cells if a.mean_range_across_cells is not None else '—'} | "
                f"{a.max_range_observed if a.max_range_observed is not None else '—'} | "
                f"{a.low_confidence_cells} |",
            )
        lines.append("")
    else:
        lines.extend(
            [
                "_No semantic / hybrid cells — hotspots apply when `eval_scoring.backend` is "
                "semantic or hybrid with repeat judges._",
                "",
            ],
        )
    lines.extend(
        [
            "## Detailed rollups by suite",
            "",
            (
                "| Suite | Cells | Semantic | Repeat judge | Low conf. | "
                "Max range | Mean range | Mean σ_tot |"
            ),
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ],
    )
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
            "## Detailed rollups by provider config",
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
            "## Detailed rollups by execution mode",
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
            "| Run | Cell | Scoring | N | j_lc | r_cf | merged | flags | max_r | σ_tot |",
            "| --- | --- | --- | ---: | --- | --- | --- | --- | ---: | ---: |",
        ],
    )
    for row in sorted(unstable, key=lambda x: (x.run_id, x.cell_id))[:80]:
        n = row.judge_repeat_count if row.judge_repeat_count is not None else "—"
        fl = ", ".join(row.confidence_flags[:3]) if row.confidence_flags else "—"
        jlc = row.judge_low_confidence if row.judge_low_confidence is not None else "—"
        mx = row.max_range_across_criteria
        tw = row.total_weighted_stdev
        lines.append(
            f"| `{row.run_id}` | `{row.cell_id}` | `{row.scoring_backend}` | {n} | {jlc} | "
            f"{row.repeat_confidence_low} | {row.confidence_low} | {fl} | "
            f"{mx if mx is not None else '—'} | {tw if tw is not None else '—'} |",
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
) -> tuple[CampaignGeneratedReportPaths, CampaignSemanticSummaryV1]:
    """Write campaign-semantic-summary.{json,md}; return paths and the summary model."""
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

    return (
        CampaignGeneratedReportPaths(
            campaign_semantic_summary_json="campaign-semantic-summary.json",
            campaign_semantic_summary_md="campaign-semantic-summary.md",
        ),
        summary,
    )
