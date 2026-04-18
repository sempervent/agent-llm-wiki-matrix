"""Repeat semantic judge runs: aggregation, disagreement metrics, confidence flags."""

from __future__ import annotations

import statistics
from typing import Any, Literal

SemanticAggregationStrategy = Literal["mean", "median", "trimmed_mean"]


def trimmed_mean(vals: list[float], trim_fraction: float) -> float:
    """Mean after removing ``trim_fraction`` from each tail (sorted)."""
    if not vals:
        msg = "trimmed_mean requires non-empty vals"
        raise ValueError(msg)
    if trim_fraction <= 0:
        return sum(vals) / len(vals)
    s = sorted(vals)
    n = len(s)
    k = int(n * trim_fraction)
    if 2 * k >= n:
        return sum(s) / n
    core = s[k : n - k]
    return sum(core) / len(core)


def aggregate_values(
    values: list[float],
    strategy: SemanticAggregationStrategy,
    trim_fraction: float,
) -> float:
    if not values:
        msg = "aggregate_values requires non-empty values"
        raise ValueError(msg)
    if strategy == "mean":
        return sum(values) / len(values)
    if strategy == "median":
        return float(statistics.median(values))
    return trimmed_mean(values, trim_fraction)


def aggregate_criterion_scores(
    runs: list[dict[str, float]],
    criterion_ids: list[str],
    strategy: SemanticAggregationStrategy,
    trim_fraction: float,
) -> dict[str, float]:
    out: dict[str, float] = {}
    for cid in criterion_ids:
        vals = [r[cid] for r in runs if cid in r]
        if len(vals) != len(runs):
            msg = f"missing criterion {cid!r} in some runs"
            raise ValueError(msg)
        out[cid] = round(aggregate_values(vals, strategy, trim_fraction), 6)
    return out


def criterion_disagreement(values: list[float]) -> tuple[float, float, float, float]:
    """Return min, max, range, population stdev."""
    if not values:
        return 0.0, 0.0, 0.0, 0.0
    lo, hi = min(values), max(values)
    rng = hi - lo
    stdev = statistics.pstdev(values) if len(values) > 1 else 0.0
    return lo, hi, rng, stdev


def build_disagreement_summary(
    runs: list[dict[str, float]],
    criterion_ids: list[str],
    weights: dict[str, float],
) -> dict[str, Any]:
    """Per-criterion stats, mean stdev across criteria, total weighted score per run."""
    per: dict[str, dict[str, float]] = {}
    stdevs: list[float] = []
    for cid in criterion_ids:
        vals = [r[cid] for r in runs]
        lo, hi, rng, stdev = criterion_disagreement(vals)
        per[cid] = {
            "min": round(lo, 6),
            "max": round(hi, 6),
            "score_range": round(rng, 6),
            "stdev": round(stdev, 6),
        }
        stdevs.append(stdev)
    mean_stdev = sum(stdevs) / len(stdevs) if stdevs else 0.0
    tws: list[float] = []
    weight_sum = sum(weights.values())
    for r in runs:
        total = sum(weights[c] * r[c] for c in criterion_ids) / weight_sum
        tws.append(round(total, 6))
    tw_stdev = statistics.pstdev(tws) if len(tws) > 1 else 0.0
    max_range = max(per[c]["score_range"] for c in criterion_ids)
    return {
        "per_criterion": per,
        "mean_stdev_across_criteria": round(mean_stdev, 6),
        "total_weighted_per_run": tws,
        "total_weighted_stdev": round(tw_stdev, 6),
        "max_range_across_criteria": round(max_range, 6),
    }


def assess_low_confidence(
    *,
    per_criterion_range: dict[str, dict[str, float]],
    mean_stdev_across_criteria: float,
    total_weighted_stdev: float,
    max_range_across_criteria: float,
    max_criterion_range: float | None,
    max_criterion_stdev: float | None,
    max_mean_criterion_stdev: float | None,
    max_total_weighted_stdev: float | None,
) -> tuple[bool, list[str]]:
    flags: list[str] = []
    if max_criterion_range is not None and max_range_across_criteria > max_criterion_range:
        flags.append(
            f"max_criterion_range {max_range_across_criteria:.6f} > "
            f"threshold {max_criterion_range:g}",
        )
    if max_criterion_stdev is not None:
        for cid, row in per_criterion_range.items():
            if row["stdev"] > max_criterion_stdev:
                flags.append(
                    f"criterion {cid!r} stdev {row['stdev']:.6f} > {max_criterion_stdev:g}",
                )
                break
    if (
        max_mean_criterion_stdev is not None
        and mean_stdev_across_criteria > max_mean_criterion_stdev
    ):
        flags.append(
            f"mean_criterion_stdev {mean_stdev_across_criteria:.6f} > {max_mean_criterion_stdev:g}",
        )
    if max_total_weighted_stdev is not None and total_weighted_stdev > max_total_weighted_stdev:
        flags.append(
            f"total_weighted_stdev {total_weighted_stdev:.6f} > {max_total_weighted_stdev:g}",
        )
    return bool(flags), flags
