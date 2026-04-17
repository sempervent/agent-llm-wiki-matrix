"""Ollama HTTP API provider (/api/chat)."""

from __future__ import annotations

from typing import Any

import httpx

from agent_llm_wiki_matrix.providers.base import BaseProvider, CompletionRequest
from agent_llm_wiki_matrix.providers.config import OllamaSection


class OllamaProvider(BaseProvider):
    """Talk to a local or remote Ollama instance."""

    def __init__(
        self,
        section: OllamaSection,
        *,
        timeout_s: float = 120.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._section = section
        self._timeout = timeout_s
        self._transport = transport

    @property
    def name(self) -> str:
        return "ollama"

    def complete(self, request: CompletionRequest) -> str:
        model = request.model or self._section.model
        url = self._section.host.rstrip("/") + "/api/chat"
        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": request.prompt}],
            "stream": False,
        }
        if request.temperature is not None:
            payload["options"] = {"temperature": request.temperature}
        with httpx.Client(timeout=self._timeout, transport=self._transport) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
        msg = data.get("message") or {}
        content = msg.get("content")
        if not isinstance(content, str):
            msg = "Unexpected Ollama response shape (missing message.content)"
            raise RuntimeError(msg)
        return content
