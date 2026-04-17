"""Serialize browser evidence for prompts and markdown reports."""

from __future__ import annotations

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
    if evidence.dom_snapshot_ref:
        lines.append(f"- **dom_snapshot_ref:** {evidence.dom_snapshot_ref}")
    if evidence.notes:
        lines.append(f"- **notes:** {evidence.notes}")
    return "\n".join(lines) + "\n"
