"""Deterministic mock provider for tests and offline pipelines."""

from __future__ import annotations

import hashlib

from agent_llm_wiki_matrix.providers.base import BaseProvider, CompletionRequest


class MockProvider(BaseProvider):
    """Returns stable output derived from prompt bytes (no network)."""

    @property
    def name(self) -> str:
        return "mock"

    def complete(self, request: CompletionRequest) -> str:
        digest = hashlib.sha256(request.prompt.encode("utf-8")).hexdigest()[:16]
        model = request.model or "mock-model"
        return f"[mock:{model}] {digest}"
