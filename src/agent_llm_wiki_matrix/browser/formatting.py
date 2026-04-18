"""Serialize browser evidence for prompts and markdown reports."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from agent_llm_wiki_matrix.browser.models import BrowserEvidence, DomExcerpt, ScreenshotMetadata

_PROMPT_HTML_SNIPPET_MAX = 720
_MARKDOWN_HTML_FENCE_MAX = 1600


def _truncate_html_snippet(s: str, *, max_len: int = _PROMPT_HTML_SNIPPET_MAX) -> str:
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "…"


def _sha_short(digest: str | None, *, n: int = 10) -> str:
    if not digest:
        return "—"
    return digest[:n] + ("…" if len(digest) > n else "")


def extension_digest_short(ext: dict[str, Any] | None) -> str:
    """Single-line digest for report tables (deterministic fixtures + MCP honesty)."""
    if not ext:
        return "—"
    parts: list[str] = []
    fp = ext.get("fixture_profile")
    if isinstance(fp, str) and fp:
        parts.append(fp)
    net = ext.get("network")
    if isinstance(net, dict):
        rt = net.get("requests_total")
        fr = net.get("failed_requests")
        if rt is not None:
            tail = f"{fr} fail" if fr else "ok"
            parts.append(f"net {rt} req/{tail}")
    a11y = ext.get("accessibility")
    if isinstance(a11y, dict) and "violations_count" in a11y:
        parts.append(f"a11y {a11y['violations_count']}v")
    perf = ext.get("performance")
    if isinstance(perf, dict):
        lcp = perf.get("largest_contentful_paint_ms")
        if lcp is not None:
            parts.append(f"LCP {lcp:g}ms")
    td = ext.get("trace_digest")
    if isinstance(td, str) and td:
        parts.append(f"trace {_sha_short(td, n=12)}")
    if ext.get("runner") == "mcp_stdio":
        parts.append("MCP stdio (local)")
    if parts:
        return " · ".join(parts)
    keys = sorted(k for k in ext if k != "structured_capture_version")
    return ", ".join(keys[:5]) + ("…" if len(keys) > 5 else "")


def format_extensions_compact_markdown(ext: dict[str, Any] | None) -> str:
    """Compact table for report bodies (replaces long nested bullets where possible)."""
    if not ext:
        return "_None._"
    lines = [
        "| Extension block | Summary |",
        "| --- | --- |",
    ]
    known = (
        "fixture_profile",
        "structured_capture_version",
        "runner",
        "trace_digest",
        "network",
        "accessibility",
        "performance",
    )
    consumed: set[str] = set()
    for key in known:
        if key not in ext:
            continue
        consumed.add(key)
        val = ext[key]
        if key == "structured_capture_version":
            lines.append(f"| `{key}` | {val!r} |")
            continue
        if key == "trace_digest" and isinstance(val, str):
            lines.append(f"| `{key}` | `{_sha_short(val, n=16)}` |")
            continue
        if key == "runner":
            lines.append(f"| `{key}` | {_describe_runner_cell(str(val))} |")
            continue
        if key == "network" and isinstance(val, dict):
            rt = val.get("requests_total", "—")
            fr = val.get("failed_requests", "—")
            lu = val.get("last_url", "—")
            st = val.get("last_status_code", "—")
            summ = f"req {rt}, fail {fr}, last `{lu}` → {st}"
            lines.append(f"| **network** | {summ} |")
            continue
        if key in ("accessibility", "performance") and isinstance(val, dict):
            pairs = ", ".join(f"{k_}={v_!r}" for k_, v_ in sorted(val.items())[:8])
            if len(val) > 8:
                pairs += ", …"
            lines.append(f"| **{key}** | {pairs} |")
            continue
        lines.append(f"| `{key}` | {val!r} |")

    remainder = {k: v for k, v in ext.items() if k not in consumed}
    if remainder:
        lines.append("| **other** | see JSON block below |")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(remainder, sort_keys=True, ensure_ascii=False, indent=2))
        lines.append("```")
    return "\n".join(lines)


def _describe_runner_cell(runner: str) -> str:
    r = runner.lower()
    if r in ("file", "mock", "browser_mock"):
        return f"`{runner}` (deterministic fixture)"
    if "playwright" in r:
        return f"`{runner}` (optional live capture)"
    if "mcp" in r:
        return f"`{runner}` — local stdio JSON bridge (not remote/IDE-hosted)"
    return f"`{runner}`"


def signals_digest_line(evidence: BrowserEvidence) -> str:
    """Counts for summary tables: navigation, console, DOM excerpts, screenshots."""
    n_nav = len(evidence.navigation_sequence)
    n_con = len(evidence.console_messages)
    n_dom = len(evidence.dom_excerpts)
    n_shot = len(evidence.screenshots)
    bits = [
        f"nav×{n_nav}",
        f"console×{n_con}",
        f"dom×{n_dom}",
        f"shot×{n_shot}",
    ]
    if evidence.dom_snapshot_ref:
        bits.append("snap")
    return " · ".join(bits)


def screenshot_primary_viewport_summary(evidence: BrowserEvidence) -> str:
    """First screenshot viewport / scope for compact comparison tables (deterministic metadata)."""
    if not evidence.screenshots:
        return "—"
    s = evidence.screenshots[0]
    w, h = s.viewport_width, s.viewport_height
    scope = s.capture_scope or "?"
    if w is not None and h is not None:
        return f"{w}×{h} ({scope})"
    return str(scope)


def format_extensions_markdown(ext: dict[str, Any] | None) -> list[str]:
    """Readable Markdown bullets for ``extensions`` (structured sub-blocks + JSON remainder)."""
    if not ext:
        return ["_None._"]
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
        lines.append(f"- **{key}**")
        if (key == "network" or key in ("accessibility", "performance")) and isinstance(val, dict):
            for nk, nv in sorted(val.items()):
                lines.append(f"  - `{nk}`: {nv!r}")
        else:
            lines.append(f"  - {val!r}")

    remainder = {k: v for k, v in ext.items() if k not in consumed}
    if remainder:
        lines.append("- **other**")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(remainder, sort_keys=True, ensure_ascii=False, indent=2))
        lines.append("```")
    return lines


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
    signals_digest: str = ""
    extension_digest: str = ""


def _md_cell_text(s: str) -> str:
    """Avoid breaking Markdown tables."""
    return s.replace("|", "\\|").replace("\n", " ")


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
        signals_digest=signals_digest_line(evidence),
        extension_digest=extension_digest_short(evidence.extensions),
    )


def render_dom_excerpts_markdown(excerpts: Sequence[DomExcerpt]) -> str:
    """Table + optional fenced HTML for auditors."""
    if not excerpts:
        return "_No DOM excerpts._"
    lines = [
        "| # | Label | Selector | Role | a11y name | Order | Visible text |",
        "| ---: | --- | --- | --- | --- | ---: | --- |",
    ]
    for i, ex in enumerate(excerpts, start=1):
        lines.append(
            f"| {i} | {ex.label or '—'} | `{ex.selector or '—'}` | "
            f"`{ex.aria_role or '—'}` | {ex.accessibility_name or '—'} | "
            f"{ex.dom_order if ex.dom_order is not None else '—'} | "
            f"{_md_cell_text(ex.visible_text or '—')} |",
        )
    if not any(ex.html_snippet for ex in excerpts):
        return "\n".join(lines)
    blocks: list[str] = ["", "**HTML snippets** (truncated for Markdown)", ""]
    for ex in excerpts:
        if not ex.html_snippet:
            continue
        label = ex.label or "excerpt"
        shown = ex.html_snippet
        trunc = False
        if len(shown) > _MARKDOWN_HTML_FENCE_MAX:
            shown = shown[: _MARKDOWN_HTML_FENCE_MAX - 1] + "…"
            trunc = True
        blocks.append(f"_{label}_ (`{ex.selector or '?'}`)")
        blocks.append("")
        blocks.append("```html")
        blocks.append(shown)
        blocks.append("```")
        if trunc:
            blocks.append("_… truncated._")
        blocks.append("")
    return "\n".join(lines) + "\n" + "\n".join(blocks).rstrip()


def render_screenshots_markdown(screenshots: Sequence[ScreenshotMetadata]) -> str:
    """Screenshot metadata as a readable table (no binary; SHA for integrity)."""
    if not screenshots:
        return "_No screenshot metadata._"
    lines = [
        "| Seq | Scope | Target | Viewport | DPR | SHA-256 (short) | MIME | Caption |",
        "| ---: | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for s in screenshots:
        vp = "—"
        if s.viewport_width and s.viewport_height:
            vp = f"{s.viewport_width}×{s.viewport_height}"
        dpr = f"{s.device_pixel_ratio:g}" if s.device_pixel_ratio is not None else "—"
        sha = _sha_short(s.content_sha256, n=12) if s.content_sha256 else "—"
        tgt = f"`{s.target_selector}`" if s.target_selector else "—"
        sc = s.capture_scope or "—"
        cap = _md_cell_text(s.caption) if s.caption else "—"
        seq = str(s.sequence) if s.sequence is not None else "—"
        mime = s.mime_type or "—"
        lines.append(
            f"| {seq} | `{sc}` | {tgt} | {vp} | {dpr} | `{sha}` | {mime} | {cap} |",
        )
    return "\n".join(lines)


def render_browser_evidence_detail_markdown(
    *,
    heading_label: str,
    suite_ref: str | None,
    runner: str,
    evidence: BrowserEvidence,
) -> str:
    """One cell/run block: navigation, console, excerpts, screenshots, extensions."""
    meta: list[str] = [f"#### {heading_label}", ""]
    if suite_ref:
        meta.append(f"- **suite:** `{suite_ref}`")
    meta.append(f"- **runner:** {_describe_runner_cell(runner)}")
    _ev = f"- **evidence:** `{evidence.id}`"
    if evidence.title:
        _ev += f" — {evidence.title}"
    meta.append(_ev)
    meta.append(f"- **signals:** {signals_digest_line(evidence)}")
    meta.append(f"- **extensions (digest):** {extension_digest_short(evidence.extensions)}")
    if evidence.dom_snapshot_ref:
        meta.append(f"- **dom_snapshot_ref:** `{evidence.dom_snapshot_ref}`")
    meta.append("")
    meta.append("**Navigation**")
    meta.append("")
    for step in evidence.navigation_sequence:
        bit = [f"`{step.url}`"]
        if step.title:
            bit.append(f"“{step.title}”")
        if step.action:
            bit.append(f"[{step.action}]")
        meta.append(f"- {' '.join(bit)}")
    meta.append("")
    if evidence.console_messages:
        meta.append("**Console**")
        meta.append("")
        for m in evidence.console_messages:
            meta.append(f"- `[{m.level}]` {_md_cell_text(m.text)}")
        meta.append("")
    meta.append("**DOM excerpts**")
    meta.append("")
    meta.append(render_dom_excerpts_markdown(evidence.dom_excerpts))
    meta.append("")
    meta.append("**Screenshots**")
    meta.append("")
    meta.append(render_screenshots_markdown(evidence.screenshots))
    meta.append("")
    meta.append("**Extensions (structured)**")
    meta.append("")
    meta.append(format_extensions_compact_markdown(evidence.extensions))
    if evidence.notes:
        meta.append("")
        meta.append(f"_Notes:_ {_md_cell_text(evidence.notes)}")
    return "\n".join(meta)


def render_benchmark_browser_evidence_markdown(
    sections: Sequence[tuple[BrowserEvidenceReportRow, BrowserEvidence]],
) -> str:
    """Summary table plus legible per-cell sections for ``reports/report.md``."""
    if not sections:
        return ""
    rows_only = [t[0] for t in sections]
    lines = [
        "",
        "## Browser evidence (fixture summary)",
        "",
        "Per-cell **browser_mock** traces (`cells/.../browser_evidence.json`). "
        "**Playwright** is optional (live capture). **MCP** stdio is a **local** JSON bridge "
        "to a subprocess — not IDE-hosted or remote automation (`docs/architecture/browser.md`).",
        "",
        "| Cell | Evidence | Runner | Signals | DOM snap | Extension digest |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows_only:
        ev = f"`{r.evidence_id}`"
        if r.title:
            ev = f"{ev} ({_md_cell_text(r.title)})"
        snap = "yes" if r.has_dom_snapshot_ref else "—"
        sig = r.signals_digest
        dig = r.extension_digest
        lines.append(
            f"| `{r.cell_id}` | {ev} | `{r.runner}` | {_md_cell_text(sig)} | {snap} | "
            f"{_md_cell_text(dig)} |",
        )
    lines.append("")
    lines.append("### Browser traces (DOM, screenshots, extensions)")
    lines.append("")
    for row, evidence in sections:
        lines.append(
            render_browser_evidence_detail_markdown(
                heading_label=f"Cell `{row.cell_id}`",
                suite_ref=None,
                runner=row.runner,
                evidence=evidence,
            ),
        )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_campaign_browser_evidence_table_only(
    rows: Sequence[BrowserEvidenceReportRow],
) -> str:
    """Table-only fragment (used when pairing with external headings)."""
    if not rows:
        return ""
    lines = [
        "| Member cell | Evidence | Runner | Signals | DOM snap | Extension digest |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        ev = f"`{r.evidence_id}`"
        if r.title:
            ev = f"{ev} ({_md_cell_text(r.title)})"
        snap = "yes" if r.has_dom_snapshot_ref else "—"
        lines.append(
            f"| `{r.cell_id}` | {ev} | `{r.runner}` | {_md_cell_text(r.signals_digest)} | {snap} | "
            f"{_md_cell_text(r.extension_digest)} |",
        )
    return "\n".join(lines) + "\n"
