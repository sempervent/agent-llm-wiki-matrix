"""Load provider configuration from environment variables and optional YAML."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

ProviderKind = str  # validated via Literal in ProviderConfig


class OllamaSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    host: str = Field(default="http://127.0.0.1:11434", description="Ollama server base URL")
    model: str = Field(default="llama3.2")


class OpenAICompatibleSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_url: str = Field(default="http://127.0.0.1:8080/v1")
    api_key: str = Field(default="")
    model: str = Field(default="gpt-oss")


class ProviderConfig(BaseModel):
    """Resolved provider configuration (YAML + env overrides)."""

    model_config = ConfigDict(extra="forbid")

    kind: str = Field(default="mock")
    ollama: OllamaSection = Field(default_factory=OllamaSection)
    openai_compatible: OpenAICompatibleSection = Field(default_factory=OpenAICompatibleSection)

    @field_validator("kind")
    @classmethod
    def kind_must_be_known(cls, v: str) -> str:
        allowed = {"mock", "ollama", "openai_compatible"}
        if v not in allowed:
            msg = f"provider kind must be one of {sorted(allowed)}"
            raise ValueError(msg)
        return v


def _read_yaml(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if data is None:
        return {}
    if not isinstance(data, dict):
        msg = "Provider YAML root must be a mapping"
        raise TypeError(msg)
    return data


def load_provider_config(
    *,
    yaml_path: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> ProviderConfig:
    """Load config from optional YAML file, then apply environment overrides."""
    env: Mapping[str, str] = os.environ if environ is None else environ
    base: dict[str, Any] = {}
    if yaml_path is not None and yaml_path.is_file():
        base = _read_yaml(yaml_path)

    data = ProviderConfig.model_validate(base).model_dump()

    if v := env.get("ALWM_PROVIDER"):
        data["kind"] = v

    ollama = data["ollama"]
    if v := env.get("OLLAMA_HOST"):
        ollama["host"] = v
    if v := env.get("OLLAMA_MODEL"):
        ollama["model"] = v

    oaic = data["openai_compatible"]
    if v := env.get("OPENAI_BASE_URL"):
        oaic["base_url"] = v
    if v := env.get("OPENAI_API_KEY"):
        oaic["api_key"] = v
    if v := env.get("OPENAI_MODEL"):
        oaic["model"] = v

    data["ollama"] = ollama
    data["openai_compatible"] = oaic

    return ProviderConfig.model_validate(data)
