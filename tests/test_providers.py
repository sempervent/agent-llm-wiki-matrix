"""Provider adapters and configuration (deterministic; no live network)."""

from __future__ import annotations

from pathlib import Path

import httpx

from agent_llm_wiki_matrix.providers.base import CompletionRequest
from agent_llm_wiki_matrix.providers.config import (
    OllamaSection,
    OpenAICompatibleSection,
    ProviderConfig,
    load_provider_config,
)
from agent_llm_wiki_matrix.providers.factory import create_provider
from agent_llm_wiki_matrix.providers.mock import MockProvider
from agent_llm_wiki_matrix.providers.ollama import OllamaProvider
from agent_llm_wiki_matrix.providers.openai_compatible import OpenAICompatibleProvider


def test_mock_provider_is_deterministic() -> None:
    p = MockProvider()
    req = CompletionRequest(prompt="hello")
    a = p.complete(req)
    b = p.complete(req)
    assert a == b
    assert "[mock:mock-model]" in a


def test_load_provider_config_env_overrides() -> None:
    cfg = load_provider_config(
        yaml_path=None,
        environ={
            "ALWM_PROVIDER": "ollama",
            "OLLAMA_HOST": "http://example:11434",
            "OLLAMA_MODEL": "mistral",
        },
    )
    assert cfg.kind == "ollama"
    assert cfg.ollama.host == "http://example:11434"
    assert cfg.ollama.model == "mistral"


def test_load_provider_config_from_yaml(tmp_path: Path) -> None:
    path = tmp_path / "p.yaml"
    path.write_text(
        """
kind: openai_compatible
openai_compatible:
  base_url: http://localhost:9000/v1
  model: test-model
""",
        encoding="utf-8",
    )
    cfg = load_provider_config(yaml_path=path, environ={})
    assert cfg.kind == "openai_compatible"
    assert cfg.openai_compatible.base_url == "http://localhost:9000/v1"
    assert cfg.openai_compatible.model == "test-model"


def test_create_provider_factory() -> None:
    cfg = ProviderConfig(kind="mock")
    p = create_provider(cfg)
    assert isinstance(p, MockProvider)


def test_ollama_provider_mocked_transport() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/api/chat" in str(request.url)
        return httpx.Response(200, json={"message": {"content": "pong"}})

    transport = httpx.MockTransport(handler)
    section = OllamaSection(host="http://ollama.test")
    provider = OllamaProvider(section, transport=transport)
    out = provider.complete(CompletionRequest(prompt="ping", model="m"))
    assert out == "pong"


def test_openai_compatible_mocked_transport() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/chat/completions" in str(request.url)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "pong"}}]},
        )

    transport = httpx.MockTransport(handler)
    section = OpenAICompatibleSection(base_url="http://llama.test/v1")
    provider = OpenAICompatibleProvider(section, transport=transport)
    out = provider.complete(CompletionRequest(prompt="ping"))
    assert out == "pong"
