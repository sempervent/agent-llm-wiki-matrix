"""Campaign-level comparative reports (Markdown + JSON) from member benchmark runs.

Reuses :func:`analyze_longitudinal` and failure-tag taxonomy from ``pipelines.longitudinal``.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent_llm_wiki_matrix.benchmark.persistence import write_json_sorted, write_utf8_text
from agent_llm_wiki_matrix.models import BenchmarkCampaignManifest, CampaignGeneratedReportPaths
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
) -> dict[str, Any]:
    """Structured mirror of the Markdown report (deterministic key order via JSON dump)."""
    dimensions = summarize_campaign_dimensions(manifest)
    varied_axes = [k for k, v in dimensions.items() if isinstance(v, dict) and v.get("varied")]
    backends = aggregate_backend_performance(snapshots)
    scoring_unstable = count_semantic_instability_by_scoring_backend(analysis)
    failure_rank = count_failure_tags(analysis)
    mode_top = top_mode_gap_rows(analysis)

    return {
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


def render_campaign_comparative_markdown(
    manifest: BenchmarkCampaignManifest,
    snapshots: list[RunSnapshot],
    analysis: LongitudinalAnalysis,
) -> str:
    """Narrative report: dimensions, backends, scoring instability, mode gaps, FT-* counts."""
    lines = [
        f"# Campaign comparative report: `{manifest.campaign_id}`",
        "",
        "Aggregates **succeeded** member runs under this campaign directory. "
        "Regression-style **`FT-*`** signals use the same taxonomy as longitudinal analysis "
        "(adjacent run order in the campaign manifest when the same benchmark cell appears "
        "in multiple runs). Within-run mode gaps and judge instability apply per snapshot.",
        "",
        "## Which dimensions varied",
        "",
    ]
    dim = summarize_campaign_dimensions(manifest)
    lines.append("| Axis | Distinct values | Varied |")
    lines.append("| --- | ---: | --- |")
    for key in sorted(dim.keys()):
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
        lines.append(f"| `{axis}` | {dc} ({vshow}) | {varied} |")
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
) -> CampaignGeneratedReportPaths | None:
    """Write ``reports/campaign-report.md`` and ``reports/campaign-analysis.json`` when possible.

    Returns updated ``CampaignGeneratedReportPaths`` fragment, or ``None`` to keep defaults only.
    """
    if manifest.dry_run:
        return None
    paths = _manifest_paths_for_succeeded_runs(output_dir, manifest)
    if not paths:
        return None

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

    write_utf8_text(md_path, render_campaign_comparative_markdown(manifest, snaps, analysis))
    write_json_sorted(json_path, build_campaign_analysis_dict(manifest, snaps, analysis))

    return CampaignGeneratedReportPaths(
        campaign_comparative_report_md="reports/campaign-report.md",
        campaign_analysis_json="reports/campaign-analysis.json",
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
