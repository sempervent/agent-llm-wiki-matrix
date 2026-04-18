"""Campaign-level grouping by longitudinal fingerprint axes.

Uses :func:`group_snapshots_by` and :func:`truncate_fingerprint_display` from
``pipelines.longitudinal`` so campaign comparative reports stay aligned with
``alwm benchmark longitudinal`` grouping.
"""

from __future__ import annotations

from collections import defaultdict
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

# Experiment-config fingerprints (exclude execution_mode for “which knob correlates with drift”).
CONFIG_FINGERPRINT_AXIS_KEYS: frozenset[str] = frozenset(
    {
        "provider_config_fingerprint",
        "scoring_config_fingerprint",
        "prompt_registry_state_fingerprint",
        "browser_config_fingerprint",
    },
)

# Heuristic thresholds for attribution (aggregate bucket stats; not causal inference).
_SPREAD_STRONG = 0.03  # aligned with default longitudinal regression_delta scale
_SPREAD_WEAK = 0.01
# Evidence strength (aggregate cell counts — not statistical power).
_MIN_CELLS_MODERATE = 4
_MIN_CELLS_PER_BUCKET_WEAK = 2


def _instability_rate(unstable: int, cells: int) -> float:
    if cells <= 0:
        return 0.0
    return round(unstable / cells, 6)


def _enriched_groups_from_insight(ins: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for g in ins.get("groups") or []:
        u = int(g.get("unstable_cell_events") or 0)
        cells = int(g.get("cell_count") or 0)
        row = dict(g)
        row["instability_rate"] = _instability_rate(u, cells)
        out.append(row)
    return out


def _compute_evidence_strength(
    *,
    total_cells: int,
    min_bucket_cells: int,
    distinct_groups: int,
) -> tuple[str, list[str]]:
    """Heuristic evidence tier + human-readable limitations (not statistical tests)."""
    notes: list[str] = []
    if distinct_groups < 2:
        return ("weak", ["Only one bucket — no cross-bucket comparison."])
    if total_cells < _MIN_CELLS_MODERATE:
        notes.append(
            f"Total pooled cells ({total_cells}) is below {_MIN_CELLS_MODERATE} — "
            "aggregate means are **easily swayed** by a few cells.",
        )
    if min_bucket_cells < _MIN_CELLS_PER_BUCKET_WEAK:
        notes.append(
            f"Smallest bucket has only {min_bucket_cells} cell(s) — **high variance** in that "
            "bucket mean.",
        )
    if distinct_groups == 2 and total_cells < 8:
        notes.append(
            "Only two buckets and modest cell totals — treat spread as **directional**, not firm.",
        )

    if total_cells >= 12 and min_bucket_cells >= 4:
        return ("moderate", notes)
    if total_cells >= _MIN_CELLS_MODERATE and min_bucket_cells >= _MIN_CELLS_PER_BUCKET_WEAK:
        strength = "moderate" if not notes else "weak"
        return (strength, notes)
    return ("weak", notes)


def classify_axis_difference_attribution(
    ins: dict[str, Any],
    enriched: list[dict[str, Any]],
) -> dict[str, Any]:
    """Classify one varied axis: configuration-like vs instability-like vs mixed/inconclusive.

    Returns a row for ``attribution_by_axis`` in ``fingerprint_axis_interpretation`` JSON.
    Adds ``evidence_strength`` and ``uncertainty_notes`` (optional keys; backward compatible).
    """
    key = str(ins.get("axis_key", ""))
    spread = float(ins.get("pooled_mean_score_spread") or 0.0)
    total_u = sum(int(g.get("unstable_cell_events") or 0) for g in enriched)
    total_cells = sum(int(g.get("cell_count") or 0) for g in enriched)
    min_bucket_cells = min((int(g.get("cell_count") or 0) for g in enriched), default=0)
    distinct_groups = len(enriched)
    max_rate = max((float(g.get("instability_rate") or 0.0) for g in enriched), default=0.0)
    lo = ins.get("lowest_mean_group") or {}
    hi = ins.get("highest_mean_group") or {}
    lo_label = lo.get("label")
    hi_label = hi.get("label")
    max_u = (
        max(enriched, key=lambda x: (x["unstable_cell_events"], x.get("instability_rate", 0.0)))
        if enriched
        else None
    )
    axis_kind = "config_fingerprint" if key in CONFIG_FINGERPRINT_AXIS_KEYS else "execution_mode"

    attribution = "inconclusive"
    confidence = "low"
    rationale = ""

    if not enriched:
        return {
            "axis_key": key,
            "axis_title": ins.get("axis_title", key),
            "axis_kind": axis_kind,
            "attribution": "inconclusive",
            "attribution_label": "inconclusive",
            "confidence": "low",
            "evidence_strength": "weak",
            "uncertainty_notes": ["No per-bucket stats — cannot assess sample sizes or spreads."],
            "rationale": "No per-bucket stats — cannot attribute differences on this axis.",
            "metrics": {
                "pooled_mean_score_spread": round(spread, 6),
                "total_unstable_cell_events": total_u,
                "max_instability_rate_across_buckets": round(max_rate, 6),
                "total_cells_in_axis": total_cells,
                "min_bucket_cell_count": 0,
                "distinct_bucket_count": 0,
            },
        }

    ev_strength, uncertainty_notes = _compute_evidence_strength(
        total_cells=total_cells,
        min_bucket_cells=min_bucket_cells,
        distinct_groups=distinct_groups,
    )
    if spread < _SPREAD_WEAK and total_u == 0:
        attribution = "inconclusive"
        confidence = "low"
        rationale = (
            "**Inconclusive (weak separation):** pooled mean spread is below the weak threshold "
            "and there are no judge-instability rows — any bucket gap may be **noise** at this "
            "cell count; do not treat rank order as meaningful."
        )
    elif spread < _SPREAD_WEAK and total_u > 0:
        attribution = "likely_instability"
        confidence = "moderate" if total_u >= 2 else "low"
        rationale = (
            "**Likely instability-driven:** bucket means are similar in aggregate, but "
            "FT-JUDGE-UNSTABLE-class signals appear — headline scores may reflect "
            "**judge variance** more than a stable configuration effect."
        )
    elif spread >= _SPREAD_STRONG and total_u == 0:
        attribution = "likely_configuration"
        confidence = "moderate" if total_cells >= 4 else "low"
        cfg_note = (
            "manifest fingerprint slices (resolved provider/scoring/registry/browser config)"
            if axis_kind == "config_fingerprint"
            else "execution mode slices (harness/tooling path)"
        )
        rationale = (
            f"**Likely configuration / path-driven:** meaningful pooled mean spread across "
            f"{cfg_note} with **no** judge-instability rows in these buckets — gaps are "
            f"**plausibly stable** vs config/path at this granularity (still not causal)."
        )
    elif spread >= _SPREAD_STRONG and total_u > 0 and max_u is not None:
        mu_label = max_u.get("group_label")
        mu_n = int(max_u.get("unstable_cell_events") or 0)
        if (
            lo_label
            and mu_label == lo_label
            and mu_n > 0
            and hi_label
            and lo_label != hi_label
        ):
            attribution = "mixed_config_and_instability"
            confidence = "low"
            rationale = (
                "**Mixed signals:** meaningful spread **and** the lowest-mean bucket shows the "
                "most instability — a **clean configuration story is not supported** without "
                "per-cell evaluation and provenance."
            )
        elif spread >= _SPREAD_STRONG:
            attribution = "mixed_config_and_instability"
            confidence = "moderate"
            rationale = (
                "**Mixed signals:** meaningful spread co-occurs with judge instability in some "
                "buckets — treat means as **partially** config/path and **partially** judge noise."
            )
    else:
        # Borderline spread
        if total_u == 0:
            attribution = "inconclusive"
            confidence = "low"
            rationale = (
                "**Inconclusive (borderline spread):** spread sits between weak/strong thresholds "
                "with no instability flags — a configuration-driven explanation is **not** "
                "well-supported by aggregate stats alone."
            )
        else:
            attribution = "mixed_config_and_instability"
            confidence = "low"
            rationale = (
                "**Mixed / inconclusive:** borderline spread with instability signals — "
                "aggregate attribution is **ambiguous**."
            )

    if ev_strength == "weak" and confidence == "moderate":
        confidence = "low"
        uncertainty_notes.append(
            "Confidence downgraded to **low** because aggregate evidence strength is **weak**.",
        )

    label_map = {
        "likely_configuration": "configuration-dominant",
        "likely_instability": "instability-dominant",
        "mixed_config_and_instability": "mixed",
        "inconclusive": "inconclusive",
    }

    return {
        "axis_key": key,
        "axis_title": ins.get("axis_title", key),
        "axis_kind": axis_kind,
        "attribution": attribution,
        "attribution_label": label_map.get(attribution, attribution),
        "confidence": confidence,
        "evidence_strength": ev_strength,
        "uncertainty_notes": uncertainty_notes,
        "rationale": rationale,
        "metrics": {
            "pooled_mean_score_spread": round(spread, 6),
            "total_unstable_cell_events": total_u,
            "max_instability_rate_across_buckets": round(max_rate, 6),
            "total_cells_in_axis": total_cells,
            "min_bucket_cell_count": min_bucket_cells,
            "distinct_bucket_count": distinct_groups,
        },
    }


def _signal_class_for_hint_kind(kind: str) -> str:
    if kind == "config_fingerprint_axis_in_top_score_spread":
        return "configuration"
    if kind in (
        "low_mean_bucket_most_judge_instability",
        "high_mean_bucket_most_judge_instability",
        "spread_with_judge_instability",
    ):
        return "instability"
    if kind == "regression_edges_cluster_in_bucket":
        return "mixed"
    return "inconclusive"


def _synthesize_differentiation_overview(attribution_rows: list[dict[str, Any]]) -> str:
    """One short paragraph for reports (explicitly non-causal)."""
    if not attribution_rows:
        return (
            "No fingerprint axis had more than one bucket in this pass, so there is no "
            "cross-bucket spread to attribute."
        )
    weak_axes = [
        r
        for r in attribution_rows
        if str(r.get("evidence_strength") or "") == "weak"
    ]
    weak_prefix = ""
    if weak_axes:
        ak_w = ", ".join(f"`{r.get('axis_key')}`" for r in weak_axes[:4])
        weak_prefix = (
            f"**Evidence is limited on** {ak_w} (small cell counts and/or thin buckets) — "
            "treat all labels below as **triage only**, not confirmation. "
        )

    by_att: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in attribution_rows:
        by_att[str(r.get("attribution", ""))].append(r)
    parts: list[str] = []
    if by_att.get("likely_configuration"):
        ak = ", ".join(f"`{r['axis_key']}`" for r in by_att["likely_configuration"][:3])
        parts.append(
            f"**Likely configuration / path (heuristic):** {ak} show the clearest "
            "**mean separation** with **low** judge-instability signal in aggregate — "
            "consistent with **stable** config/path differences, still **not** proven causation.",
        )
    if by_att.get("likely_instability"):
        ak = ", ".join(f"`{r['axis_key']}`" for r in by_att["likely_instability"][:3])
        parts.append(
            f"**Likely instability-driven:** {ak} show instability signals without strong mean "
            "separation — **do not** rank buckets by score alone.",
        )
    if by_att.get("mixed_config_and_instability"):
        ak = ", ".join(f"`{r['axis_key']}`" for r in by_att["mixed_config_and_instability"][:3])
        parts.append(
            f"**Mixed signals:** {ak} combine spread with instability — **cannot** separate "
            "clean configuration effects from judge noise at bucket level.",
        )
    if by_att.get("inconclusive"):
        if not parts:
            parts.append(
                "**Inconclusive:** spreads are small/borderline or evidence is thin — this pass "
                "does **not** support a firm story about why buckets differ.",
            )
        else:
            parts.append(
                "Other axes are **inconclusive**; down-rank those rows when prioritizing "
                "follow-up.",
            )
    body = " ".join(parts)
    return (weak_prefix + body).strip()


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
            cell_ct = sum(len(s.cells) for s in snaps)
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
                    "cell_count": cell_ct,
                    "run_count": len(snaps),
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


def build_fingerprint_axis_interpretation(
    snapshots: list[RunSnapshot],
    analysis: LongitudinalAnalysis,
    insights: list[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate interpretation: spread ranking, instability hotspots, heuristic drift hints.

    Uses the same buckets as ``build_fingerprint_axis_insights`` / ``group_snapshots_by``.
    """
    _ = snapshots  # reserved — kept for signature parity with callers that reload snapshots
    ranking: list[dict[str, Any]] = []
    hotspots: list[dict[str, Any]] = []
    hints: list[dict[str, Any]] = []

    varied_insights = [i for i in insights if i.get("varied")]
    spread_sorted = sorted(
        varied_insights,
        key=lambda x: float(x.get("pooled_mean_score_spread") or 0.0),
        reverse=True,
    )
    for rank, ins in enumerate(spread_sorted, start=1):
        sp = ins.get("pooled_mean_score_spread")
        ranking.append(
            {
                "rank": rank,
                "axis_key": ins["axis_key"],
                "axis_title": ins.get("axis_title", ins["axis_key"]),
                "pooled_mean_score_spread": sp,
                "distinct_groups": ins.get("distinct_groups"),
                "lowest_mean_group": ins.get("lowest_mean_group"),
                "highest_mean_group": ins.get("highest_mean_group"),
            },
        )

    attribution_by_axis = [
        classify_axis_difference_attribution(ins, _enriched_groups_from_insight(ins))
        for ins in varied_insights
    ]

    for ins in varied_insights:
        key = ins["axis_key"]
        enriched = _enriched_groups_from_insight(ins)
        if not enriched:
            continue
        max_ev = max(enriched, key=lambda x: (x["unstable_cell_events"], x["instability_rate"]))
        max_rate = max(enriched, key=lambda x: (x["instability_rate"], x["unstable_cell_events"]))
        hotspots.append(
            {
                "axis_key": key,
                "axis_title": ins.get("axis_title", key),
                "most_unstable_events": {
                    "group_label": max_ev["group_label"],
                    "label_display": max_ev["label_display"],
                    "unstable_cell_events": max_ev["unstable_cell_events"],
                    "cell_count": max_ev.get("cell_count", 0),
                    "instability_rate": max_ev["instability_rate"],
                },
                "highest_instability_rate": {
                    "group_label": max_rate["group_label"],
                    "label_display": max_rate["label_display"],
                    "unstable_cell_events": max_rate["unstable_cell_events"],
                    "cell_count": max_rate.get("cell_count", 0),
                    "instability_rate": max_rate["instability_rate"],
                },
            },
        )

        lo = ins.get("lowest_mean_group")
        hi = ins.get("highest_mean_group")
        max_u_label = max_ev["group_label"]
        spread = float(ins.get("pooled_mean_score_spread") or 0.0)
        if lo and lo.get("label") == max_u_label and max_ev["unstable_cell_events"] > 0:
            hints.append(
                {
                    "kind": "low_mean_bucket_most_judge_instability",
                    "axis_key": key,
                    "severity": "watch",
                    "summary": (
                        "The lowest pooled-mean bucket on this axis also carries the most "
                        "judge-instability signals — score gaps may be confounded by judge noise."
                    ),
                    "bucket_label_display": max_ev["label_display"],
                },
            )
        if hi and hi.get("label") == max_u_label and max_ev["unstable_cell_events"] > 0:
            hints.append(
                {
                    "kind": "high_mean_bucket_most_judge_instability",
                    "axis_key": key,
                    "severity": "note",
                    "summary": (
                        "The highest pooled-mean bucket also shows the most judge-instability "
                        "signals — verify rubric grounding for those runs."
                    ),
                    "bucket_label_display": max_ev["label_display"],
                },
            )
        if spread >= 0.03 and max_ev["unstable_cell_events"] > 0:
            hints.append(
                {
                    "kind": "spread_with_judge_instability",
                    "axis_key": key,
                    "severity": "watch",
                    "summary": (
                        f"Non-trivial pooled mean spread ({spread:.6f}) co-occurs with judge "
                        "instability on this axis — compare evaluations and provenance across "
                        "buckets."
                    ),
                    "pooled_mean_score_spread": round(spread, 6),
                },
            )

    seen_cfg_rank: set[str] = set()
    for rank, row in enumerate(ranking[:3], start=1):
        ak = row["axis_key"]
        if ak in CONFIG_FINGERPRINT_AXIS_KEYS and ak not in seen_cfg_rank:
            seen_cfg_rank.add(ak)
            hints.append(
                {
                    "kind": "config_fingerprint_axis_in_top_score_spread",
                    "axis_key": ak,
                    "severity": "note",
                    "rank_in_spread": rank,
                    "summary": (
                        "This experiment-config fingerprint axis is among the top score-spread "
                        "drivers — compare manifest comparison_fingerprints and member manifests."
                    ),
                },
            )

    best_reg: tuple[int, str, dict[str, Any]] | None = None
    for ins in varied_insights:
        for g in ins.get("groups") or []:
            rg = int(g.get("regressions_targeting_group") or 0)
            if best_reg is None or rg > best_reg[0]:
                best_reg = (rg, ins["axis_key"], g)
    if best_reg is not None and best_reg[0] > 0:
        _n, axis_k, top_reg = best_reg
        hints.append(
            {
                "kind": "regression_edges_cluster_in_bucket",
                "axis_key": axis_k,
                "severity": "watch",
                "summary": (
                    "Run-over-run regression edges (destination run in bucket) cluster most "
                    f"often under `{top_reg['label_display']}` on this axis."
                ),
                "regressions_targeting_group": best_reg[0],
                "bucket_label_display": top_reg["label_display"],
            },
        )

    for h in hints:
        k = str(h.get("kind", ""))
        h.setdefault("signal_class", _signal_class_for_hint_kind(k))

    interpretation_caveats = [
        "Attribution labels describe **aggregate bucket patterns**, not proven causation.",
        "Confidence and **evidence_strength** are heuristics from cell/run counts — **not** "
        "statistical significance.",
        "Confidence is **low** when few member runs, few cells per bucket, or "
        "**evidence_strength** is **weak**.",
        "Compare `comparison_fingerprints` on each member `manifest.json` before trusting "
        "cross-run score deltas.",
        "**inconclusive** / **mixed** are expected when sample sizes are small or instability "
        "co-occurs with spread.",
    ]

    return {
        "schema_version": 1,
        "differentiation_overview": _synthesize_differentiation_overview(attribution_by_axis),
        "attribution_by_axis": attribution_by_axis,
        "interpretation_caveats": interpretation_caveats,
        "score_spread_ranking": ranking,
        "instability_hotspots": hotspots,
        "drift_correlation_hints": hints,
        "notes": [
            "Pooled mean is over all cell total_weighted_score values in each fingerprint bucket.",
            "Judge instability counts FT-JUDGE-UNSTABLE-class rows whose run is in the bucket.",
            "Hints are heuristic; confirm with member manifests and evaluation.json.",
            "attribution / signal_class fields are non-causal heuristics for triage only.",
            "attribution_label categorizes likely_configuration / likely_instability / mixed / "
            "inconclusive for display; evidence_strength reflects aggregate cell counts only.",
        ],
    }


def render_fingerprint_axis_interpretation_markdown(interpretation: dict[str, Any]) -> str:
    """Markdown fragment: attribution, spread ranking, hotspots, grouped hints."""
    lines = [
        "### Axis interpretation (why buckets differ)",
        "",
        "These rows summarize **aggregate** differences across fingerprint buckets (same keys as "
        "``group_snapshots_by``). Labels distinguish **likely configuration-driven** vs "
        "**likely instability-driven** vs **mixed** vs **inconclusive** patterns — they are "
        "**not** causal claims and can be wrong when cell counts are small.",
        "",
        "**Reading the categories:** **configuration-dominant** = spread with little instability "
        "signal; **instability-dominant** = instability without strong mean separation; "
        "**mixed** = spread and instability overlap; **inconclusive** = weak/borderline evidence.",
        "",
    ]
    caveats = interpretation.get("interpretation_caveats") or []
    if caveats:
        lines.append("> **Uncertainty & limits:**")
        for c in caveats:
            lines.append(f"> - {c}")
        lines.append("")

    overview = interpretation.get("differentiation_overview")
    if isinstance(overview, str) and overview.strip():
        lines.append("#### Summary")
        lines.append("")
        lines.append(overview.strip())
        lines.append("")

    attr_rows = interpretation.get("attribution_by_axis") or []
    if attr_rows:
        lines.append("#### Per-axis attribution (heuristic)")
        lines.append("")
        lines.append(
            "| Axis | Kind | Pattern | Evidence | Conf. | Cells (min bucket) |",
        )
        lines.append("| --- | --- | --- | --- | --- | ---: |")
        driver_labels = {
            "likely_configuration": "**Config-driven** (heuristic)",
            "likely_instability": "**Instability-driven** (heuristic)",
            "mixed_config_and_instability": "**Mixed signals**",
            "inconclusive": "**Inconclusive**",
        }
        for row in attr_rows:
            ak = row.get("axis_key", "")
            kind = str(row.get("axis_kind", ""))
            att = str(row.get("attribution", ""))
            conf = str(row.get("confidence", ""))
            evs = str(row.get("evidence_strength", "—"))
            driver = driver_labels.get(att, att)
            m = row.get("metrics") or {}
            min_b = m.get("min_bucket_cell_count")
            min_s = str(min_b) if isinstance(min_b, int) else "—"
            lines.append(
                f"| `{ak}` | `{kind}` | {driver} | {evs} | {conf} | {min_s} |",
            )
        lines.append("")
        lines.append("**Rationale & sample limits (per axis):**")
        lines.append("")
        for row in attr_rows:
            ak = row.get("axis_key", "")
            rat = str(row.get("rationale", ""))
            un = row.get("uncertainty_notes") or []
            lines.append(f"- **`{ak}`:** {rat}")
            if isinstance(un, list) and un:
                for note in un:
                    lines.append(f"  - _Limit:_ {note}")
        lines.append("")

    rank = interpretation.get("score_spread_ranking") or []
    if not rank:
        lines.append("_No multi-bucket axes — nothing to rank._")
        lines.append("")
    else:
        lines.append("#### Score spread (ranked by pooled mean gap across buckets)")
        lines.append("")
        lines.append("| Rank | Axis | Spread | Lowest mean (bucket) | Highest mean (bucket) |")
        lines.append("| ---: | --- | ---: | --- | --- |")
        for r in rank:
            lo = r.get("lowest_mean_group") or {}
            hi = r.get("highest_mean_group") or {}
            sp = r.get("pooled_mean_score_spread")
            sp_s = f"{float(sp):.6f}" if isinstance(sp, (int, float)) else "—"
            lo_d = str(lo.get("label_display") or "—")
            hi_d = str(hi.get("label_display") or "—")
            lines.append(
                f"| {r.get('rank')} | `{r.get('axis_key')}` | {sp_s} | `{lo_d}` | `{hi_d}` |",
            )
        lines.append("")

    hot = interpretation.get("instability_hotspots") or []
    if not hot:
        lines.append("#### Instability hotspots by axis")
        lines.append("")
        lines.append("_No varied fingerprint axes._")
        lines.append("")
    else:
        lines.append("#### Instability hotspots (judge instability vs bucket size)")
        lines.append("")
        lines.append(
            "| Axis | Most events (bucket) | Events | Cells | Rate | "
            "Highest rate (bucket) | Rate |",
        )
        lines.append("| --- | --- | ---: | ---: | ---: | --- | ---: |")
        for h in hot:
            me = h.get("most_unstable_events") or {}
            hr = h.get("highest_instability_rate") or {}
            lines.append(
                f"| `{h.get('axis_key')}` | `{me.get('label_display')}` | "
                f"{me.get('unstable_cell_events')} | {me.get('cell_count')} | "
                f"{me.get('instability_rate', 0):.6f} | "
                f"`{hr.get('label_display')}` | {hr.get('instability_rate', 0):.6f} |",
            )
        lines.append("")

    hints = interpretation.get("drift_correlation_hints") or []
    lines.append("#### Raw signals (secondary checks)")
    lines.append("")
    lines.append(
        "_Cross-checks beyond the attribution table — grouped by **signal_class** "
        "(configuration vs instability vs mixed). Still heuristic._",
    )
    lines.append("")
    if not hints:
        lines.append("_No secondary hints for this dataset._")
    else:
        dedup: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()
        for h in hints:
            sig = (str(h.get("kind")), str(h.get("axis_key")), str(h.get("summary", ""))[:120])
            if sig in seen:
                continue
            seen.add(sig)
            dedup.append(h)
        by_class: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for h in dedup:
            sc = str(h.get("signal_class") or "inconclusive")
            by_class[sc].append(h)
        order = ("configuration", "instability", "mixed", "inconclusive")
        titles = {
            "configuration": "Configuration / spread structure",
            "instability": "Judge instability co-location",
            "mixed": "Mixed (e.g. regressions across runs)",
            "inconclusive": "Other",
        }
        for sc in order:
            bucket = by_class.get(sc)
            if not bucket:
                continue
            lines.append(f"##### {titles.get(sc, sc)}")
            lines.append("")
            for h in bucket:
                kind = h.get("kind", "?")
                sev = h.get("severity", "note")
                ax = h.get("axis_key", "")
                summ = h.get("summary", "")
                lines.append(f"- **`{kind}`** (`{ax}`, _{sev}_): {summ}")
            lines.append("")
    lines.append("")
    return "\n".join(lines)


def fingerprint_compare_to_json(
    group_rows: list[FingerprintAxisGroupRow],
    insights: list[dict[str, Any]],
    *,
    interpretation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Structured block merged into ``campaign-analysis.json``."""
    out: dict[str, Any] = {
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
    if interpretation is not None:
        out["fingerprint_axis_interpretation"] = interpretation
    return out


def render_fingerprint_compare_markdown(
    group_rows: list[FingerprintAxisGroupRow],
    insights: list[dict[str, Any]],
    *,
    interpretation: dict[str, Any] | None = None,
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
        "_Axis interpretation below states **evidence strength** (aggregate cell counts) and "
        "**uncertainty** explicitly — small buckets or few cells mean labels are **tentative**._",
        "",
    ]
    if interpretation:
        lines.append(render_fingerprint_axis_interpretation_markdown(interpretation).rstrip())
        lines.append("")

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
