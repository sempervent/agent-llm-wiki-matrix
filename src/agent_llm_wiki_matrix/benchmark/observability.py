"""Markdown snippets for benchmark runtime / retry summaries (manifest + report footers)."""

from __future__ import annotations

from agent_llm_wiki_matrix.models import (
    BenchmarkRetrySummaryV1,
    BenchmarkRunTimingSummaryV1,
    CampaignAggregatedRuntimeV1,
)


def render_benchmark_runtime_markdown(
    timing: BenchmarkRunTimingSummaryV1,
    retry: BenchmarkRetrySummaryV1 | None,
) -> str:
    """Append to reports/report.md after the main report body."""
    lines = [
        "",
        "## Runtime observability",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| started_at_utc | `{timing.started_at_utc}` |",
        f"| finished_at_utc | `{timing.finished_at_utc}` |",
        f"| duration_seconds | {timing.duration_seconds:.6f} |",
        f"| browser_phase_seconds | {timing.browser_phase_seconds:.6f} |",
        f"| provider_completion_seconds | {timing.provider_completion_seconds:.6f} |",
        f"| evaluation_phase_seconds | {timing.evaluation_phase_seconds:.6f} |",
        f"| judge_phase_seconds | {timing.judge_phase_seconds:.6f} |",
        "",
    ]
    if retry is not None:
        lines.extend(
            [
                "### Retry and judge summary",
                "",
                "| Field | Value |",
                "| --- | --- |",
                f"| retry_policy_max_attempts | {retry.retry_policy_max_attempts!s} |",
                f"| total_judge_invocations | {retry.total_judge_invocations} |",
                f"| cells_with_judge_parse_fallback | {retry.cells_with_judge_parse_fallback} |",
                "",
            ],
        )
    return "\n".join(lines)


def render_campaign_aggregated_runtime_markdown(agg: CampaignAggregatedRuntimeV1) -> str:
    """Section for campaign-summary.md when aggregated_runtime is set."""
    return "\n".join(
        [
            "",
            "## Aggregated runtime (member manifests)",
            "",
            (
                "Sums of per-run `runtime_summary` fields for successful member runs "
                "that recorded timing."
            ),
            "",
            "| Metric | Value |",
            "| --- | --- |",
            f"| member_runs_timed | {agg.member_runs_timed} |",
            f"| total_browser_phase_seconds | {agg.total_browser_phase_seconds:.6f} |",
            f"| total_provider_completion_seconds | {agg.total_provider_completion_seconds:.6f} |",
            f"| total_evaluation_phase_seconds | {agg.total_evaluation_phase_seconds:.6f} |",
            f"| total_judge_phase_seconds | {agg.total_judge_phase_seconds:.6f} |",
            f"| total_judge_invocations | {agg.total_judge_invocations} |",
            f"| cells_with_judge_parse_fallback | {agg.cells_with_judge_parse_fallback} |",
            "",
        ],
    )
