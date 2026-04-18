"""Serialize browser evidence for prompts and markdown reports."""

from __future__ import annotations

import json

from agent_llm_wiki_matrix.browser.models import BrowserEvidence


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
            lines.append(f"  - **{label}**{sel}")
            if ex.visible_text:
                lines.append(f"    - visible: {ex.visible_text}")
            if ex.html_snippet:
                lines.append(f"    - html: {ex.html_snippet}")
    if evidence.screenshots:
        lines.append("- **screenshots:**")
        for s in evidence.screenshots:
            bits: list[str] = []
            if s.relpath:
                bits.append(f"path `{s.relpath}`")
            if s.content_sha256:
                bits.append(f"sha256 `{s.content_sha256}`")
            if s.viewport_width and s.viewport_height:
                bits.append(f"{s.viewport_width}×{s.viewport_height}")
            if s.mime_type:
                bits.append(s.mime_type)
            if s.caption:
                bits.append(s.caption)
            lines.append(f"  - {'; '.join(bits)}")
    if evidence.dom_snapshot_ref:
        lines.append(f"- **dom_snapshot_ref:** {evidence.dom_snapshot_ref}")
    if evidence.extensions:
        lines.append("- **extensions (JSON):**")
        lines.append(json.dumps(evidence.extensions, sort_keys=True, ensure_ascii=False))
    if evidence.notes:
        lines.append(f"- **notes:** {evidence.notes}")
    return "\n".join(lines) + "\n"
