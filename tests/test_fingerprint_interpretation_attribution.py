"""Unit tests for fingerprint axis attribution heuristics (non-scoring)."""

from __future__ import annotations

from agent_llm_wiki_matrix.benchmark.campaign_fingerprint_compare import (
    classify_axis_difference_attribution,
)


def _ins(
    *,
    axis_key: str,
    spread: float,
    groups: list[dict],
) -> dict:
    return {
        "axis_key": axis_key,
        "axis_title": "T",
        "varied": True,
        "pooled_mean_score_spread": spread,
        "groups": groups,
        "lowest_mean_group": {"label": groups[0]["group_label"]},
        "highest_mean_group": {"label": groups[-1]["group_label"]},
    }


def test_likely_configuration_high_spread_no_instability() -> None:
    enriched = [
        {
            "group_label": "a",
            "unstable_cell_events": 0,
            "cell_count": 4,
            "instability_rate": 0.0,
        },
        {
            "group_label": "b",
            "unstable_cell_events": 0,
            "cell_count": 4,
            "instability_rate": 0.0,
        },
    ]
    ins = _ins(
        axis_key="provider_config_fingerprint",
        spread=0.12,
        groups=enriched,
    )
    row = classify_axis_difference_attribution(ins, enriched)
    assert row["attribution"] == "likely_configuration"
    assert row["attribution_label"] == "configuration-dominant"
    assert row["confidence"] == "moderate"
    assert row["axis_kind"] == "config_fingerprint"
    assert row["evidence_strength"] in ("moderate", "weak")
    assert row["metrics"]["min_bucket_cell_count"] == 4


def test_likely_instability_tiny_spread_with_events() -> None:
    enriched = [
        {
            "group_label": "a",
            "unstable_cell_events": 2,
            "cell_count": 4,
            "instability_rate": 0.5,
        },
        {
            "group_label": "b",
            "unstable_cell_events": 0,
            "cell_count": 4,
            "instability_rate": 0.0,
        },
    ]
    ins = _ins(axis_key="execution_mode", spread=0.005, groups=enriched)
    row = classify_axis_difference_attribution(ins, enriched)
    assert row["attribution"] == "likely_instability"
    assert row["attribution_label"] == "instability-dominant"
    assert row["axis_kind"] == "execution_mode"


def test_mixed_low_bucket_most_unstable() -> None:
    enriched = [
        {
            "group_label": "low",
            "unstable_cell_events": 3,
            "cell_count": 3,
            "instability_rate": 1.0,
        },
        {
            "group_label": "high",
            "unstable_cell_events": 0,
            "cell_count": 3,
            "instability_rate": 0.0,
        },
    ]
    ins = _ins(
        axis_key="scoring_config_fingerprint",
        spread=0.2,
        groups=enriched,
    )
    ins["lowest_mean_group"] = {"label": "low"}
    ins["highest_mean_group"] = {"label": "high"}
    row = classify_axis_difference_attribution(ins, enriched)
    assert row["attribution"] == "mixed_config_and_instability"
    assert row["attribution_label"] == "mixed"
    assert row["confidence"] == "low"


def test_inconclusive_tiny_spread_no_events() -> None:
    enriched = [
        {"group_label": "a", "unstable_cell_events": 0, "cell_count": 2, "instability_rate": 0.0},
        {"group_label": "b", "unstable_cell_events": 0, "cell_count": 2, "instability_rate": 0.0},
    ]
    ins = _ins(axis_key="browser_config_fingerprint", spread=0.005, groups=enriched)
    row = classify_axis_difference_attribution(ins, enriched)
    assert row["attribution"] == "inconclusive"
    assert row["attribution_label"] == "inconclusive"


def test_empty_enriched_returns_inconclusive_with_zero_buckets() -> None:
    row = classify_axis_difference_attribution(
        {"axis_key": "provider_config_fingerprint", "axis_title": "P"},
        [],
    )
    assert row["attribution"] == "inconclusive"
    assert row["metrics"]["distinct_bucket_count"] == 0
    assert row["uncertainty_notes"]
