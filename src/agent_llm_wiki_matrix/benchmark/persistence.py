"""Reproducible on-disk layout for benchmark runs (UTF-8, stable names)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent_llm_wiki_matrix.models import BenchmarkRunManifest
from agent_llm_wiki_matrix.schema import load_schema, validate_json


def utf8_text_blob(text: str) -> str:
    """Normalize text for deterministic bytes on disk (single trailing newline)."""
    return text.rstrip() + "\n"


def write_utf8_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(utf8_text_blob(content), encoding="utf-8", newline="\n")


def write_json_sorted(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_pydantic_json(path: Path, model: Any) -> None:
    """Write a Pydantic model with sorted keys for diff-stable output."""
    write_json_sorted(path, model.model_dump(exclude_none=True))


def write_benchmark_manifest(path: Path, manifest: BenchmarkRunManifest) -> None:
    """Serialize manifest.json with JSON Schema validation then diff-stable JSON."""
    data = manifest.model_dump(mode="json", exclude_none=True)
    validate_json(data, load_schema("schemas/v1/manifest.schema.json"))
    write_json_sorted(path, data)
