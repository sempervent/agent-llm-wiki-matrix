"""Construct providers from configuration."""

from __future__ import annotations

from agent_llm_wiki_matrix.providers.base import BaseProvider
from agent_llm_wiki_matrix.providers.config import ProviderConfig
from agent_llm_wiki_matrix.providers.mock import MockProvider
from agent_llm_wiki_matrix.providers.ollama import OllamaProvider
from agent_llm_wiki_matrix.providers.openai_compatible import OpenAICompatibleProvider


def create_provider(config: ProviderConfig) -> BaseProvider:
    """Instantiate the configured provider backend."""
    if config.kind == "mock":
        return MockProvider()
    if config.kind == "ollama":
        return OllamaProvider(config.ollama)
    if config.kind == "openai_compatible":
        return OpenAICompatibleProvider(config.openai_compatible)
    msg = f"Unsupported provider kind: {config.kind}"
    raise ValueError(msg)
