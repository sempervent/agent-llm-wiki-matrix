"""Campaign-level comparative reports (Markdown + JSON) from member benchmark runs.

Reuses :func:`analyze_longitudinal` and failure-tag taxonomy from ``pipelines.longitudinal``.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent_llm_wiki_matrix.benchmark.campaign_browser_evidence import (
    campaign_browser_evidence_json_rows,
    render_campaign_browser_evidence_markdown,
)
from agent_llm_wiki_matrix.benchmark.campaign_fingerprint_compare import (
    build_fingerprint_axis_groups,
    build_fingerprint_axis_insights,
    build_fingerprint_axis_interpretation,
    fingerprint_compare_to_json,
    render_fingerprint_compare_markdown,
)
from agent_llm_wiki_matrix.benchmark.campaign_semantic_summary import (
    render_campaign_semantic_judge_section_markdown,
)
from agent_llm_wiki_matrix.benchmark.persistence import write_json_sorted, write_utf8_text
from agent_llm_wiki_matrix.models import (
    BenchmarkCampaignManifest,
    BenchmarkCampaignRunEntry,
    CampaignGeneratedReportPaths,
    CampaignSemanticSummaryV1,
)
from agent_llm_wiki_matrix.pipelines.longitudinal import (
    FAILURE_TAXONOMY,
    LongitudinalAnalysis,
    RunSnapshot,
    analyze_longitudinal,
    load_run_snapshots,
    render_failure_atlas,
)

# Defaults aligned with ``alwm benchmark longitudinal`` CLI for deterministic CI.
_DEFAULT_REGRESSION_DELTA = 0.03
_DEFAULT_LOW_SCORE = 0.55
_DEFAULT_MIN_RECURRING = 2
_DEFAULT_MODE_GAP = 0.12
_DEFAULT_SEMANTIC_STDEV = 0.12
_DEFAULT_SEMANTIC_RANGE = 0.22
_DEFAULT_SERIES_SWING = 0.06
_DEFAULT_MIN_RUNS_SWING = 3


@dataclass(frozen=True)
class BackendMeanRow:
    """Mean cell score aggregated by ``backend_kind`` across member runs."""

    backend_kind: str
    mean_score: float
    cell_count: int


@dataclass(frozen=True)
class MemberMeanByAxisValue:
    """Mean of member-run ``mean_total_weighted_score`` for one sweep value."""

    axis_value: str
    run_count: int
    mean_member_score: float


def _execution_mode_filter_label(r: BenchmarkCampaignRunEntry) -> str:
    if r.execution_modes_filter:
        return ",".join(r.execution_modes_filter)
    return "—"


def _provider_label(ref: str | None) -> str:
    return ref if ref is not None else "null (harness default)"


def rollup_member_mean_scores_by_dimension(
    manifest: BenchmarkCampaignManifest,
) -> dict[str, list[MemberMeanByAxisValue]]:
    """Group succeeded runs with scores by each campaign axis; mean of run-level means per value."""
    runs = [
        r
        for r in manifest.runs
        if r.status == "succeeded" and r.mean_total_weighted_score is not None
    ]
    if not runs:
        return {}

    def bucket(
        key_fn: Callable[[BenchmarkCampaignRunEntry], str],
    ) -> list[MemberMeanByAxisValue]:
        by_val: dict[str, list[float]] = defaultdict(list)
        for r in runs:
            mscore = r.mean_total_weighted_score
            assert mscore is not None
            by_val[key_fn(r)].append(mscore)
        out: list[MemberMeanByAxisValue] = []
        for axis_value in sorted(by_val.keys()):
            vals = by_val[axis_value]
            out.append(
                MemberMeanByAxisValue(
                    axis_value=axis_value,
                    run_count=len(vals),
                    mean_member_score=sum(vals) / len(vals),
                ),
            )
        return sorted(out, key=lambda x: (-x.mean_member_score, x.axis_value))

    return {
        "suite_ref": bucket(lambda r: r.suite_ref),
        "benchmark_id": bucket(lambda r: r.benchmark_id),
        "provider_config_ref": bucket(lambda r: _provider_label(r.provider_config_ref)),
        "eval_scoring_label": bucket(lambda r: r.eval_scoring_label),
        "execution_modes_filter": bucket(_execution_mode_filter_label),
        "browser_config_applied": bucket(lambda r: "true" if r.browser_config_applied else "false"),
    }


def _best_worst_member_means(
    rows: Sequence[MemberMeanByAxisValue],
) -> tuple[MemberMeanByAxisValue | None, MemberMeanByAxisValue | None]:
    if len(rows) < 2:
        return (rows[0] if rows else None, None)
    hi = max(rows, key=lambda x: (x.mean_member_score, -x.run_count, x.axis_value))
    lo = min(rows, key=lambda x: (x.mean_member_score, x.run_count, x.axis_value))
    return (hi, lo)


def _manifest_paths_for_succeeded_runs(
    output_dir: Path,
    manifest: BenchmarkCampaignManifest,
) -> list[Path]:
    out: list[Path] = []
    for row in manifest.runs:
        if row.status != "succeeded":
            continue
        p = output_dir / row.manifest_relpath
        if p.is_file():
            out.append(p)
    return sorted(out, key=lambda x: str(x))


def suite_ref_benchmark_id_partition_coincide(
    manifest: BenchmarkCampaignManifest,
) -> bool:
    """True when ``suite_ref`` and ``benchmark_id`` induce the same partition of runs.

    Then the two axes carry the same sweep signal; Markdown summaries list ``suite_ref``
    only to avoid redundant emphasis. JSON rollups are unchanged.
    """
    runs = manifest.runs
    if len(runs) < 2:
        return False
    suites = {r.suite_ref for r in runs}
    benches = {r.benchmark_id for r in runs}
    if len(suites) <= 1 or len(benches) <= 1:
        return False
    for i, a in enumerate(runs):
        for b in runs[i + 1 :]:
            if (a.suite_ref == b.suite_ref) != (a.benchmark_id == b.benchmark_id):
                return False
    return True


def _markdown_sweep_axis_keys(
    axis_keys: Sequence[str],
    manifest: BenchmarkCampaignManifest,
) -> list[str]:
    """Drop ``benchmark_id`` from ordered axis names when it duplicates ``suite_ref``."""
    keys = list(axis_keys)
    if suite_ref_benchmark_id_partition_coincide(manifest):
        return [k for k in keys if k != "benchmark_id"]
    return keys


def summarize_campaign_dimensions(manifest: BenchmarkCampaignManifest) -> dict[str, Any]:
    """Which sweep dimensions took more than one distinct value (comparative axes)."""
    runs = manifest.runs
    suites = sorted({r.suite_ref for r in runs})
    benchmarks = sorted({r.benchmark_id for r in runs})
    providers = sorted(
        {r.provider_config_ref for r in runs},
        key=lambda x: (x is None, str(x)),
    )
    eval_labels = sorted({r.eval_scoring_label for r in runs})
    mode_filters: list[str] = []
    for r in runs:
        if r.execution_modes_filter:
            mode_filters.append(",".join(r.execution_modes_filter))
        else:
            mode_filters.append("—")
    mode_distinct = sorted(set(mode_filters))
    browser_flags = sorted({r.browser_config_applied for r in runs})

    def varied(name: str, values: Sequence[Any], display: list[str]) -> dict[str, Any]:
        return {
            "axis": name,
            "distinct_count": len(set(values)),
            "values": display,
            "varied": len(set(values)) > 1,
        }

    return {
        "suite_ref": varied("suite_ref", suites, list(suites)),
        "benchmark_id": varied("benchmark_id", benchmarks, list(benchmarks)),
        "provider_config_ref": varied(
            "provider_config_ref",
            [r.provider_config_ref for r in runs],
            [str(p) if p is not None else "null (harness default)" for p in providers],
        ),
        "eval_scoring_label": varied("eval_scoring_label", eval_labels, list(eval_labels)),
        "execution_modes_filter": varied("execution_modes_filter", mode_filters, mode_distinct),
        "browser_config_applied": varied(
            "browser_config_applied",
            [r.browser_config_applied for r in runs],
            [str(x) for x in browser_flags],
        ),
    }


def aggregate_backend_performance(snapshots: Sequence[RunSnapshot]) -> list[BackendMeanRow]:
    """Best-effort mean of cell ``total_score`` by ``backend_kind`` (cross-run)."""
    by_kind: dict[str, list[float]] = defaultdict(list)
    for s in snapshots:
        for c in s.cells:
            by_kind[c.backend_kind].append(c.total_score)
    rows: list[BackendMeanRow] = []
    for kind in sorted(by_kind.keys()):
        vals = by_kind[kind]
        rows.append(
            BackendMeanRow(
                backend_kind=kind,
                mean_score=sum(vals) / len(vals),
                cell_count=len(vals),
            ),
        )
    return sorted(rows, key=lambda r: (-r.mean_score, r.backend_kind))


def count_semantic_instability_by_scoring_backend(
    analysis: LongitudinalAnalysis,
) -> list[tuple[str, int]]:
    """Count unstable cells from ``semantic_stability``, keyed by ``scoring_backend``."""
    counts: dict[str, int] = defaultdict(int)
    snap_by_id = {s.run_id: s for s in analysis.snapshots}
    for row in analysis.semantic_stability:
        s = snap_by_id.get(row.run_id)
        if s is None:
            continue
        for c in s.cells:
            if c.cell_id == row.cell_id:
                counts[c.scoring_backend] += 1
                break
    return sorted(counts.items(), key=lambda x: (-x[1], x[0]))


def count_failure_tags(analysis: LongitudinalAnalysis) -> list[tuple[str, int]]:
    """Descending frequency of FT-* codes (signal count = len of tag list)."""
    out: list[tuple[str, int]] = []
    for code in sorted(analysis.failure_tags.keys()):
        n = len(analysis.failure_tags[code])
        if n:
            out.append((code, n))
    out.sort(key=lambda x: (-x[1], x[0]))
    return out


def mean_score_extremes_by_sweep_axis(
    manifest: BenchmarkCampaignManifest,
) -> dict[str, Any]:
    """Best / worst mean member score per sweep axis when at least two runs have scores."""
    roll = rollup_member_mean_scores_by_dimension(manifest)
    rows = [
        r
        for r in manifest.runs
        if r.status == "succeeded" and r.mean_total_weighted_score is not None
    ]
    out: dict[str, Any] = {"member_runs_with_scores": len(rows)}
    if len(rows) < 2:
        out["comparable"] = False
        out["note"] = "Need at least two succeeded member runs with mean scores to compare axes."
        return out

    out["comparable"] = True
    out["axes"] = {}
    for axis_key in sorted(roll.keys()):
        buckets = roll[axis_key]
        if len(buckets) < 2:
            out["axes"][axis_key] = {
                "varied": False,
                "distinct_values": len(buckets),
                "note": "Single distinct value on this axis — no best/worst spread.",
            }
            continue
        hi, lo = _best_worst_member_means(buckets)
        assert hi is not None and lo is not None
        out["axes"][axis_key] = {
            "varied": True,
            "distinct_values": len(buckets),
            "best": {
                "label": hi.axis_value,
                "mean_score": round(hi.mean_member_score, 6),
                "run_count": hi.run_count,
            },
            "worst": {
                "label": lo.axis_value,
                "mean_score": round(lo.mean_member_score, 6),
                "run_count": lo.run_count,
            },
            "spread": round(hi.mean_member_score - lo.mean_member_score, 6),
        }
    return out


def member_mean_score_dimension_to_json(
    manifest: BenchmarkCampaignManifest,
) -> dict[str, Any]:
    """Structured rollups for ``campaign-analysis.json`` (mirrors member-run score tables)."""
    roll = rollup_member_mean_scores_by_dimension(manifest)
    ext = mean_score_extremes_by_sweep_axis(manifest)
    axes_out: dict[str, Any] = {}
    for axis_key in sorted(roll.keys()):
        rows = roll[axis_key]
        values = [
            {
                "axis_value": r.axis_value,
                "run_count": r.run_count,
                "mean_member_score": round(r.mean_member_score, 6),
            }
            for r in rows
        ]
        ax_block = ext.get("axes", {}).get(axis_key) if ext.get("comparable") else None
        entry: dict[str, Any] = {
            "values": values,
        }
        if isinstance(ax_block, dict) and ax_block.get("varied"):
            entry["best"] = ax_block.get("best")
            entry["worst"] = ax_block.get("worst")
            entry["spread"] = ax_block.get("spread")
        else:
            entry["comparable_across_values"] = False
        axes_out[axis_key] = entry
    return axes_out


def render_comparative_executive_markdown(
    manifest: BenchmarkCampaignManifest,
    snapshots: list[RunSnapshot],
    analysis: LongitudinalAnalysis,
) -> str:
    """Top-of-report digest: dimensions, score extremes, backends, instability, gaps, FT-*."""
    dim = summarize_campaign_dimensions(manifest)
    varied = sorted(k for k, v in dim.items() if isinstance(v, dict) and v.get("varied"))
    coincide = suite_ref_benchmark_id_partition_coincide(manifest)
    varied_md = _markdown_sweep_axis_keys(varied, manifest)
    ext = mean_score_extremes_by_sweep_axis(manifest)
    lines = [
        "## At a glance",
        "",
    ]
    if varied_md:
        ax_line = ", ".join(f"`{a}`" for a in varied_md)
        lines.append(f"- **Varied sweep axes:** {ax_line}.")
        if coincide:
            lines.append(
                "- _Note:_ `suite_ref` and `benchmark_id` sweep together — "
                "member scores by benchmark are the same grouping as by suite.",
            )
    else:
        lines.append(
            "- **Varied sweep axes:** _none — single configuration path in this campaign._",
        )

    if ext.get("comparable"):
        lines.extend(["", "### Mean member score — best / worst by axis", ""])
        axes_block = ext.get("axes") or {}
        for axis_name in _markdown_sweep_axis_keys(sorted(axes_block.keys()), manifest):
            block = axes_block[axis_name]
            if not isinstance(block, dict):
                continue
            if not block.get("varied"):
                lines.append(
                    f"- **`{axis_name}`:** _not comparable_ — {block.get('note', 'single value')}",
                )
                continue
            b, w = block["best"], block["worst"]
            lines.append(
                f"- **`{axis_name}`:** best `{b['label']}` ({b['mean_score']:.6f}, "
                f"n={b['run_count']}), worst `{w['label']}` ({w['mean_score']:.6f}, "
                f"n={w['run_count']}), spread **{block['spread']:.6f}**",
            )
    else:
        lines.extend(
            [
                "",
                "### Mean member score — best / worst by axis",
                "",
                f"- _{ext.get('note', 'Not enough scored member runs.')}_",
            ],
        )

    backs = aggregate_backend_performance(snapshots)
    lines.extend(["", "### Backend (mean cell score across the campaign)", ""])
    if not backs:
        lines.append("_No cells in member manifests._")
    else:
        best_b, worst_b = backs[0], backs[-1]
        lines.append(
            f"- **Best:** `{best_b.backend_kind}` ({best_b.mean_score:.6f} "
            f"over {best_b.cell_count} cells)",
        )
        if len(backs) > 1:
            lines.append(
                f"- **Weakest:** `{worst_b.backend_kind}` ({worst_b.mean_score:.6f} "
                f"over {worst_b.cell_count} cells)",
            )
        else:
            lines.append("- **Weakest:** _only one backend kind present._")

    su = count_semantic_instability_by_scoring_backend(analysis)
    total_unstable = sum(n for _, n in su)
    lines.extend(["", "### Semantic / hybrid instability (longitudinal)", ""])
    if not su:
        lines.append(
            "_No cells flagged as semantically unstable at configured thresholds._",
        )
    else:
        top_sb, top_n = su[0]
        lines.append(
            f"- **Hotspot scoring_backend:** `{top_sb}` ({top_n} unstable cell event(s); "
            f"**{total_unstable}** total across backends).",
        )
        if len(su) > 1:
            rest = ", ".join(f"`{k}`×{n}" for k, n in su[1:6])
            lines.append(f"- **Also:** {rest}")

    mode_rows = top_mode_gap_rows(analysis, limit=5)
    lines.extend(["", "### Execution mode gaps (within-run)", ""])
    if not analysis.mode_gaps:
        lines.append(
            "_No mode-gap rows above threshold (or modes not comparable in member runs)._",
        )
    else:
        thr = _DEFAULT_MODE_GAP
        lines.append(
            f"- **Signals:** {len(analysis.mode_gaps)} row(s) at threshold ≥ {thr:g}.",
        )
        r0 = mode_rows[0]
        modes_s = ", ".join(f"{m}={r0.by_mode[m]:.4f}" for m in sorted(r0.by_mode.keys()))
        lines.append(
            f"- **Largest spread:** **{r0.spread:.4f}** on `{r0.run_id}` / "
            f"`{r0.prompt_id}` ({modes_s}).",
        )

    ranked = count_failure_tags(analysis)
    lines.extend(["", "### Top recurring failure tags (FT-*)", ""])
    if not ranked:
        lines.append("_No FT-* signals in this pass._")
    else:
        top5 = ranked[:5]
        parts = [f"`{c}`×{n}" for c, n in top5]
        lines.append("- " + ", ".join(parts))
        if len(ranked) > 5:
            lines.append(f"- _… and {len(ranked) - 5} more code(s) in the table below._")
    lines.append("")
    return "\n".join(lines)


def render_member_mean_score_tables_markdown(manifest: BenchmarkCampaignManifest) -> str:
    """One table per axis with multiple distinct values (member-run mean scores)."""
    roll = rollup_member_mean_scores_by_dimension(manifest)
    coincide = suite_ref_benchmark_id_partition_coincide(manifest)
    lines: list[str] = [
        "## Member-run mean score by sweep value",
        "",
        "Each row is the mean of **mean_total_weighted_score** for member runs at that sweep "
        "value (equal weight per run). Only axes with **more than one** distinct value are shown.",
        "",
    ]
    any_table = False
    for axis_key in sorted(roll.keys()):
        if coincide and axis_key == "benchmark_id":
            continue
        rows = roll[axis_key]
        if len(rows) < 2:
            continue
        any_table = True
        lines.append(f"### `{axis_key}`")
        lines.append("")
        lines.append("| Value | Runs | Mean member score |")
        lines.append("| --- | ---: | ---: |")
        for r in sorted(rows, key=lambda x: (-x.mean_member_score, x.axis_value)):
            safe = r.axis_value.replace("|", "\\|")
            lines.append(
                f"| `{safe}` | {r.run_count} | {r.mean_member_score:.6f} |",
            )
        lines.append("")
    if not any_table:
        lines.append("_No axis had more than one distinct value among runs with scores._")
        lines.append("")
    return "\n".join(lines)


def load_longitudinal_bundle_for_campaign(
    repo_root: Path,
    output_dir: Path,
    manifest: BenchmarkCampaignManifest,
) -> tuple[list[RunSnapshot], LongitudinalAnalysis] | None:
    """Reload member snapshots and analysis (same thresholds as comparative artifacts)."""
    paths = _manifest_paths_for_succeeded_runs(output_dir, manifest)
    if not paths:
        return None
    repo_root = repo_root.resolve()
    snaps = load_run_snapshots(repo_root, paths)
    analysis = analyze_longitudinal(
        snaps,
        regression_delta=_DEFAULT_REGRESSION_DELTA,
        low_score=_DEFAULT_LOW_SCORE,
        min_recurring=_DEFAULT_MIN_RECURRING,
        mode_gap_threshold=_DEFAULT_MODE_GAP,
        semantic_stdev_threshold=_DEFAULT_SEMANTIC_STDEV,
        semantic_range_threshold=_DEFAULT_SEMANTIC_RANGE,
        series_swing_threshold=_DEFAULT_SERIES_SWING,
        min_runs_for_swing=_DEFAULT_MIN_RUNS_SWING,
    )
    return snaps, analysis


def render_campaign_at_a_glance_markdown(
    manifest: BenchmarkCampaignManifest,
    *,
    longitudinal_bundle: tuple[list[RunSnapshot], LongitudinalAnalysis] | None = None,
    semantic_summary: CampaignSemanticSummaryV1 | None = None,
) -> str:
    """Readable digest for campaign-summary.md: spreads, hotspots, gaps, tags."""
    lines = [
        "## At a glance",
        "",
        "Mean-score spreads, backends, semantic instability, mode gaps, and **FT-*** tags. "
        "Details: **`reports/campaign-report.md`**; judge variance: "
        "**`campaign-semantic-summary.md`**.",
        "",
    ]
    if manifest.dry_run:
        lines.extend(["_Dry run — no member runs executed._", ""])
        return "\n".join(lines)

    ext = mean_score_extremes_by_sweep_axis(manifest)
    coincide = suite_ref_benchmark_id_partition_coincide(manifest)
    lines.extend(["### Mean score — best / worst by sweep axis", ""])
    if not ext.get("comparable"):
        lines.append(f"- {ext.get('note', 'Not enough runs to compare.')}")
    else:
        axes = ext.get("axes") or {}
        for axis_name in _markdown_sweep_axis_keys(sorted(axes.keys()), manifest):
            block = axes.get(axis_name)
            if not isinstance(block, dict):
                continue
            if not block.get("varied"):
                lines.append(
                    f"- **`{axis_name}`:** {block.get('note', 'not varied')}",
                )
                continue
            b, w = block["best"], block["worst"]
            lines.append(
                f"- **`{axis_name}`:** best `{b['label']}` ({b['mean_score']:.6f}), "
                f"worst `{w['label']}` ({w['mean_score']:.6f}), spread **{block['spread']:.6f}**",
            )
    if coincide:
        lines.append(
            "_`benchmark_id` tracks `suite_ref` here (same grouping); see comparative report "
            "for the full dimension table._",
        )
    lines.append("")

    snaps: list[RunSnapshot] = []
    analysis: LongitudinalAnalysis | None = None
    if longitudinal_bundle is not None:
        snaps, analysis = longitudinal_bundle

    lines.extend(["### Provider / backend (mean cell score)", ""])
    if not snaps:
        lines.append("_No longitudinal bundle — run comparative report after member successes._")
    else:
        backs = aggregate_backend_performance(snaps)
        if not backs:
            lines.append("_No cells in member runs._")
        else:
            best_b, worst_b = backs[0], backs[-1]
            lines.append(
                f"- **Best:** `{best_b.backend_kind}` ({best_b.mean_score:.6f} "
                f"over {best_b.cell_count} cells)",
            )
            if len(backs) > 1:
                lines.append(
                    f"- **Weakest:** `{worst_b.backend_kind}` ({worst_b.mean_score:.6f} "
                    f"over {worst_b.cell_count} cells)",
                )
            else:
                lines.append("- **Weakest:** _single backend kind in this campaign._")
    lines.append("")

    lines.extend(["### Semantic instability hotspots (longitudinal)", ""])
    if analysis is None:
        lines.append("_Not computed (no succeeded member manifests or analysis skipped)._")
    else:
        su = count_semantic_instability_by_scoring_backend(analysis)
        if not su:
            lines.append("_No cells flagged as semantically unstable at configured thresholds._")
        else:
            for sb, n in su[:8]:
                lines.append(f"- **`{sb}`:** {n} unstable cell event(s)")
    lines.append("")

    lines.extend(["### Execution mode gaps (within-run)", ""])
    if analysis is None or not analysis.mode_gaps:
        lines.append(
            "_No mode-gap rows above threshold, or modes not comparable in member runs._",
        )
    else:
        for r in top_mode_gap_rows(analysis, limit=5):
            modes_s = ", ".join(f"{m}={r.by_mode[m]:.4f}" for m in sorted(r.by_mode.keys()))
            lines.append(
                f"- **`{r.run_id}`** / `{r.prompt_id}` — spread **{r.spread:.4f}** ({modes_s})",
            )
    lines.append("")

    lines.extend(["### Top recurring failure tags (FT-*)", ""])
    if analysis is None:
        lines.append("_No longitudinal analysis._")
    else:
        ranked = count_failure_tags(analysis)
        if not ranked:
            lines.append("_No FT-* signals in this pass._")
        else:
            top = ranked[:8]
            parts = [f"`{c}`×{n}" for c, n in top]
            lines.append("- " + ", ".join(parts))
            if len(ranked) > 8:
                rest_n = len(ranked) - 8
                lines.append(
                    f"- _… +{rest_n} more (see taxonomy in `reports/campaign-report.md`)._",
                )
    lines.append("")

    lines.extend(["### Judge confidence & repeat disagreement (rollup)", ""])
    if semantic_summary is None:
        lines.append("_No semantic summary artifact — run campaign with member manifests._")
    else:
        tot = semantic_summary.totals
        _mrc = tot.max_range_across_campaign
        _max_range_disp = _mrc if _mrc is not None else "—"
        lines.extend(
            [
                f"- **Low-confidence (merged):** {tot.low_confidence_cells} — "
                f"judge {tot.cells_flagged_judge_low_confidence}, "
                f"repeat {tot.cells_flagged_repeat_confidence_low}",
                f"- **Repeat-judge cells (N>1):** {tot.cells_with_repeat_judge}; "
                f"**max range:** {_max_range_disp}",
                "",
            ],
        )
        ih = semantic_summary.instability_highlights
        cf_items = list(ih.confidence_flag_counts.items())
        if cf_items:
            fk, fv = cf_items[0]
            lines.append(
                f"- **Top threshold flag:** `{fk}` ({fv} cell(s))",
            )
        if semantic_summary.criterion_instability:
            c0 = semantic_summary.criterion_instability[0]
            lines.append(
                f"- **Top unstable criterion (by Σ score_range):** `{c0.criterion_id}` "
                f"(Σ={c0.sum_score_range:.6f})",
            )
        lines.append("")
    lines.extend(["### Semantic / hybrid judge — axis hotspots (rollup)", ""])
    if semantic_summary is None:
        lines.append("_No semantic summary artifact (see campaign-semantic-summary when present)._")
    elif semantic_summary.totals.cells_semantic_or_hybrid == 0:
        lines.append("_All cells used deterministic scoring — no judge variance rollups._")
    else:

        def _hot_table(
            title: str,
            rollups: Sequence[Any],
            primary: str,
            fallback: str,
        ) -> None:
            def _rank(x: Any) -> tuple[float, float]:
                p = getattr(x, primary, None)
                f = getattr(x, fallback, None)
                return (
                    float(p) if p is not None else -1.0,
                    float(f) if f is not None else -1.0,
                )

            def _hot_score(x: Any) -> float:
                a, b = _rank(x)
                return max(a, b) if max(a, b) >= 0 else -1.0

            ranked = sorted(
                rollups,
                key=lambda x: (_hot_score(x), x.axis_value),
                reverse=True,
            )
            lines.append(
                f"**{title}** (ranked by `{primary}`, then `{fallback}`):",
            )
            if not rollups:
                lines.append("- _No rollup rows._")
            else:
                for x in ranked[:5]:
                    pr, fb = _rank(x)
                    pr_s = f"{pr:.6f}" if pr >= 0 else "—"
                    fb_s = f"{fb:.6f}" if fb >= 0 else "—"
                    lines.append(
                        f"- `{x.axis_value}` — mean_range={pr_s}, max_range={fb_s} "
                        f"(low-conf.: {x.low_confidence_cells})",
                    )
            lines.append("")

        _hot_table(
            "By suite",
            semantic_summary.by_suite,
            "mean_range_across_cells",
            "max_range_observed",
        )
        _hot_table(
            "By provider axis",
            semantic_summary.by_provider,
            "mean_range_across_cells",
            "max_range_observed",
        )
        _hot_table(
            "By execution mode",
            semantic_summary.by_execution_mode,
            "mean_range_across_cells",
            "max_range_observed",
        )

    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def top_mode_gap_rows(
    analysis: LongitudinalAnalysis,
    *,
    limit: int = 20,
) -> list[Any]:
    """Largest execution-mode spreads within a run (same prompt, multiple modes)."""
    rows = sorted(
        analysis.mode_gaps,
        key=lambda r: (-r.spread, r.run_id, r.prompt_id),
    )
    return rows[:limit]


def build_campaign_analysis_dict(
    manifest: BenchmarkCampaignManifest,
    snapshots: list[RunSnapshot],
    analysis: LongitudinalAnalysis,
    *,
    campaign_dir: Path | None = None,
    semantic_summary: CampaignSemanticSummaryV1 | None = None,
) -> dict[str, Any]:
    """Structured mirror of the Markdown report (deterministic key order via JSON dump)."""
    dimensions = summarize_campaign_dimensions(manifest)
    varied_axes = [k for k, v in dimensions.items() if isinstance(v, dict) and v.get("varied")]
    backends = aggregate_backend_performance(snapshots)
    scoring_unstable = count_semantic_instability_by_scoring_backend(analysis)
    failure_rank = count_failure_tags(analysis)
    mode_top = top_mode_gap_rows(analysis)

    fp_rows = build_fingerprint_axis_groups(snapshots, analysis)
    fp_insights = build_fingerprint_axis_insights(snapshots, analysis)
    fp_interp = build_fingerprint_axis_interpretation(snapshots, analysis, fp_insights)
    fp_block = fingerprint_compare_to_json(
        fp_rows,
        fp_insights,
        interpretation=fp_interp,
    )

    out: dict[str, Any] = {
        "schema_version": 1,
        "campaign_id": manifest.campaign_id,
        "dimensions": dimensions,
        "varied_axes": sorted(varied_axes),
        "backend_performance": [
            {
                "backend_kind": b.backend_kind,
                "mean_score": round(b.mean_score, 6),
                "cell_count": b.cell_count,
            }
            for b in backends
        ],
        "semantic_instability_by_scoring_backend": [
            {"scoring_backend": k, "unstable_cell_events": n} for k, n in scoring_unstable
        ],
        "execution_mode_gaps_top": [
            {
                "run_id": r.run_id,
                "benchmark_id": r.benchmark_id,
                "prompt_id": r.prompt_id,
                "spread": round(r.spread, 6),
                "by_mode": {m: round(s, 6) for m, s in sorted(r.by_mode.items())},
            }
            for r in mode_top
        ],
        "failure_tag_counts": [{"code": c, "signal_count": n} for c, n in failure_rank],
        "failure_tags_detail": {k: v for k, v in sorted(analysis.failure_tags.items())},
        "longitudinal_thresholds": {
            "regression_delta": _DEFAULT_REGRESSION_DELTA,
            "low_score": _DEFAULT_LOW_SCORE,
            "min_recurring": _DEFAULT_MIN_RECURRING,
            "mode_gap_threshold": _DEFAULT_MODE_GAP,
            "semantic_stdev_threshold": _DEFAULT_SEMANTIC_STDEV,
            "semantic_range_threshold": _DEFAULT_SEMANTIC_RANGE,
            "series_swing_threshold": _DEFAULT_SERIES_SWING,
            "min_runs_for_swing": _DEFAULT_MIN_RUNS_SWING,
        },
    }
    out["mean_score_extremes_by_sweep_axis"] = mean_score_extremes_by_sweep_axis(manifest)
    out["member_mean_score_by_dimension"] = member_mean_score_dimension_to_json(manifest)
    out.update(fp_block)
    if campaign_dir is not None:
        be = campaign_browser_evidence_json_rows(
            campaign_dir=campaign_dir,
            manifest=manifest,
        )
        if be:
            out["browser_evidence_member_cells"] = be
    if semantic_summary is not None:
        t = semantic_summary.totals
        ih = semantic_summary.instability_highlights
        out["judge_campaign_semantic"] = {
            "totals": {
                "low_confidence_cells": t.low_confidence_cells,
                "cells_flagged_judge_low_confidence": t.cells_flagged_judge_low_confidence,
                "cells_flagged_repeat_confidence_low": t.cells_flagged_repeat_confidence_low,
                "cells_with_repeat_judge": t.cells_with_repeat_judge,
                "max_range_across_campaign": t.max_range_across_campaign,
                "mean_range_repeat_cells": t.mean_range_repeat_cells,
                "mean_total_weighted_stdev_repeat": t.mean_total_weighted_stdev_repeat,
            },
            "confidence_flag_counts": ih.confidence_flag_counts,
            "criterion_instability_top": [
                {
                    "criterion_id": c.criterion_id,
                    "cells_with_repeat_judge": c.cells_with_repeat_judge,
                    "sum_score_range": round(c.sum_score_range, 6),
                    "max_score_range": round(c.max_score_range, 6),
                    "mean_score_range": round(c.mean_score_range, 6),
                }
                for c in semantic_summary.criterion_instability[:15]
            ],
            "unstable_suites": [
                {
                    "rank": h.rank,
                    "axis_value": h.axis_value,
                    "instability_score": round(h.instability_score, 6),
                    "low_confidence_cells": h.low_confidence_cells,
                    "repeat_judge_cells": h.repeat_judge_cells,
                }
                for h in ih.unstable_suites[:8]
            ],
            "unstable_providers": [
                {
                    "rank": h.rank,
                    "axis_value": h.axis_value,
                    "instability_score": round(h.instability_score, 6),
                    "low_confidence_cells": h.low_confidence_cells,
                    "repeat_judge_cells": h.repeat_judge_cells,
                }
                for h in ih.unstable_providers[:8]
            ],
            "unstable_execution_modes": [
                {
                    "rank": h.rank,
                    "axis_value": h.axis_value,
                    "instability_score": round(h.instability_score, 6),
                    "low_confidence_cells": h.low_confidence_cells,
                    "repeat_judge_cells": h.repeat_judge_cells,
                }
                for h in ih.unstable_execution_modes[:8]
            ],
        }
    return out


def render_campaign_comparative_markdown(
    manifest: BenchmarkCampaignManifest,
    snapshots: list[RunSnapshot],
    analysis: LongitudinalAnalysis,
    *,
    browser_evidence_markdown: str = "",
    semantic_summary: CampaignSemanticSummaryV1 | None = None,
) -> str:
    """Narrative report: dimensions, backends, scoring instability, mode gaps, FT-* counts."""
    lines = [
        f"# Campaign comparative report: `{manifest.campaign_id}`",
        "",
        "Succeeded member runs only. **`FT-*`** taxonomy matches longitudinal analysis "
        "(manifest run order). Mode gaps and judge instability are per snapshot.",
        "",
        render_comparative_executive_markdown(manifest, snapshots, analysis),
    ]
    if semantic_summary is not None:
        lines.append(render_campaign_semantic_judge_section_markdown(semantic_summary))
    lines.extend(
        [
            "## Which dimensions varied",
            "",
        ],
    )
    dim = summarize_campaign_dimensions(manifest)
    coincide = suite_ref_benchmark_id_partition_coincide(manifest)
    lines.append("| Axis | Distinct values | Varied |")
    lines.append("| --- | ---: | --- |")
    for key in sorted(dim.keys()):
        if coincide and key == "benchmark_id":
            continue
        block = dim[key]
        if not isinstance(block, dict):
            continue
        vals = block.get("values")
        varied = "yes" if block.get("varied") else "no"
        vshow = (
            ", ".join(str(x) for x in vals) if isinstance(vals, list) else str(vals)
        )
        axis = block.get("axis", key)
        dc = block.get("distinct_count", 0)
        if coincide and key == "suite_ref":
            axis_label = "suite_ref (paired with benchmark_id)"
        else:
            axis_label = str(axis)
        lines.append(f"| `{axis_label}` | {dc} ({vshow}) | {varied} |")
    lines.append("")

    lines.append(render_member_mean_score_tables_markdown(manifest).rstrip())
    lines.append("")

    fp_rows = build_fingerprint_axis_groups(snapshots, analysis)
    fp_insights = build_fingerprint_axis_insights(snapshots, analysis)
    fp_interp = build_fingerprint_axis_interpretation(snapshots, analysis, fp_insights)
    lines.append(
        render_fingerprint_compare_markdown(
            fp_rows,
            fp_insights,
            interpretation=fp_interp,
        ).rstrip(),
    )
    lines.append("")
    if browser_evidence_markdown.strip():
        lines.append(browser_evidence_markdown.rstrip())
        lines.append("")

    lines.extend(
        [
            "## Provider / backend performance (mean cell score)",
            "",
            "Higher is better (simple mean of **total_weighted_score** over all cells "
            "using that **backend_kind** across member runs).",
            "",
            "| Rank | backend_kind | Mean score | Cells |",
            "| ---: | --- | ---: | ---: |",
        ],
    )
    backs = aggregate_backend_performance(snapshots)
    for i, b in enumerate(backs, start=1):
        lines.append(
            f"| {i} | `{b.backend_kind}` | {b.mean_score:.6f} | {b.cell_count} |",
        )
    if not backs:
        lines.append("| — | — | — | — |")
    lines.append("")

    lines.extend(
        [
            "## Scoring backends with semantic / hybrid instability",
            "",
            "Counts **cells** flagged in longitudinal semantic stability analysis "
            "(low confidence or repeat-variance thresholds), grouped by **scoring_backend** "
            "on the evaluation artifact.",
            "",
            "| scoring_backend | Unstable cell events |",
            "| --- | ---: |",
        ],
    )
    su = count_semantic_instability_by_scoring_backend(analysis)
    if not su:
        lines.append("| *(no unstable cells)* | 0 |")
    for sb, n in su:
        lines.append(f"| `{sb}` | {n} |")
    lines.append("")

    _n_mode = min(20, max(1, len(analysis.mode_gaps)))
    _mode_intro = (
        f"Largest spreads across **execution_mode** for the same **prompt_id** inside one "
        f"member run (threshold ≥ {_DEFAULT_MODE_GAP:g}; top {_n_mode} rows)."
    )
    lines.extend(
        [
            "## Execution mode divergence (within-run)",
            "",
            _mode_intro,
            "",
            "| run_id | benchmark | prompt | spread | modes (score) |",
            "| --- | --- | --- | ---: | --- |",
        ],
    )
    for r in top_mode_gap_rows(analysis, limit=20):
        modes_s = ", ".join(
            f"{m}={r.by_mode[m]:.4f}" for m in sorted(r.by_mode.keys())
        )
        lines.append(
            f"| `{r.run_id}` | `{r.benchmark_id}` | `{r.prompt_id}` | {r.spread:.6f} | {modes_s} |",
        )
    if not analysis.mode_gaps:
        lines.append("| — | — | — | — | _No mode-gap signals at threshold._ |")
    lines.append("")

    lines.extend(
        [
            "## Top recurring failure taxonomy tags",
            "",
            "Signal counts (unique FT-* entries per code). See `docs/workflows/"
            "longitudinal-reporting.md` or `FAILURE_TAXONOMY` in `pipelines/longitudinal.py`.",
            "",
            "| Rank | Code | Signals | Description |",
            "| ---: | --- | ---: | --- |",
        ],
    )
    ranked = count_failure_tags(analysis)
    for i, (code, n) in enumerate(ranked[:15], start=1):
        desc = FAILURE_TAXONOMY.get(code, "")
        lines.append(f"| {i} | `{code}` | {n} | {desc} |")
    if not ranked:
        lines.append("| — | — | 0 | _No FT-* signals in this pass._ |")
    lines.append("")

    lines.append("## Failure atlas (full taxonomy)")
    lines.append("")
    atlas_lines = render_failure_atlas(analysis).split("\n")
    if atlas_lines and atlas_lines[0].startswith("# "):
        atlas_lines = atlas_lines[1:]
    while atlas_lines and atlas_lines[0].strip() == "":
        atlas_lines.pop(0)
    lines.extend(atlas_lines)
    return "\n".join(lines)


def write_campaign_comparative_artifacts(
    repo_root: Path,
    output_dir: Path,
    manifest: BenchmarkCampaignManifest,
    *,
    semantic_summary: CampaignSemanticSummaryV1 | None = None,
) -> tuple[
    CampaignGeneratedReportPaths | None,
    tuple[list[RunSnapshot], LongitudinalAnalysis] | None,
]:
    """Write ``reports/campaign-report.md`` and ``reports/campaign-analysis.json`` when possible.

    Returns ``(paths_fragment, (snapshots, analysis))`` for embedding in campaign summary, or
    ``(None, None)`` when skipped. Pass ``semantic_summary`` so the comparative report and JSON
    mirror **judge_low_confidence** / **repeat_aggregation** rollups from
    ``campaign-semantic-summary.json``.
    """
    if manifest.dry_run:
        return None, None
    paths = _manifest_paths_for_succeeded_runs(output_dir, manifest)
    if not paths:
        return None, None

    repo_root = repo_root.resolve()
    output_dir = output_dir.resolve()
    snaps = load_run_snapshots(repo_root, paths)
    analysis = analyze_longitudinal(
        snaps,
        regression_delta=_DEFAULT_REGRESSION_DELTA,
        low_score=_DEFAULT_LOW_SCORE,
        min_recurring=_DEFAULT_MIN_RECURRING,
        mode_gap_threshold=_DEFAULT_MODE_GAP,
        semantic_stdev_threshold=_DEFAULT_SEMANTIC_STDEV,
        semantic_range_threshold=_DEFAULT_SEMANTIC_RANGE,
        series_swing_threshold=_DEFAULT_SERIES_SWING,
        min_runs_for_swing=_DEFAULT_MIN_RUNS_SWING,
    )

    reports_dir = output_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    md_path = reports_dir / "campaign-report.md"
    json_path = reports_dir / "campaign-analysis.json"

    browser_md = render_campaign_browser_evidence_markdown(
        campaign_dir=output_dir,
        manifest=manifest,
    )
    write_utf8_text(
        md_path,
        render_campaign_comparative_markdown(
            manifest,
            snaps,
            analysis,
            browser_evidence_markdown=browser_md,
            semantic_summary=semantic_summary,
        ),
    )
    write_json_sorted(
        json_path,
        build_campaign_analysis_dict(
            manifest,
            snaps,
            analysis,
            campaign_dir=output_dir,
            semantic_summary=semantic_summary,
        ),
    )

    return (
        CampaignGeneratedReportPaths(
            campaign_comparative_report_md="reports/campaign-report.md",
            campaign_analysis_json="reports/campaign-analysis.json",
        ),
        (snaps, analysis),
    )


def merge_generated_report_paths(
    base: CampaignGeneratedReportPaths | None,
    extra: CampaignGeneratedReportPaths | None,
) -> CampaignGeneratedReportPaths:
    if base is None:
        base = CampaignGeneratedReportPaths()
    if extra is None:
        return base
    data = base.model_dump(mode="json")
    for k, v in extra.model_dump(mode="json").items():
        if v is not None:
            data[k] = v
    return CampaignGeneratedReportPaths.model_validate(data)
