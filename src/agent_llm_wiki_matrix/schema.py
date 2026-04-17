"""JSON Schema loading and validation helpers."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator

from agent_llm_wiki_matrix.logging_config import get_logger

log = get_logger("schema")


def repo_root_from_env() -> Path:
    """Resolve repository root for schema paths (override with ALWM_REPO_ROOT)."""
    return Path(os.environ.get("ALWM_REPO_ROOT", ".")).resolve()


@lru_cache(maxsize=64)
def _load_schema_at(resolved_path: str) -> dict[str, Any]:
    full = Path(resolved_path)
    if not full.is_file():
        log.error("schema_missing", path=str(full))
        raise FileNotFoundError(f"Schema not found: {full}")
    text = full.read_text(encoding="utf-8")
    return cast(dict[str, Any], json.loads(text))


def load_schema(schema_path: str) -> dict[str, Any]:
    """Load a JSON Schema from a path relative to the repository root."""
    full = (repo_root_from_env() / schema_path).resolve()
    return _load_schema_at(str(full))


def validate_json(instance: dict[str, Any], schema: dict[str, Any]) -> None:
    """Validate a JSON-like object against a schema; raise on failure."""
    Draft202012Validator(schema).validate(instance)


def validate_file(instance_path: Path, schema_path: str) -> None:
    """Validate a JSON file against a schema loaded by relative path."""
    schema = load_schema(schema_path)
    raw = instance_path.read_text(encoding="utf-8")
    instance = json.loads(raw)
    if not isinstance(instance, dict):
        raise TypeError("Top-level JSON must be an object")
    validate_json(instance, schema)
