"""Abstract provider contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CompletionRequest:
    """Single-turn completion input (expand to multi-turn in later phases)."""

    prompt: str
    model: str | None = None
    temperature: float | None = None


class BaseProvider(ABC):
    """Switchable backend for text generation (Ollama, OpenAI-compatible HTTP, mock)."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Stable provider id (mock, ollama, openai_compatible)."""

    @abstractmethod
    def complete(self, request: CompletionRequest) -> str:
        """Return model text for the given prompt."""
