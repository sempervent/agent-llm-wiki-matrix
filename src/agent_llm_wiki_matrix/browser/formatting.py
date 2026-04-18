"""Serialize browser evidence for prompts and markdown reports."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from agent_llm_wiki_matrix.browser.models import BrowserEvidence

_PROMPT_HTML_SNIPPET_MAX = 720


def _truncate_html_snippet(s: str, *, max_len: int = _PROMPT_HTML_SNIPPET_MAX) -> str:
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "…"


def _format_extensions_for_prompt(ext: dict[str, Any]) -> list[str]:
    """Render known extension keys readably; dump the rest as sorted JSON."""
    lines: list[str] = []
    known_order = (
        "fixture_profile",
        "structured_capture_version",
        "runner",
        "trace_digest",
        "network",
        "accessibility",
        "performance",
    )
    consumed: set[str] = set()
    for key in known_order:
        if key not in ext:
            continue
        consumed.add(key)
        val = ext[key]
        if key == "network" and isinstance(val, dict):
            lines.append("- **network:**")
            for nk, nv in sorted(val.items()):
                lines.append(f"  - {nk}: {nv}")
        elif key == "accessibility" and isinstance(val, dict):
            lines.append("- **accessibility:**")
            for ak, av in sorted(val.items()):
                lines.append(f"  - {ak}: {av}")
        elif key == "performance" and isinstance(val, dict):
            lines.append("- **performance:**")
            for pk, pv in sorted(val.items()):
                lines.append(f"  - {pk}: {pv}")
        else:
            lines.append(f"- **{key}:** {val!r}")

    remainder = {k: v for k, v in ext.items() if k not in consumed}
    if remainder:
        lines.append("- **other (JSON):**")
        lines.append(json.dumps(remainder, sort_keys=True, ensure_ascii=False))
    return lines


def evidence_to_prompt_block(evidence: BrowserEvidence) -> str:
    """Stable, human-readable block suitable to append to an LLM prompt."""
    lines: list[str] = [
        "### Browser evidence (structured)",
        f"- **id:** {evidence.id}",
    ]
    if evidence.title:
        lines.append(f"- **title:** {evidence.title}")
    lines.append("- **navigation:**")
    for step in evidence.navigation_sequence:
        parts = [step.url]
        if step.title:
            parts.append(f"“{step.title}”")
        if step.action:
            parts.append(f"[{step.action}]")
        lines.append(f"  - {' '.join(parts)}")
    if evidence.console_messages:
        lines.append("- **console:**")
        for m in evidence.console_messages:
            lines.append(f"  - [{m.level}] {m.text}")
    if evidence.dom_excerpts:
        lines.append("- **dom_excerpts:**")
        for ex in evidence.dom_excerpts:
            label = ex.label or "(excerpt)"
            sel = f" `{ex.selector}`" if ex.selector else ""
            meta: list[str] = []
            if ex.aria_role:
                meta.append(f"aria_role={ex.aria_role}")
            if ex.accessibility_name:
                meta.append(f"a11y_name={ex.accessibility_name!r}")
            if ex.dom_order is not None:
                meta.append(f"order={ex.dom_order}")
            meta_s = f" ({'; '.join(meta)})" if meta else ""
            lines.append(f"  - **{label}**{sel}{meta_s}")
            if ex.visible_text:
                lines.append(f"    - visible: {ex.visible_text}")
            if ex.html_snippet:
                shown = _truncate_html_snippet(ex.html_snippet)
                suffix = " _(truncated in prompt)_" if shown != ex.html_snippet else ""
                lines.append(f"    - html: {shown}{suffix}")
    if evidence.screenshots:
        lines.append("- **screenshots:**")
        for s in evidence.screenshots:
            bits: list[str] = []
            if s.sequence is not None:
                bits.append(f"#{s.sequence}")
            if s.capture_scope:
                bits.append(s.capture_scope)
            if s.target_selector:
                bits.append(f"target `{s.target_selector}`")
            if s.relpath:
                bits.append(f"path `{s.relpath}`")
            if s.content_sha256:
                bits.append(f"sha256 `{s.content_sha256}`")
            if s.viewport_width and s.viewport_height:
                bits.append(f"{s.viewport_width}×{s.viewport_height}")
            if s.device_pixel_ratio is not None:
                bits.append(f"dpr {s.device_pixel_ratio}")
            if s.mime_type:
                bits.append(s.mime_type)
            if s.caption:
                bits.append(s.caption)
            lines.append(f"  - {'; '.join(bits)}")
    if evidence.dom_snapshot_ref:
        lines.append(f"- **dom_snapshot_ref:** {evidence.dom_snapshot_ref}")
    if evidence.extensions:
        lines.append("- **extensions:**")
        lines.extend(_format_extensions_for_prompt(evidence.extensions))
    if evidence.notes:
        lines.append(f"- **notes:** {evidence.notes}")
    return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class BrowserEvidenceReportRow:
    """One row for the benchmark Markdown report (browser_mock cells)."""

    cell_id: str
    evidence_id: str
    title: str | None
    runner: str
    excerpt_count: int
    screenshot_count: int
    has_dom_snapshot_ref: bool
    extension_keys: tuple[str, ...]


def _md_cell_text(s: str) -> str:
    """Avoid breaking Markdown tables."""
    return s.replace("|", "\\|").replace("\n", " ")


def render_benchmark_browser_evidence_markdown(rows: Sequence[BrowserEvidenceReportRow]) -> str:
    """Append to reports/report.md after the main report body when browser cells ran."""
    if not rows:
        return ""
    lines = [
        "",
        "## Browser evidence (fixture summary)",
        "",
        "Per-cell structured traces written during **browser_mock** execution "
        "(see `cells/.../browser_evidence.json`).",
        "",
        "| Cell | Evidence | Runner | Excerpts | Screens | DOM snapshot ref | Extension keys |",
        "| --- | --- | --- | ---: | ---: | --- | --- |",
    ]
    for r in rows:
        ev = f"`{r.evidence_id}`"
        if r.title:
            ev = f"{ev} ({_md_cell_text(r.title)})"
        snap = "yes" if r.has_dom_snapshot_ref else "—"
        ext_keys = ", ".join(r.extension_keys) if r.extension_keys else "—"
        lines.append(
            f"| `{r.cell_id}` | {ev} | `{r.runner}` | {r.excerpt_count} | {r.screenshot_count} | "
            f"{snap} | {ext_keys} |"
        )
    lines.append("")
    return "\n".join(lines)


def browser_evidence_report_row_from_evidence(
    *,
    cell_id: str,
    runner: str,
    evidence: BrowserEvidence,
) -> BrowserEvidenceReportRow:
    """Build a report row from captured evidence."""
    ext = evidence.extensions or {}
    keys = tuple(sorted(ext.keys()))
    return BrowserEvidenceReportRow(
        cell_id=cell_id,
        evidence_id=evidence.id,
        title=evidence.title,
        runner=runner,
        excerpt_count=len(evidence.dom_excerpts),
        screenshot_count=len(evidence.screenshots),
        has_dom_snapshot_ref=bool(evidence.dom_snapshot_ref),
        extension_keys=keys,
    )
