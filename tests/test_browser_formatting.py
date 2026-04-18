"""Markdown formatting for browser evidence (deterministic fixtures)."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_llm_wiki_matrix.benchmark.campaign_browser_evidence import (
    render_campaign_browser_cross_run_comparison,
)
from agent_llm_wiki_matrix.browser.formatting import (
    extension_digest_short,
    format_extensions_compact_markdown,
    format_extensions_markdown,
    render_benchmark_browser_evidence_markdown,
    render_dom_excerpts_markdown,
    render_screenshots_markdown,
    signals_digest_line,
)
from agent_llm_wiki_matrix.browser.load import load_browser_evidence

_REPO = Path(__file__).resolve().parents[1]


def test_render_dom_excerpts_includes_fenced_html_for_checkout_fixture() -> None:
    ev = load_browser_evidence(_REPO / "fixtures/browser_evidence/v1/checkout_flow.json")
    md = render_dom_excerpts_markdown(ev.dom_excerpts)
    assert "| # | Label |" in md
    assert "```html" in md
    assert "button" in md.lower()


def test_render_screenshots_table_columns() -> None:
    ev = load_browser_evidence(_REPO / "fixtures/browser_evidence/v1/checkout_flow.json")
    md = render_screenshots_markdown(ev.screenshots)
    assert "viewport" in md.lower() or "element" in md.lower()
    assert "390×844" in md


def test_render_campaign_cross_run_comparison_two_runs() -> None:
    ev_c = load_browser_evidence(_REPO / "fixtures/browser_evidence/v1/checkout_flow.json")
    ev_f = load_browser_evidence(_REPO / "fixtures/browser_evidence/v1/form_validation.json")
    items = [
        ("r0", "b0", "su/checkout.yaml", "c1", "file", ev_c),
        ("r1", "b1", "su/form.yaml", "c1", "file", ev_f),
    ]
    md = render_campaign_browser_cross_run_comparison(items)
    assert "### Cross-run contrast" in md
    assert "`r0`" in md and "`r1`" in md


def test_browser_evidence_compare_example_campaign_report_on_disk() -> None:
    p = _REPO / "examples/campaign_runs/browser_evidence_compare/reports/campaign-report.md"
    md = p.read_text(encoding="utf-8")
    assert "## Browser evidence (member runs)" in md
    assert "Cross-run contrast" in md
    assert "| Signals |" in md


def test_extension_digest_short_checkout_fixture() -> None:
    ev = load_browser_evidence(_REPO / "fixtures/browser_evidence/v1/checkout_flow.json")
    assert ev.extensions
    d = extension_digest_short(ev.extensions)
    assert "checkout_flow" in d
    assert "net" in d.lower() or "14" in d


def test_signals_digest_line_counts() -> None:
    ev = load_browser_evidence(_REPO / "fixtures/browser_evidence/v1/checkout_flow.json")
    s = signals_digest_line(ev)
    assert "nav×3" in s
    assert "dom×2" in s
    assert "shot×2" in s
    assert "snap" in s


def test_format_extensions_compact_markdown_table() -> None:
    ev = load_browser_evidence(_REPO / "fixtures/browser_evidence/v1/checkout_flow.json")
    md = format_extensions_compact_markdown(ev.extensions)
    assert "| Extension block | Summary |" in md
    assert "**network**" in md
    assert "accessibility" in md.lower()


def test_format_extensions_markdown_network_block() -> None:
    ev = load_browser_evidence(_REPO / "fixtures/browser_evidence/v1/checkout_flow.json")
    assert ev.extensions
    lines = format_extensions_markdown(ev.extensions)
    text = "\n".join(lines)
    assert "network" in text.lower()
    assert "requests_total" in text or "14" in text


def test_benchmark_report_markdown_full_includes_detail_sections() -> None:
    from agent_llm_wiki_matrix.browser.formatting import (
        browser_evidence_report_row_from_evidence,
    )

    ev = load_browser_evidence(_REPO / "fixtures/browser_evidence/v1/form_validation.json")
    row = browser_evidence_report_row_from_evidence(
        cell_id="v-form__p-one",
        runner="file",
        evidence=ev,
    )
    md = render_benchmark_browser_evidence_markdown([(row, ev)])
    assert "### Browser traces (DOM, screenshots, extensions)" in md
    assert "**DOM excerpts**" in md
    assert "**Screenshots**" in md
    assert "**Extensions (structured)**" in md
    assert "| Signals |" in md
    assert "| Extension digest |" in md


def test_browser_traces_compare_benchmark_writes_legible_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALWM_FIXTURE_MODE", "1")
    from agent_llm_wiki_matrix.benchmark import load_benchmark_definition, run_benchmark

    dfn = load_benchmark_definition(_REPO / "fixtures/benchmarks/browser_traces_compare.v1.yaml")
    out = tmp_path / "run"
    run_benchmark(
        dfn,
        repo_root=_REPO,
        output_dir=out,
        created_at="1970-01-01T00:00:00Z",
        run_id="btc",
        provider_yaml=None,
        environ={"ALWM_FIXTURE_MODE": "1"},
        fixture_mode_force_mock=True,
    )
    report_md = (out / "reports" / "report.md").read_text(encoding="utf-8")
    assert "checkout_flow" in report_md or "evidence.checkout_flow" in report_md
    assert "form_validation" in report_md or "evidence.form_validation" in report_md
    assert "### Browser traces (DOM, screenshots, extensions)" in report_md
    assert "Playwright" in report_md
    assert "MCP" in report_md
