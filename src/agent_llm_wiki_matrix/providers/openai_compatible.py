"""OpenAI-compatible HTTP API (llama.cpp server, vLLM, etc.)."""

from __future__ import annotations

from typing import Any

import httpx

from agent_llm_wiki_matrix.providers.base import BaseProvider, CompletionRequest
from agent_llm_wiki_matrix.providers.config import OpenAICompatibleSection


class OpenAICompatibleProvider(BaseProvider):
    """POST /v1/chat/completions against an OpenAI-compatible server."""

    def __init__(
        self,
        section: OpenAICompatibleSection,
        *,
        timeout_s: float = 120.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._section = section
        self._timeout = timeout_s
        self._transport = transport

    @property
    def name(self) -> str:
        return "openai_compatible"

    def complete(self, request: CompletionRequest) -> str:
        model = request.model or self._section.model
        base = self._section.base_url.rstrip("/")
        url = f"{base}/chat/completions"
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._section.api_key:
            headers["Authorization"] = f"Bearer {self._section.api_key}"
        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": request.prompt}],
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        with httpx.Client(timeout=self._timeout, transport=self._transport) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        choices = data.get("choices") or []
        if not choices:
            msg = "OpenAI-compatible response missing choices[]"
            raise RuntimeError(msg)
        message = (choices[0] or {}).get("message") or {}
        content = message.get("content")
        if not isinstance(content, str):
            msg = "OpenAI-compatible response missing choices[0].message.content"
            raise RuntimeError(msg)
        return content
