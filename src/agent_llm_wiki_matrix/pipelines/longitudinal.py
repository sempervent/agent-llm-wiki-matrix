"""Longitudinal and weekly analysis from benchmark run directories.

Loads manifest + evaluations + optional matrices/grid.json.
"""

from __future__ import annotations

import glob
import json
import statistics
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from agent_llm_wiki_matrix.artifacts import load_artifact_file
from agent_llm_wiki_matrix.models import (
    BenchmarkComparisonFingerprints,
    BenchmarkResponse,
    BenchmarkRunManifest,
    BenchmarkTaxonomyV1,
    ComparisonMatrix,
    Evaluation,
    EvaluationJudgeProvenance,
)
from agent_llm_wiki_matrix.pipelines.benchmark_run_context import (
    BenchmarkRunContextV1,
    load_run_context_optional,
)

FAILURE_TAXONOMY: dict[str, str] = {
    "FT-ABS-LOW": "Cell total score below the configured low-score threshold.",
    "FT-RUN-REG": (
        "Run-over-run regression: total score dropped more than the regression delta "
        "vs the previous snapshot for the same benchmark + cell."
    ),
    "FT-CRIT-DROP": "At least one rubric criterion dropped vs the previous run for that cell.",
    "FT-RECUR-LOW": (
        "Cell scored below the low threshold in at least `min_recurring` distinct runs."
    ),
    "FT-MODE-GAP": (
        "Within a single run, spread of cell means across execution modes for the same prompt "
        "exceeds the mode-gap threshold."
    ),
    "FT-PROV-SPLIT": (
        "Within a single run, multiple backend kinds present — compare mock vs live paths "
        "explicitly when interpreting scores."
    ),
    "FT-JUDGE-UNSTABLE": (
        "Semantic or hybrid judge flagged low confidence, or repeat-run stdev/range "
        "exceeded the configured semantic threshold for that cell."
    ),
    "FT-SERIES-SWING": (
        "High variance of total score across three or more snapshots for the same benchmark "
        "cell (oscillation / instability over time)."
    ),
}


def _truncate_fingerprint_display(s: str, *, max_len: int = 22) -> str:
    if len(s) <= max_len:
        return s
    return f"{s[: max_len - 1]}…"


def _parse_created_at(raw: str) -> datetime:
    s = raw.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def _iso_week(dt: datetime) -> tuple[int, int]:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.isocalendar()[0], dt.isocalendar()[1]


@dataclass(frozen=True)
class CellSnapshot:
    """One cell's scored metrics loaded from disk."""

    cell_id: str
    variant_id: str
    prompt_id: str
    execution_mode: str
    agent_stack: str
    backend_kind: str
    backend_model: str
    total_score: float
    criterion_scores: dict[str, float]
    scoring_backend: str
    eval_relpath: str
    semantic_variance: dict[str, Any] | None = None
    judge_low_confidence: bool | None = None


@dataclass(frozen=True)
class RunSnapshot:
    """One benchmark output directory (manifest at root)."""

    run_root: Path
    run_relpath: str
    manifest_path: str
    run_id: str
    benchmark_id: str
    title: str
    created_at: datetime
    created_at_raw: str
    cells: tuple[CellSnapshot, ...]
    grid: ComparisonMatrix | None
    taxonomy: BenchmarkTaxonomyV1 | None = None
    run_context: BenchmarkRunContextV1 | None = None
    comparison_fingerprints: BenchmarkComparisonFingerprints | None = None


def _judge_provenance_relpath(
    row_judge: str | None,
    ev_judge: str | None,
) -> str | None:
    return row_judge or ev_judge


def _build_semantic_variance(
    ev: Evaluation,
    prov: EvaluationJudgeProvenance | None,
) -> dict[str, Any] | None:
    """Structured semantic/hybrid repeat variance for Markdown and JSON summaries."""
    if ev.scoring_backend == "deterministic":
        return None
    out: dict[str, Any] = {}
    if ev.judge_low_confidence is not None:
        out["judge_low_confidence"] = ev.judge_low_confidence
    if ev.judge_repeat_count is not None:
        out["judge_repeat_count"] = ev.judge_repeat_count
    if ev.judge_semantic_aggregation is not None:
        out["judge_semantic_aggregation"] = ev.judge_semantic_aggregation
    if prov is not None:
        out["scoring_backend"] = prov.scoring_backend
        if prov.repeat_aggregation is not None:
            ra = prov.repeat_aggregation
            d = ra.disagreement
            out["total_weighted_stdev"] = d.total_weighted_stdev
            out["max_range_across_criteria"] = d.max_range_across_criteria
            out["mean_stdev_across_criteria"] = d.mean_stdev_across_criteria
        if prov.hybrid_aggregation is not None:
            out["hybrid_semantic_weight"] = prov.hybrid_aggregation.semantic_weight
            out["hybrid_deterministic_weight"] = prov.hybrid_aggregation.deterministic_weight
    return out or None


LongitudinalGroupKey = Literal[
    "git_ref",
    "release_tag",
    "provider_fingerprint",
    "scoring_backend",
    "execution_mode",
    "task_family",
    "suite_definition_fingerprint",
    "prompt_set_fingerprint",
    "provider_config_fingerprint",
    "scoring_config_fingerprint",
    "browser_config_fingerprint",
    "prompt_registry_state_fingerprint",
]


def _label_for_group_key(snap: RunSnapshot, key: LongitudinalGroupKey) -> str:
    if key == "git_ref":
        if snap.run_context and snap.run_context.git_ref:
            return snap.run_context.git_ref
        return "(unknown)"
    if key == "release_tag":
        return (
            snap.run_context.release_tag
            if snap.run_context and snap.run_context.release_tag
            else "(unknown)"
        )
    if key == "provider_fingerprint":
        return (
            snap.run_context.provider_fingerprint
            if snap.run_context and snap.run_context.provider_fingerprint
            else "(unknown)"
        )
    if key == "scoring_backend":
        kinds = {c.scoring_backend for c in snap.cells}
        return next(iter(kinds)) if len(kinds) == 1 else "(mixed)"
    if key == "execution_mode":
        modes = {c.execution_mode for c in snap.cells}
        return next(iter(modes)) if len(modes) == 1 else "(mixed)"
    if key == "task_family":
        if snap.taxonomy is not None:
            return snap.taxonomy.task_family
        return "(unknown)"
    if key == "suite_definition_fingerprint":
        if snap.comparison_fingerprints is not None:
            return snap.comparison_fingerprints.suite_definition
        return "(unknown)"
    if key == "prompt_set_fingerprint":
        if snap.comparison_fingerprints is not None:
            return snap.comparison_fingerprints.prompt_set
        return "(unknown)"
    if key == "provider_config_fingerprint":
        if snap.comparison_fingerprints is not None:
            return snap.comparison_fingerprints.provider_config
        return "(unknown)"
    if key == "scoring_config_fingerprint":
        if snap.comparison_fingerprints is not None:
            return snap.comparison_fingerprints.scoring_config
        return "(unknown)"
    if key == "browser_config_fingerprint":
        if snap.comparison_fingerprints is not None:
            return snap.comparison_fingerprints.browser_config
        return "(unknown)"
    if key == "prompt_registry_state_fingerprint":
        if snap.comparison_fingerprints is not None:
            return snap.comparison_fingerprints.prompt_registry_state
        return "(unknown)"
    msg = f"unsupported group key: {key}"
    raise ValueError(msg)


def group_snapshots_by(
    snapshots: Sequence[RunSnapshot],
    key: LongitudinalGroupKey,
) -> dict[str, list[RunSnapshot]]:
    """Group runs by git ref, tag, provider, taxonomy, or fingerprint keys."""
    buckets: dict[str, list[RunSnapshot]] = defaultdict(list)
    for s in snapshots:
        label = _label_for_group_key(s, key)
        buckets[label].append(s)
    return {k: sorted(v, key=lambda x: (x.created_at, x.run_id)) for k, v in buckets.items()}


def load_run_snapshot(repo_root: Path, manifest_path: Path) -> RunSnapshot:
    """Load manifest, cell evaluations/responses, and optional grid matrix."""
    repo_root = repo_root.resolve()
    manifest_path = manifest_path.resolve()
    run_root = manifest_path.parent
    try:
        mrel = manifest_path.relative_to(repo_root).as_posix()
        rrel = run_root.relative_to(repo_root).as_posix()
    except ValueError:
        mrel = str(manifest_path)
        rrel = str(run_root)

    raw_m = json.loads(manifest_path.read_text(encoding="utf-8"))
    mf = BenchmarkRunManifest.model_validate(raw_m)
    run_context = load_run_context_optional(run_root)

    cells: list[CellSnapshot] = []
    for row in mf.cells:
        ev_path = run_root / row.evaluation_relpath
        br_path = run_root / row.aggregate_response_relpath
        ev = load_artifact_file(ev_path, "evaluation")
        if not isinstance(ev, Evaluation):
            msg = "Expected evaluation artifact"
            raise TypeError(msg)
        br = load_artifact_file(br_path, "benchmark_response")
        if not isinstance(br, BenchmarkResponse):
            msg = "Expected benchmark_response artifact"
            raise TypeError(msg)
        vid, pid = br.variant_id, br.prompt_id
        prov: EvaluationJudgeProvenance | None = None
        jp = _judge_provenance_relpath(row.judge_provenance_relpath, ev.judge_provenance_relpath)
        if jp:
            prov_path = run_root / jp
            if prov_path.is_file():
                loaded_prov = load_artifact_file(prov_path, "evaluation_judge_provenance")
                if not isinstance(loaded_prov, EvaluationJudgeProvenance):
                    msg = "Expected evaluation_judge_provenance artifact"
                    raise TypeError(msg)
                prov = loaded_prov
        sem_var = _build_semantic_variance(ev, prov)
        cells.append(
            CellSnapshot(
                cell_id=row.cell_id,
                variant_id=vid,
                prompt_id=pid,
                execution_mode=br.execution_mode,
                agent_stack=br.agent_stack,
                backend_kind=br.backend_kind,
                backend_model=br.backend_model,
                total_score=ev.total_weighted_score,
                criterion_scores=dict(ev.scores),
                scoring_backend=ev.scoring_backend,
                eval_relpath=row.evaluation_relpath,
                semantic_variance=sem_var,
                judge_low_confidence=ev.judge_low_confidence,
            ),
        )

    grid: ComparisonMatrix | None = None
    gpath = run_root / mf.matrix_grid_path
    if gpath.is_file():
        loaded_grid = load_artifact_file(gpath, "matrix")
        if not isinstance(loaded_grid, ComparisonMatrix):
            msg = "Expected matrix artifact for grid"
            raise TypeError(msg)
        grid = loaded_grid

    return RunSnapshot(
        run_root=run_root,
        run_relpath=rrel,
        manifest_path=mrel,
        run_id=mf.run_id,
        benchmark_id=mf.benchmark_id,
        title=mf.title,
        created_at=_parse_created_at(mf.created_at),
        created_at_raw=mf.created_at,
        cells=tuple(cells),
        grid=grid,
        taxonomy=mf.taxonomy,
        run_context=run_context,
        comparison_fingerprints=mf.comparison_fingerprints,
    )


def discover_manifest_paths(repo_root: Path, glob_pattern: str) -> list[Path]:
    """Resolve ``glob_pattern`` relative to repo root (forward slashes)."""
    repo_root = repo_root.resolve()
    full = str(repo_root / glob_pattern)
    paths = sorted(Path(p) for p in glob.glob(full))
    return [p for p in paths if p.is_file()]


def load_run_snapshots(repo_root: Path, manifest_paths: Sequence[Path]) -> list[RunSnapshot]:
    snaps = [load_run_snapshot(repo_root, p) for p in manifest_paths]
    return sorted(snaps, key=lambda s: (s.created_at, s.run_id))


@dataclass
class RegressionRow:
    benchmark_id: str
    cell_id: str
    from_run: str
    to_run: str
    prev_score: float
    curr_score: float
    delta: float


@dataclass
class ImprovementRow:
    benchmark_id: str
    cell_id: str
    from_run: str
    to_run: str
    prev_score: float
    curr_score: float
    delta: float


@dataclass
class CriterionDropRow:
    benchmark_id: str
    cell_id: str
    criterion_id: str
    from_run: str
    to_run: str
    prev: float
    curr: float


@dataclass
class RecurringLowRow:
    benchmark_id: str
    cell_id: str
    runs: list[str]
    scores: list[float]


@dataclass
class ModeGapRow:
    run_id: str
    benchmark_id: str
    prompt_id: str
    spread: float
    by_mode: dict[str, float]


@dataclass
class SemanticStabilityRow:
    """Per-cell semantic/hybrid judge instability within one snapshot."""

    run_id: str
    run_relpath: str
    benchmark_id: str
    cell_id: str
    total_weighted_stdev: float | None
    max_range_across_criteria: float | None
    judge_low_confidence: bool | None
    reason: str


@dataclass
class ScoreOscillationRow:
    """High variance of total score across time for one benchmark cell."""

    benchmark_id: str
    cell_id: str
    run_count: int
    score_std: float
    run_relpaths: list[str]
    scores: list[float]


@dataclass
class LongitudinalAnalysis:
    """Structured output for JSON + Markdown."""

    snapshots: list[RunSnapshot]
    regressions: list[RegressionRow]
    improvements: list[ImprovementRow]
    criterion_drops: list[CriterionDropRow]
    recurring_lows: list[RecurringLowRow]
    mode_gaps: list[ModeGapRow]
    semantic_stability: list[SemanticStabilityRow]
    score_oscillations: list[ScoreOscillationRow]
    weekly_buckets: dict[tuple[int, int], list[RunSnapshot]]
    failure_tags: dict[str, list[str]] = field(default_factory=dict)


def analyze_longitudinal(
    snapshots: Sequence[RunSnapshot],
    *,
    regression_delta: float,
    low_score: float,
    min_recurring: int,
    mode_gap_threshold: float,
    semantic_stdev_threshold: float = 0.12,
    semantic_range_threshold: float = 0.22,
    series_swing_threshold: float = 0.06,
    min_runs_for_swing: int = 3,
) -> LongitudinalAnalysis:
    snaps = sorted(snapshots, key=lambda s: (s.created_at, s.run_id))
    regressions: list[RegressionRow] = []
    improvements: list[ImprovementRow] = []
    criterion_drops: list[CriterionDropRow] = []
    recurring_lows: list[RecurringLowRow] = []
    mode_gaps: list[ModeGapRow] = []
    semantic_stability: list[SemanticStabilityRow] = []
    score_oscillations: list[ScoreOscillationRow] = []
    failure_tags: dict[str, list[str]] = defaultdict(list)

    weekly: dict[tuple[int, int], list[RunSnapshot]] = defaultdict(list)
    for s in snaps:
        y, w = _iso_week(s.created_at)
        weekly[(y, w)].append(s)

    # Index cells by (benchmark_id, cell_id) -> list of (snapshot, cell)
    series: dict[tuple[str, str], list[tuple[RunSnapshot, CellSnapshot]]] = defaultdict(list)
    for s in snaps:
        for c in s.cells:
            series[(s.benchmark_id, c.cell_id)].append((s, c))

    for key, chain in series.items():
        bench_id, cell_id = key
        chain_sorted = sorted(chain, key=lambda t: (t[0].created_at, t[0].run_id))
        for i in range(1, len(chain_sorted)):
            prev_s, prev_c = chain_sorted[i - 1]
            curr_s, curr_c = chain_sorted[i]
            d = curr_c.total_score - prev_c.total_score
            if d < -regression_delta:
                regressions.append(
                    RegressionRow(
                        benchmark_id=bench_id,
                        cell_id=cell_id,
                        from_run=prev_s.run_relpath,
                        to_run=curr_s.run_relpath,
                        prev_score=prev_c.total_score,
                        curr_score=curr_c.total_score,
                        delta=d,
                    ),
                )
                failure_tags["FT-RUN-REG"].append(f"{bench_id}::{cell_id}")
            elif d > regression_delta:
                improvements.append(
                    ImprovementRow(
                        benchmark_id=bench_id,
                        cell_id=cell_id,
                        from_run=prev_s.run_relpath,
                        to_run=curr_s.run_relpath,
                        prev_score=prev_c.total_score,
                        curr_score=curr_c.total_score,
                        delta=d,
                    ),
                )
            # criterion drops
            for cid in prev_c.criterion_scores:
                if cid not in curr_c.criterion_scores:
                    continue
                cd = curr_c.criterion_scores[cid] - prev_c.criterion_scores[cid]
                if cd < -regression_delta:
                    criterion_drops.append(
                        CriterionDropRow(
                            benchmark_id=bench_id,
                            cell_id=cell_id,
                            criterion_id=cid,
                            from_run=prev_s.run_relpath,
                            to_run=curr_s.run_relpath,
                            prev=prev_c.criterion_scores[cid],
                            curr=curr_c.criterion_scores[cid],
                        ),
                    )
                    failure_tags["FT-CRIT-DROP"].append(f"{bench_id}::{cell_id}::{cid}")

    # Recurring lows
    low_runs: dict[tuple[str, str], list[tuple[str, float]]] = defaultdict(list)
    for s in snaps:
        for c in s.cells:
            if c.total_score < low_score:
                low_runs[(s.benchmark_id, c.cell_id)].append((s.run_relpath, c.total_score))
    for key, runs in low_runs.items():
        if len(runs) >= min_recurring:
            recurring_lows.append(
                RecurringLowRow(
                    benchmark_id=key[0],
                    cell_id=key[1],
                    runs=[r[0] for r in runs],
                    scores=[r[1] for r in runs],
                ),
            )
            failure_tags["FT-RECUR-LOW"].append(f"{key[0]}::{key[1]}")

    # Absolute low (latest snapshot per cell)
    for s in snaps:
        for c in s.cells:
            if c.total_score < low_score:
                failure_tags["FT-ABS-LOW"].append(f"{s.benchmark_id}::{c.cell_id}")

    # Mode gaps: per run, per prompt_id — max min spread across execution modes
    for s in snaps:
        by_prompt: dict[str, list[CellSnapshot]] = defaultdict(list)
        for c in s.cells:
            by_prompt[c.prompt_id].append(c)
        for pid, group in by_prompt.items():
            modes = {c.execution_mode: c.total_score for c in group}
            if len(modes) < 2:
                continue
            vals = list(modes.values())
            spread = max(vals) - min(vals)
            if spread >= mode_gap_threshold:
                mode_gaps.append(
                    ModeGapRow(
                        run_id=s.run_id,
                        benchmark_id=s.benchmark_id,
                        prompt_id=pid,
                        spread=spread,
                        by_mode=modes,
                    ),
                )
                failure_tags["FT-MODE-GAP"].append(f"{s.benchmark_id}::{pid}")

    # Provider split narrative
    for s in snaps:
        kinds = {c.backend_kind for c in s.cells}
        if len(kinds) > 1:
            failure_tags["FT-PROV-SPLIT"].append(s.benchmark_id)

    # High variance of total score across runs (same benchmark cell)
    for key, chain in series.items():
        bench_id, cell_id = key
        chain_sorted = sorted(chain, key=lambda t: (t[0].created_at, t[0].run_id))
        scores = [t[1].total_score for t in chain_sorted]
        rels = [t[0].run_relpath for t in chain_sorted]
        if len(scores) < min_runs_for_swing:
            continue
        std = statistics.pstdev(scores)
        if std > series_swing_threshold:
            score_oscillations.append(
                ScoreOscillationRow(
                    benchmark_id=bench_id,
                    cell_id=cell_id,
                    run_count=len(scores),
                    score_std=std,
                    run_relpaths=rels,
                    scores=scores,
                ),
            )
            failure_tags["FT-SERIES-SWING"].append(f"{bench_id}::{cell_id}")

    # Semantic / hybrid repeat variance (within-run)
    for s in snaps:
        for c in s.cells:
            tw_stdev: float | None = None
            mx_range: float | None = None
            if c.semantic_variance:
                raw_tw = c.semantic_variance.get("total_weighted_stdev")
                if isinstance(raw_tw, (int, float)):
                    tw_stdev = float(raw_tw)
                raw_mx = c.semantic_variance.get("max_range_across_criteria")
                if isinstance(raw_mx, (int, float)):
                    mx_range = float(raw_mx)
            reasons: list[str] = []
            if c.judge_low_confidence is True:
                reasons.append("judge_low_confidence")
            if tw_stdev is not None and tw_stdev > semantic_stdev_threshold:
                reasons.append(f"total_weighted_stdev>{semantic_stdev_threshold:g}")
            if mx_range is not None and mx_range > semantic_range_threshold:
                reasons.append(f"max_range_across_criteria>{semantic_range_threshold:g}")
            if not reasons:
                continue
            semantic_stability.append(
                SemanticStabilityRow(
                    run_id=s.run_id,
                    run_relpath=s.run_relpath,
                    benchmark_id=s.benchmark_id,
                    cell_id=c.cell_id,
                    total_weighted_stdev=tw_stdev,
                    max_range_across_criteria=mx_range,
                    judge_low_confidence=c.judge_low_confidence,
                    reason=", ".join(reasons),
                ),
            )
            failure_tags["FT-JUDGE-UNSTABLE"].append(f"{s.benchmark_id}::{c.cell_id}")

    return LongitudinalAnalysis(
        snapshots=list(snaps),
        regressions=regressions,
        improvements=improvements,
        criterion_drops=criterion_drops,
        recurring_lows=recurring_lows,
        mode_gaps=mode_gaps,
        semantic_stability=semantic_stability,
        score_oscillations=score_oscillations,
        weekly_buckets=dict(weekly),
        failure_tags={k: sorted(set(v)) for k, v in failure_tags.items()},
    )


def render_failure_taxonomy_reference() -> str:
    """Markdown table of failure codes (for docs and atlas preamble)."""
    lines = [
        "# Failure taxonomy (benchmark longitudinal)",
        "",
        "| Code | Description |",
        "| --- | --- |",
    ]
    for code, desc in FAILURE_TAXONOMY.items():
        lines.append(f"| `{code}` | {desc} |")
    lines.append("")
    return "\n".join(lines)


def render_failure_atlas(analysis: LongitudinalAnalysis) -> str:
    """Failure-atlas style markdown grouped by taxonomy code."""
    lines = [
        "# Failure atlas",
        "",
        (
            "Grouped signals from the analyzed benchmark runs. "
            "Paths are relative to the repository root."
        ),
        "",
    ]
    for code, desc in FAILURE_TAXONOMY.items():
        tags = analysis.failure_tags.get(code, [])
        lines.append(f"## {code}")
        lines.append("")
        lines.append(desc)
        lines.append("")
        if not tags:
            lines.append("_No signals in this pass._")
        else:
            for t in tags:
                lines.append(f"- `{t}`")
        lines.append("")
    return "\n".join(lines)


def render_weekly_markdown(analysis: LongitudinalAnalysis) -> str:
    """Weekly rollup: runs per ISO week and mean score (all cells)."""
    lines = [
        "# Weekly benchmark rollup",
        "",
        "| ISO year-week | Runs | Benchmark ids | Task families | Mean total score |",
        "| --- | ---: | --- | --- | ---: |",
    ]
    for (y, w) in sorted(analysis.weekly_buckets.keys()):
        bucket = analysis.weekly_buckets[(y, w)]
        ids = sorted({s.benchmark_id for s in bucket})
        fams = sorted(
            {s.taxonomy.task_family for s in bucket if s.taxonomy is not None},
        )
        fam_cell = ", ".join(fams) if fams else "—"
        scores: list[float] = []
        for s in bucket:
            for c in s.cells:
                scores.append(c.total_score)
        mean = sum(scores) / len(scores) if scores else 0.0
        lines.append(
            f"| {y}-W{w:02d} | {len(bucket)} | {', '.join(ids)} | {fam_cell} | {mean:.6f} |",
        )
    lines.append("")
    lines.append("## Run labels (git / release / provider)")
    lines.append("")
    lines.append("| Run id | Git ref | Release tag | Provider fingerprint |")
    lines.append("| --- | --- | --- | --- |")
    for s in sorted(analysis.snapshots, key=lambda x: (x.created_at, x.run_id)):
        gr = s.run_context.git_ref if s.run_context and s.run_context.git_ref else "—"
        rt = s.run_context.release_tag if s.run_context and s.run_context.release_tag else "—"
        pf = (
            s.run_context.provider_fingerprint
            if s.run_context and s.run_context.provider_fingerprint
            else "—"
        )
        lines.append(f"| `{s.run_id}` | {gr} | {rt} | {pf} |")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- Mean is a simple average of all cell totals in that week (cross-benchmark).")
    lines.append("- Task families come from optional manifest `taxonomy` when present.")
    lines.append("- Populate `run_context.json` beside each manifest for longitudinal grouping.")
    lines.append("")
    return "\n".join(lines)


def render_longitudinal_markdown(analysis: LongitudinalAnalysis, *, title: str) -> str:
    """Full longitudinal narrative: regressions, improvements, mode/provider comparisons."""
    lines = [
        f"# {title}",
        "",
        "## Regressions (run-over-run)",
        "",
    ]
    if not analysis.regressions:
        lines.append("_None detected at current thresholds._")
    else:
        lines.append("| Benchmark | Cell | Δ score | Previous | Current | From → To |")
        lines.append("| --- | --- | ---: | ---: | ---: | --- |")
        for reg in analysis.regressions:
            lines.append(
                f"| `{reg.benchmark_id}` | `{reg.cell_id}` | {reg.delta:.6f} | "
                f"{reg.prev_score:.6f} | {reg.curr_score:.6f} | "
                f"`{reg.from_run}` → `{reg.to_run}` |",
            )
    lines.append("")
    lines.append("## Improvements (run-over-run)")
    lines.append("")
    if not analysis.improvements:
        lines.append("_None detected at current thresholds._")
    else:
        lines.append("| Benchmark | Cell | Δ score | Previous | Current | From → To |")
        lines.append("| --- | --- | ---: | ---: | ---: | --- |")
        for imp in analysis.improvements:
            lines.append(
                f"| `{imp.benchmark_id}` | `{imp.cell_id}` | {imp.delta:+.6f} | "
                f"{imp.prev_score:.6f} | {imp.curr_score:.6f} | "
                f"`{imp.from_run}` → `{imp.to_run}` |",
            )

    lines.append("")
    lines.append("## Criterion-level drops")
    lines.append("")
    if not analysis.criterion_drops:
        lines.append("_None._")
    else:
        lines.append("| Benchmark | Cell | Criterion | Prev | Curr |")
        lines.append("| --- | --- | --- | ---: | ---: |")
        for cd in analysis.criterion_drops:
            lines.append(
                f"| `{cd.benchmark_id}` | `{cd.cell_id}` | `{cd.criterion_id}` | "
                f"{cd.prev:.6f} | {cd.curr:.6f} |",
            )

    lines.append("")
    lines.append("## Recurring low scores")
    lines.append("")
    if not analysis.recurring_lows:
        lines.append("_None._")
    else:
        lines.append("| Benchmark | Cell | Runs (n) | Scores |")
        lines.append("| --- | --- | ---: | --- |")
        for rec in analysis.recurring_lows:
            lines.append(
                f"| `{rec.benchmark_id}` | `{rec.cell_id}` | {len(rec.runs)} | "
                f"{', '.join(f'{x:.4f}' for x in rec.scores)} |",
            )

    lines.append("")
    lines.append("## Execution mode spread (same prompt, one run)")
    lines.append("")
    if not analysis.mode_gaps:
        lines.append("_No multi-mode spreads above threshold._")
    else:
        lines.append("| Run id | Benchmark | Prompt | Spread | Modes (mode=score) |")
        lines.append("| --- | --- | --- | ---: | --- |")
        for mg in analysis.mode_gaps:
            modes = "; ".join(f"{k}={v:.4f}" for k, v in sorted(mg.by_mode.items()))
            row = (
                f"| `{mg.run_id}` | `{mg.benchmark_id}` | `{mg.prompt_id}` | "
                f"{mg.spread:.6f} | {modes} |"
            )
            lines.append(row)

    lines.append("")
    lines.append("## Score oscillation (across runs)")
    lines.append("")
    if not analysis.score_oscillations:
        lines.append("_None above threshold (needs at least three snapshots per cell)._")
    else:
        lines.append("| Benchmark | Cell | Runs | σ (total) | Scores |")
        lines.append("| --- | --- | ---: | ---: | --- |")
        for so in analysis.score_oscillations:
            sc = ", ".join(f"{x:.4f}" for x in so.scores)
            lines.append(
                f"| `{so.benchmark_id}` | `{so.cell_id}` | {so.run_count} | "
                f"{so.score_std:.6f} | {sc} |",
            )

    lines.append("")
    lines.append("## Semantic / hybrid instability (within-run)")
    lines.append("")
    lines.append(
        "Rows appear when thresholds flag `FT-JUDGE-UNSTABLE` (see failure taxonomy).",
    )
    lines.append("")
    if not analysis.semantic_stability:
        lines.append("_None above thresholds._")
    else:
        lines.append("| Run | Cell | σ_tot | max_range | Low conf. | Reason |")
        lines.append("| --- | --- | ---: | ---: | --- | --- |")
        for ss in analysis.semantic_stability:
            tw = f"{ss.total_weighted_stdev:.6f}" if ss.total_weighted_stdev is not None else "—"
            mr = (
                f"{ss.max_range_across_criteria:.6f}"
                if ss.max_range_across_criteria is not None
                else "—"
            )
            lc = str(ss.judge_low_confidence) if ss.judge_low_confidence is not None else "—"
            lines.append(
                f"| `{ss.run_id}` | `{ss.cell_id}` | {tw} | {mr} | {lc} | {ss.reason} |",
            )

    lines.append("")
    lines.append("## Provider / backend mix")
    lines.append("")
    lines.append(
        "Per run, cells may use `mock`, `ollama`, or `openai_compatible`. "
        "Treat cross-kind comparisons as indicative only unless rubrics and prompts "
        "are held constant.",
    )
    lines.append("")
    for s in analysis.snapshots:
        kinds = sorted({c.backend_kind for c in s.cells})
        lines.append(f"- `{s.run_id}` (`{s.benchmark_id}`): backends {', '.join(kinds)}")
    lines.append("")

    lines.append("## All cells: semantic variance fields (when present)")
    lines.append("")
    any_sem = False
    for s in analysis.snapshots:
        for c in s.cells:
            if not c.semantic_variance:
                continue
            any_sem = True
            raw_tw = c.semantic_variance.get("total_weighted_stdev")
            raw_mr = c.semantic_variance.get("max_range_across_criteria")
            tw_s = f"{raw_tw:.6f}" if isinstance(raw_tw, (int, float)) else "—"
            mr_s = f"{raw_mr:.6f}" if isinstance(raw_mr, (int, float)) else "—"
            jlc = c.judge_low_confidence
            lines.append(
                f"- `{s.run_id}` / `{c.cell_id}`: σ_tot={tw_s}, max_range={mr_s}, "
                f"judge_low_confidence={jlc}",
            )
    if not any_sem:
        lines.append("_No semantic/hybrid provenance with variance metadata in this bundle._")
    lines.append("")
    return "\n".join(lines)


def render_regression_report_markdown(analysis: LongitudinalAnalysis, *, title: str) -> str:
    """Markdown-first report focused on regressions, criterion loss, and instability."""
    lines = [
        f"# {title}",
        "",
        "Condensed view for triage: regressions, criterion drops, recurring lows, "
        "run-level score oscillation, and semantic-judge instability.",
        "",
        "## Regressions",
        "",
    ]
    if not analysis.regressions:
        lines.append("_None._")
    else:
        lines.append("| Benchmark | Cell | Δ | From → To |")
        lines.append("| --- | --- | ---: | --- |")
        for reg in analysis.regressions:
            lines.append(
                f"| `{reg.benchmark_id}` | `{reg.cell_id}` | {reg.delta:.6f} | "
                f"`{reg.from_run}` → `{reg.to_run}` |",
            )
    lines.append("")
    lines.append("## Criterion drops")
    lines.append("")
    if not analysis.criterion_drops:
        lines.append("_None._")
    else:
        lines.append("| Benchmark | Cell | Criterion | Prev | Curr |")
        lines.append("| --- | --- | --- | ---: | ---: |")
        for cd in analysis.criterion_drops:
            lines.append(
                f"| `{cd.benchmark_id}` | `{cd.cell_id}` | `{cd.criterion_id}` | "
                f"{cd.prev:.6f} | {cd.curr:.6f} |",
            )
    lines.append("")
    lines.append("## Recurring lows")
    lines.append("")
    if not analysis.recurring_lows:
        lines.append("_None._")
    else:
        lines.append("| Benchmark | Cell | n | Scores |")
        lines.append("| --- | --- | ---: | --- |")
        for rec in analysis.recurring_lows:
            lines.append(
                f"| `{rec.benchmark_id}` | `{rec.cell_id}` | {len(rec.runs)} | "
                f"{', '.join(f'{x:.4f}' for x in rec.scores)} |",
            )
    lines.append("")
    lines.append("## Score oscillation (across runs)")
    lines.append("")
    if not analysis.score_oscillations:
        lines.append("_None above threshold._")
    else:
        lines.append("| Benchmark | Cell | Runs | σ (total score) | Scores |")
        lines.append("| --- | --- | ---: | ---: | --- |")
        for so in analysis.score_oscillations:
            sc = ", ".join(f"{x:.4f}" for x in so.scores)
            lines.append(
                f"| `{so.benchmark_id}` | `{so.cell_id}` | {so.run_count} | "
                f"{so.score_std:.6f} | {sc} |",
            )
    lines.append("")
    lines.append("## Semantic judge instability (within run)")
    lines.append("")
    if not analysis.semantic_stability:
        lines.append("_None._")
    else:
        lines.append("| Run | Cell | σ_tot | max_range | Low conf. | Reason |")
        lines.append("| --- | --- | ---: | ---: | --- | --- |")
        for ss in analysis.semantic_stability:
            tw = f"{ss.total_weighted_stdev:.6f}" if ss.total_weighted_stdev is not None else "—"
            if ss.max_range_across_criteria is not None:
                mr = f"{ss.max_range_across_criteria:.6f}"
            else:
                mr = "—"
            lc = str(ss.judge_low_confidence) if ss.judge_low_confidence is not None else "—"
            lines.append(
                f"| `{ss.run_id}` | `{ss.cell_id}` | {tw} | {mr} | {lc} | {ss.reason} |",
            )
    lines.append("")
    return "\n".join(lines)


def render_provider_comparison_markdown(analysis: LongitudinalAnalysis, *, title: str) -> str:
    """Compare mean cell scores by provider (backend_kind) across runs."""
    lines = [
        f"# {title}",
        "",
        "Per **backend_kind** (from each cell's benchmark response), mean of cell total scores "
        "within each run. Use **`comparison_fingerprints`** on each run's `manifest.json` to "
        "confirm the same suite, prompt set, provider config, scoring config, browser config, "
        "and prompt registry state before comparing scores. Optional `run_context.json` adds "
        "git/release labels.",
        "",
        "## Comparison fingerprints (manifest)",
        "",
        "| Run id | Suite | Prompts | Providers | Scoring | Browser | Registry |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for s in sorted(analysis.snapshots, key=lambda x: (x.created_at, x.run_id)):
        if s.comparison_fingerprints is None:
            lines.append(
                f"| `{s.run_id}` | — | — | — | — | — | — |",
            )
        else:
            fp = s.comparison_fingerprints
            lines.append(
                f"| `{s.run_id}` | `{_truncate_fingerprint_display(fp.suite_definition)}` | "
                f"`{_truncate_fingerprint_display(fp.prompt_set)}` | "
                f"`{_truncate_fingerprint_display(fp.provider_config)}` | "
                f"`{_truncate_fingerprint_display(fp.scoring_config)}` | "
                f"`{_truncate_fingerprint_display(fp.browser_config)}` | "
                f"`{_truncate_fingerprint_display(fp.prompt_registry_state)}` |",
            )
    lines.append("")
    lines.append("Full hashes are 72 characters (`sha256:` + 64 hex). Truncated above for layout.")
    lines.append("")
    lines.append("## By run and backend kind")
    lines.append("")
    lines.append("| Run id | Benchmark | Backend kind | Cells | Mean score |")
    lines.append("| --- | --- | --- | ---: | ---: |")
    for s in sorted(analysis.snapshots, key=lambda x: (x.created_at, x.run_id)):
        by_bk: dict[str, list[float]] = defaultdict(list)
        for c in s.cells:
            by_bk[c.backend_kind].append(c.total_score)
        for bk in sorted(by_bk.keys()):
            vals = by_bk[bk]
            m = sum(vals) / len(vals)
            lines.append(
                f"| `{s.run_id}` | `{s.benchmark_id}` | `{bk}` | {len(vals)} | {m:.6f} |",
            )
    lines.append("")
    lines.append("## By scoring backend (evaluation)")
    lines.append("")
    lines.append("| Run id | Scoring backend | Cells | Mean score |")
    lines.append("| --- | --- | ---: | ---: |")
    for s in sorted(analysis.snapshots, key=lambda x: (x.created_at, x.run_id)):
        by_sb: dict[str, list[float]] = defaultdict(list)
        for c in s.cells:
            by_sb[c.scoring_backend].append(c.total_score)
        for sb in sorted(by_sb.keys()):
            vals = by_sb[sb]
            m = sum(vals) / len(vals)
            lines.append(f"| `{s.run_id}` | `{sb}` | {len(vals)} | {m:.6f} |")
    lines.append("")
    lines.append("## Grouping index (optional)")
    lines.append("")
    lines.append(
        "Use `group_snapshots_by(snapshots, key)` in Python with keys: "
        "`git_ref`, `release_tag`, `provider_fingerprint`, `scoring_backend`, "
        "`execution_mode`, `task_family`, "
        "`suite_definition_fingerprint`, `prompt_set_fingerprint`, "
        "`provider_config_fingerprint`, `scoring_config_fingerprint`, "
        "`browser_config_fingerprint`, `prompt_registry_state_fingerprint`.",
    )
    lines.append("")
    return "\n".join(lines)


def analysis_to_summary_dict(analysis: LongitudinalAnalysis) -> dict[str, Any]:
    """JSON-serializable summary for CI and dashboards."""
    fp_rows: list[dict[str, Any]] = []
    for s in analysis.snapshots:
        if s.comparison_fingerprints is None:
            fp_rows.append({"run_id": s.run_id, "comparison_fingerprints": None})
        else:
            fp_rows.append(
                {
                    "run_id": s.run_id,
                    "comparison_fingerprints": s.comparison_fingerprints.model_dump(
                        mode="json",
                    ),
                },
            )
    return {
        "runs": len(analysis.snapshots),
        "comparison_fingerprints_by_run": fp_rows,
        "regressions": [r.__dict__ for r in analysis.regressions],
        "improvements": [r.__dict__ for r in analysis.improvements],
        "criterion_drops": [r.__dict__ for r in analysis.criterion_drops],
        "recurring_lows": [r.__dict__ for r in analysis.recurring_lows],
        "mode_gaps": [r.__dict__ for r in analysis.mode_gaps],
        "semantic_stability": [r.__dict__ for r in analysis.semantic_stability],
        "score_oscillations": [r.__dict__ for r in analysis.score_oscillations],
        "failure_tags": analysis.failure_tags,
        "weekly": {
            f"{y}-W{w:02d}": [s.run_id for s in snaps]
            for (y, w), snaps in analysis.weekly_buckets.items()
        },
    }


def write_longitudinal_bundle(
    repo_root: Path,
    analysis: LongitudinalAnalysis,
    out_dir: Path,
    *,
    title: str,
    regression_title: str | None = None,
    provider_title: str | None = None,
) -> None:
    """Write Markdown reports (weekly, longitudinal, regression, provider) plus JSON summary."""
    _ = repo_root  # reserved for future path rewriting in reports
    reg_title = regression_title or f"Regression report — {title}"
    prov_title = provider_title or f"Provider comparison — {title}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "weekly.md").write_text(render_weekly_markdown(analysis), encoding="utf-8")
    (out_dir / "longitudinal.md").write_text(
        render_longitudinal_markdown(analysis, title=title),
        encoding="utf-8",
    )
    (out_dir / "regression.md").write_text(
        render_regression_report_markdown(analysis, title=reg_title),
        encoding="utf-8",
    )
    (out_dir / "provider-comparison.md").write_text(
        render_provider_comparison_markdown(analysis, title=prov_title),
        encoding="utf-8",
    )
    (out_dir / "failure-atlas.md").write_text(render_failure_atlas(analysis), encoding="utf-8")
    tax_md = render_failure_taxonomy_reference()
    (out_dir / "failure-taxonomy.md").write_text(tax_md, encoding="utf-8")
    (out_dir / "summary.json").write_text(
        json.dumps(analysis_to_summary_dict(analysis), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
