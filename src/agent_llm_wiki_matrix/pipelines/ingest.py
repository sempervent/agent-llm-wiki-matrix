"""Ingest Markdown wiki pages into validated Thought JSON artifacts."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from agent_llm_wiki_matrix.models import Thought


def _title_from_markdown(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return re.sub(r"^#+\s*", "", stripped).strip() or fallback
    return fallback


def ingest_markdown_pages(
    input_dir: Path,
    output_dir: Path,
    *,
    created_at: str,
    status: Literal["draft", "published"] = "draft",
) -> list[Path]:
    """Read `*.md` from ``input_dir`` and write one ``thought`` JSON per file.

    Returns paths of written files (sorted by path for determinism).
    """
    if not input_dir.is_dir():
        msg = f"Input directory does not exist: {input_dir}"
        raise FileNotFoundError(msg)
    output_dir.mkdir(parents=True, exist_ok=True)
    md_files = sorted(input_dir.glob("*.md"))
    written: list[Path] = []
    for path in md_files:
        body = path.read_text(encoding="utf-8")
        stem = path.stem
        thought_id = f"thought-{stem}"
        title = _title_from_markdown(body, stem.replace("-", " ").title())
        thought = Thought(
            id=thought_id,
            title=title,
            body_markdown=body,
            created_at=created_at,
            status=status,
            tags=["ingested"],
            links=[],
        )
        out_path = output_dir / f"{stem}.thought.json"
        out_path.write_text(
            thought.model_dump_json(indent=2, exclude_none=True) + "\n",
            encoding="utf-8",
        )
        written.append(out_path)
    return written
