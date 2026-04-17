"""Load and validate the versioned prompt registry (YAML under ``prompts/``)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from agent_llm_wiki_matrix.schema import load_schema, validate_json


class PromptRegistryEntry(BaseModel):
    """One prompt entry in ``prompts/registry.yaml``."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    description: str = ""
    path: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)


class PromptRegistryDocument(BaseModel):
    """Root object for the prompt registry file."""

    model_config = ConfigDict(extra="forbid")

    version: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)
    prompts: list[PromptRegistryEntry] = Field(min_length=1)


def _registry_dict_from_yaml(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if data is None:
        msg = "Prompt registry YAML is empty"
        raise ValueError(msg)
    if not isinstance(data, dict):
        msg = "Prompt registry YAML root must be a mapping"
        raise TypeError(msg)
    return data


def load_prompt_registry_yaml(path: Path) -> PromptRegistryDocument:
    """Load ``path``, validate against JSON Schema, return a typed document."""
    data = _registry_dict_from_yaml(path)
    schema = load_schema("schemas/v1/prompt_registry.schema.json")
    validate_json(data, schema)
    return PromptRegistryDocument.model_validate(data)


def resolve_prompt_text(*, repo_root: Path, entry: PromptRegistryEntry) -> str:
    """Return UTF-8 text for a registry entry (path relative to repo root)."""
    full = (repo_root / entry.path).resolve()
    try:
        full.relative_to(repo_root.resolve())
    except ValueError as e:
        msg = f"Prompt path escapes repo root: {entry.path}"
        raise ValueError(msg) from e
    if not full.is_file():
        msg = f"Prompt file not found: {full}"
        raise FileNotFoundError(msg)
    return full.read_text(encoding="utf-8")


def find_prompt_entry(doc: PromptRegistryDocument, prompt_id: str) -> PromptRegistryEntry:
    """Return the entry with ``id == prompt_id`` or raise ``KeyError``."""
    for p in doc.prompts:
        if p.id == prompt_id:
            return p
    raise KeyError(prompt_id)
