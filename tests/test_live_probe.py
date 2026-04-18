"""Unit tests for HTTP probes (no live servers)."""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest

from agent_llm_wiki_matrix.benchmark.live_probe import (
    ollama_model_available,
    probe_ollama_api,
    probe_openai_compatible_api,
)


def test_probe_ollama_api_false_on_network_error(monkeypatch: pytest.MonkeyPatch) -> None:
    req = httpx.Request("GET", "http://127.0.0.1:11434/api/tags")

    def boom(_url: str, **_kwargs: object) -> None:
        raise httpx.ConnectError("no server", request=req)

    monkeypatch.setattr("agent_llm_wiki_matrix.benchmark.live_probe.httpx.get", boom)
    assert probe_ollama_api("http://127.0.0.1:11434") is False


def test_probe_ollama_api_true(monkeypatch: pytest.MonkeyPatch) -> None:
    resp = MagicMock()
    resp.status_code = 200

    def fake_get(_url: str, **_kwargs: object) -> MagicMock:
        return resp

    monkeypatch.setattr("agent_llm_wiki_matrix.benchmark.live_probe.httpx.get", fake_get)
    assert probe_ollama_api("http://127.0.0.1:11434") is True


def test_ollama_model_available_finds_tagged_name(monkeypatch: pytest.MonkeyPatch) -> None:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"models": [{"name": "gpt-oss:20b"}]}

    def fake_get(_url: str, **_kwargs: object) -> MagicMock:
        return resp

    monkeypatch.setattr("agent_llm_wiki_matrix.benchmark.live_probe.httpx.get", fake_get)
    assert ollama_model_available("http://h", "gpt-oss:20b") is True


def test_probe_openai_compatible_true_on_404(monkeypatch: pytest.MonkeyPatch) -> None:
    resp = MagicMock()
    resp.status_code = 404

    def fake_get(_url: str, **_kwargs: object) -> MagicMock:
        return resp

    monkeypatch.setattr("agent_llm_wiki_matrix.benchmark.live_probe.httpx.get", fake_get)
    assert probe_openai_compatible_api("http://127.0.0.1:8080/v1") is True


def test_probe_openai_compatible_false_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    req = httpx.Request("GET", "http://127.0.0.1:8080/v1/models")

    def boom(_url: str, **_kwargs: object) -> None:
        raise httpx.ConnectError("no server", request=req)

    monkeypatch.setattr("agent_llm_wiki_matrix.benchmark.live_probe.httpx.get", boom)
    assert probe_openai_compatible_api("http://127.0.0.1:8080/v1") is False
