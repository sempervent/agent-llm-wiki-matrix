"""Versioned benchmark definitions (YAML / JSON on disk)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field


class BackendSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["mock", "ollama", "openai_compatible"]
    model: str = "mock-model"


class VariantSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    agent_stack: str = Field(min_length=1)
    execution_mode: Literal["cli", "browser_mock", "repo_governed"]
    backend: BackendSpec


class PromptItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    text: str


class BenchmarkDefinitionV1(BaseModel):
    """Benchmark bundle: prompts × variants (agent stack, backend, execution mode)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    rubric_ref: str = Field(
        min_length=1,
        description="Path relative to repository root",
    )
    prompts: list[PromptItem] = Field(min_length=1)
    variants: list[VariantSpec] = Field(min_length=1)


def load_benchmark_definition(path: Path) -> BenchmarkDefinitionV1:
    """Load a versioned benchmark definition from YAML or JSON."""
    raw_text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        data = yaml.safe_load(raw_text)
    else:
        import json

        data = json.loads(raw_text)
    if not isinstance(data, dict):
        msg = "Benchmark definition root must be an object"
        raise TypeError(msg)
    return BenchmarkDefinitionV1.model_validate(data)
