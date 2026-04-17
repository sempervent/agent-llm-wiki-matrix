"""Versioned benchmark definitions (YAML / JSON on disk)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


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
    """One prompt slot: either inline ``text`` or a ``prompt_ref`` into the registry."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    text: str | None = Field(
        default=None,
        description="Inline prompt body (mutually exclusive with prompt_ref).",
    )
    prompt_ref: str | None = Field(
        default=None,
        description="Registry prompt id (see prompts/registry.yaml or prompt_registry_ref).",
    )
    registry_version: str | None = Field(
        default=None,
        description=(
            "Optional pin: must equal the registry file's top-level version when set "
            "(only valid with prompt_ref)."
        ),
    )

    @model_validator(mode="after")
    def _inline_xor_registry(self) -> Self:
        has_text = self.text is not None
        has_ref = self.prompt_ref is not None
        if has_text == has_ref:
            msg = f"Prompt {self.id!r}: set exactly one of text or prompt_ref"
            raise ValueError(msg)
        if self.registry_version is not None and not has_ref:
            msg = f"Prompt {self.id!r}: registry_version requires prompt_ref"
            raise ValueError(msg)
        if has_text and self.text is not None and not self.text.strip():
            msg = f"Prompt {self.id!r}: inline text must be non-empty"
            raise ValueError(msg)
        if has_ref and (not self.prompt_ref or not str(self.prompt_ref).strip()):
            msg = f"Prompt {self.id!r}: prompt_ref must be a non-empty string"
            raise ValueError(msg)
        return self


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
    prompt_registry_ref: str | None = Field(
        default=None,
        description=(
            "Optional path to prompt registry YAML relative to repo root. "
            "Defaults to prompts/registry.yaml when any prompt uses prompt_ref."
        ),
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
