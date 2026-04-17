"""Merge provider YAML/env with per-variant benchmark backend overrides."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from agent_llm_wiki_matrix.providers.config import ProviderConfig, load_provider_config


def apply_backend_override(cfg: ProviderConfig, *, kind: str, model: str) -> ProviderConfig:
    """Set provider kind and model for the active backend section."""
    data = cfg.model_dump()
    data["kind"] = kind
    if kind == "ollama":
        data["ollama"]["model"] = model
    elif kind == "openai_compatible":
        data["openai_compatible"]["model"] = model
    elif kind == "mock":
        pass
    else:
        msg = f"Unsupported backend kind: {kind}"
        raise ValueError(msg)
    return ProviderConfig.model_validate(data)


def load_provider_config_for_benchmark_variant(
    *,
    yaml_path: Path | None,
    environ: Mapping[str, str],
    backend_kind: str,
    backend_model: str,
    fixture_mode_force_mock: bool = True,
) -> ProviderConfig:
    """Load config, apply variant backend; optionally force mock if fixture mode is on."""
    cfg = load_provider_config(yaml_path=yaml_path, environ=environ)
    kind = backend_kind
    model = backend_model
    if environ.get("ALWM_FIXTURE_MODE") == "1" and fixture_mode_force_mock:
        kind = "mock"
        model = backend_model or "mock-model"
    return apply_backend_override(cfg, kind=kind, model=model)


def load_judge_provider_config(
    *,
    yaml_path: Path | None,
    environ: Mapping[str, str],
    judge_live: bool,
) -> ProviderConfig:
    """Provider for semantic judge: in fixture mode, force mock unless ``judge_live`` (opt-in)."""
    cfg = load_provider_config(yaml_path=yaml_path, environ=environ)
    if environ.get("ALWM_FIXTURE_MODE") == "1" and not judge_live:
        return apply_backend_override(cfg, kind="mock", model="mock-model")
    return cfg
