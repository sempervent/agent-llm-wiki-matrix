"""Helpers for campaign/pack compare Markdown (no scoring)."""

from __future__ import annotations

from agent_llm_wiki_matrix.benchmark.campaign_compare_core import (
    partition_failure_tag_rows_for_display,
    semantic_instability_rows_all_quiet,
)


def test_semantic_instability_rows_all_quiet_empty() -> None:
    assert semantic_instability_rows_all_quiet([]) is True


def test_semantic_instability_rows_all_quiet_zeros() -> None:
    rows = [
        {
            "scoring_backend": "x",
            "left_unstable_events": 0,
            "right_unstable_events": 0,
            "delta_right_minus_left": 0,
        },
    ]
    assert semantic_instability_rows_all_quiet(rows) is True


def test_semantic_instability_rows_not_quiet() -> None:
    rows = [
        {
            "scoring_backend": "x",
            "left_unstable_events": 1,
            "right_unstable_events": 0,
            "delta_right_minus_left": -1,
        },
    ]
    assert semantic_instability_rows_all_quiet(rows) is False


def test_partition_failure_tags_movement() -> None:
    codes = [
        {
            "code": "FT-A",
            "left_signal_count": 1,
            "right_signal_count": 2,
            "delta_right_minus_left": 1,
        },
        {
            "code": "FT-B",
            "left_signal_count": 0,
            "right_signal_count": 0,
            "delta_right_minus_left": 0,
        },
    ]
    moved, quiet = partition_failure_tag_rows_for_display(codes)
    assert [r["code"] for r in moved] == ["FT-A"]
    assert [r["code"] for r in quiet] == ["FT-B"]
