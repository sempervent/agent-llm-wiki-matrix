"""Campaign-level grouping by longitudinal fingerprint axes.

Uses :func:`group_snapshots_by` and :func:`truncate_fingerprint_display` from
``pipelines.longitudinal`` so campaign comparative reports stay aligned with
``alwm benchmark longitudinal`` grouping.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agent_llm_wiki_matrix.pipelines.longitudinal import (
    LongitudinalAnalysis,
    LongitudinalGroupKey,
    RunSnapshot,
    group_snapshots_by,
    truncate_fingerprint_display,
)

# Axes requested for campaign fingerprint tables (subset of ``LongitudinalGroupKey``).
FINGERPRINT_COMPARE_AXES: tuple[tuple[LongitudinalGroupKey, str], ...] = (
    ("provider_config_fingerprint", "Provider config"),
    ("scoring_config_fingerprint", "Scoring config"),
    ("execution_mode", "Execution mode"),
    ("prompt_registry_state_fingerprint", "Prompt registry state"),
    ("browser_config_fingerprint", "Browser config"),
)


def _pooled_mean_cell_score(snapshots: list[RunSnapshot]) -> float:
    scores: list[float] = []
    for s in snapshots:
        for c in s.cells:
            scores.append(c.total_score)
    return sum(scores) / len(scores) if scores else 0.0


def _run_relpath_set(snapshots: list[RunSnapshot]) -> set[str]:
    return {s.run_relpath for s in snapshots}


def _count_unstable_for_runs(
    analysis: LongitudinalAnalysis,
    relpaths: set[str],
) -> int:
    n = 0
    for row in analysis.semantic_stability:
        if row.run_relpath in relpaths:
            n += 1
    return n


def _count_regressions_targeting(
    analysis: LongitudinalAnalysis,
    relpaths: set[str],
) -> int:
    return sum(1 for r in analysis.regressions if r.to_run in relpaths)


def _count_mode_gaps_for_runs(
    analysis: LongitudinalAnalysis,
    run_ids: set[str],
) -> int:
    return sum(1 for g in analysis.mode_gaps if g.run_id in run_ids)


@dataclass(frozen=True)
class FingerprintAxisGroupRow:
    """One bucket under a fingerprint axis."""

    axis_key: str
    axis_title: str
    group_label: str
    label_display: str
    run_ids: tuple[str, ...]
    pooled_mean_score: float
    cell_count: int
    unstable_cell_events: int
    regressions_targeting_group: int
    mode_gap_events: int


def build_fingerprint_axis_groups(
    snapshots: list[RunSnapshot],
    analysis: LongitudinalAnalysis,
) -> list[FingerprintAxisGroupRow]:
    """Group snapshots by each fingerprint axis; attach instability / regression counts."""
    rows: list[FingerprintAxisGroupRow] = []
    for key, title in FINGERPRINT_COMPARE_AXES:
        buckets = group_snapshots_by(snapshots, key)
        for label in sorted(buckets.keys()):
            snaps = buckets[label]
            rels = _run_relpath_set(snaps)
            rids = {s.run_id for s in snaps}
            cells = sum(len(s.cells) for s in snaps)
            disp = (
                label
                if key == "execution_mode"
                else truncate_fingerprint_display(label, max_len=28)
            )
            rows.append(
                FingerprintAxisGroupRow(
                    axis_key=key,
                    axis_title=title,
                    group_label=label,
                    label_display=disp,
                    run_ids=tuple(sorted(s.run_id for s in snaps)),
                    pooled_mean_score=round(_pooled_mean_cell_score(snaps), 6),
                    cell_count=cells,
                    unstable_cell_events=_count_unstable_for_runs(analysis, rels),
                    regressions_targeting_group=_count_regressions_targeting(analysis, rels),
                    mode_gap_events=_count_mode_gaps_for_runs(analysis, rids),
                ),
            )
    return rows


def build_fingerprint_axis_insights(
    snapshots: list[RunSnapshot],
    analysis: LongitudinalAnalysis,
) -> list[dict[str, Any]]:
    """Highlight score spread and where instability/regressions cluster per axis."""
    insights: list[dict[str, Any]] = []
    for key, title in FINGERPRINT_COMPARE_AXES:
        buckets = group_snapshots_by(snapshots, key)
        if len(buckets) < 2:
            insights.append(
                {
                    "axis_key": key,
                    "axis_title": title,
                    "varied": False,
                    "distinct_groups": len(buckets),
                    "pooled_mean_score_spread": None,
                    "note": "Single group on this axis — no cross-group spread.",
                },
            )
            continue

        stats: list[dict[str, Any]] = []
        for label, snaps in sorted(buckets.items()):
            rels = _run_relpath_set(snaps)
            rids = {s.run_id for s in snaps}
            pm = _pooled_mean_cell_score(snaps)
            u = _count_unstable_for_runs(analysis, rels)
            reg = _count_regressions_targeting(analysis, rels)
            stats.append(
                {
                    "group_label": label,
                    "label_display": (
                        label
                        if key == "execution_mode"
                        else truncate_fingerprint_display(label, max_len=28)
                    ),
                    "pooled_mean_score": round(pm, 6),
                    "unstable_cell_events": u,
                    "regressions_targeting_group": reg,
                    "mode_gap_events": _count_mode_gaps_for_runs(analysis, rids),
                },
            )
        means = [s["pooled_mean_score"] for s in stats]
        spread = max(means) - min(means)
        hi = max(stats, key=lambda x: x["pooled_mean_score"])
        lo = min(stats, key=lambda x: x["pooled_mean_score"])
        max_u = max(stats, key=lambda x: x["unstable_cell_events"])
        note_parts = [
            f"pooled mean score spread {spread:.6f} (lowest `{lo['label_display']}` "
            f"{lo['pooled_mean_score']:.6f} vs highest `{hi['label_display']}` "
            f"{hi['pooled_mean_score']:.6f}).",
        ]
        if max_u["unstable_cell_events"] > 0:
            note_parts.append(
                f"Most judge instability signals ({max_u['unstable_cell_events']}) "
                f"under `{max_u['label_display']}` — compare with score leaders on this axis.",
            )
        if spread >= 0.05 and max_u["unstable_cell_events"] > 0:
            note_parts.append(
                "Large score spread co-occurs with semantic instability somewhere on this axis — "
                "inspect evaluations for those runs.",
            )
        insights.append(
            {
                "axis_key": key,
                "axis_title": title,
                "varied": True,
                "distinct_groups": len(buckets),
                "pooled_mean_score_spread": round(spread, 6),
                "lowest_mean_group": {
                    "label": lo["group_label"],
                    "label_display": lo["label_display"],
                    "pooled_mean_score": lo["pooled_mean_score"],
                },
                "highest_mean_group": {
                    "label": hi["group_label"],
                    "label_display": hi["label_display"],
                    "pooled_mean_score": hi["pooled_mean_score"],
                },
                "groups": stats,
                "note": " ".join(note_parts),
            },
        )
    return insights


def fingerprint_compare_to_json(
    group_rows: list[FingerprintAxisGroupRow],
    insights: list[dict[str, Any]],
) -> dict[str, Any]:
    """Structured block merged into ``campaign-analysis.json``."""
    return {
        "fingerprint_compare_axes": [
            {
                "axis_key": r.axis_key,
                "axis_title": r.axis_title,
                "group_label": r.group_label,
                "label_display": r.label_display,
                "run_ids": list(r.run_ids),
                "pooled_mean_score": r.pooled_mean_score,
                "cell_count": r.cell_count,
                "unstable_cell_events": r.unstable_cell_events,
                "regressions_targeting_group": r.regressions_targeting_group,
                "mode_gap_events": r.mode_gap_events,
            }
            for r in group_rows
        ],
        "fingerprint_axis_insights": insights,
    }


def render_fingerprint_compare_markdown(
    group_rows: list[FingerprintAxisGroupRow],
    insights: list[dict[str, Any]],
) -> str:
    """Markdown section for ``campaign-report.md``."""
    lines = [
        "## Fingerprint axes (longitudinal grouping keys)",
        "",
        "Each **succeeded** member run is grouped using the same keys as "
        "``group_snapshots_by`` in ``pipelines/longitudinal`` "
        "(``provider_config_fingerprint``, ``scoring_config_fingerprint``, "
        "``execution_mode``, ``prompt_registry_state_fingerprint``, "
        "``browser_config_fingerprint``). **Pooled mean** is the mean of all "
        "cell **total_weighted_score** values in that group. **Unstable** counts "
        "longitudinal **FT-JUDGE-UNSTABLE**-class rows for runs in the group. "
        "**Regressions→** counts **to_run** edges (score dropped vs the prior run "
        "for the same benchmark cell) whose destination run lies in this group.",
        "",
    ]

    by_axis: dict[str, list[FingerprintAxisGroupRow]] = {}
    for r in group_rows:
        by_axis.setdefault(r.axis_key, []).append(r)

    for key, title in FINGERPRINT_COMPARE_AXES:
        block = by_axis.get(key, [])
        lines.append(f"### {title} (`{key}`)")
        lines.append("")
        lines.append(
            "| Group (short) | run_ids | Pooled mean | Cells | Unstable | "
            "Regressions→ | Mode gaps |",
        )
        lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: |")
        if not block:
            lines.append("| — | — | — | — | — | — | — |")
        else:
            for r in sorted(block, key=lambda x: x.group_label):
                rids = ", ".join(f"`{x}`" for x in r.run_ids)
                lines.append(
                    f"| `{r.label_display}` | {rids} | {r.pooled_mean_score:.6f} | "
                    f"{r.cell_count} | {r.unstable_cell_events} | "
                    f"{r.regressions_targeting_group} | {r.mode_gap_events} |",
                )
        lines.append("")

    lines.append("### Correlation-style notes (score vs instability)")
    lines.append("")
    for ins in insights:
        varied = ins.get("varied")
        title = str(ins.get("axis_title") or ins.get("axis_key") or "?")
        if not varied:
            lines.append(
                f"- **{title}:** {ins.get('note', '—')}",
            )
            continue
        spread = ins.get("pooled_mean_score_spread")
        sp_s = f"{float(spread):.6f}" if isinstance(spread, (int, float)) else "—"
        lines.append(
            f"- **{title}:** spread **{sp_s}** on pooled mean; "
            f"{ins.get('note', '')}",
        )
    lines.append("")
    return "\n".join(lines)
