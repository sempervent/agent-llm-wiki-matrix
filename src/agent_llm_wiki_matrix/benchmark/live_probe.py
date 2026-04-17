"""HTTP probes for live Ollama and OpenAI-compatible (e.g. llama.cpp) endpoints."""

from __future__ import annotations

from typing import Any

import httpx


def probe_ollama_api(host: str, *, timeout_s: float = 3.0) -> bool:
    """Return True if Ollama responds to ``GET /api/tags``."""
    url = host.rstrip("/") + "/api/tags"
    try:
        response = httpx.get(url, timeout=timeout_s)
    except httpx.RequestError:
        return False
    return response.status_code == 200


def ollama_model_available(
    host: str,
    model: str,
    *,
    timeout_s: float = 3.0,
) -> bool:
    """Return True if Ollama is up and lists a model matching ``model`` (name or name:tag)."""
    url = host.rstrip("/") + "/api/tags"
    try:
        response = httpx.get(url, timeout=timeout_s)
    except httpx.RequestError:
        return False
    if response.status_code != 200:
        return False
    try:
        data: dict[str, Any] = response.json()
    except ValueError:
        return False
    models = data.get("models") or []
    if not isinstance(models, list):
        return False
    want = model.strip()
    for entry in models:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        if not isinstance(name, str):
            continue
        if name == want or name.startswith(want + ":"):
            return True
    return False


def probe_openai_compatible_api(base_url: str, *, timeout_s: float = 3.0) -> bool:
    """Return True if something responds at ``GET <base>/models`` (HTTP layer only).

    Some llama.cpp builds return 404 for ``/v1/models`` while chat still works; any
    non-error HTTP response counts as reachable for smoke checks.
    """
    root = base_url.rstrip("/")
    url = f"{root}/models"
    try:
        response = httpx.get(url, timeout=timeout_s)
    except httpx.RequestError:
        return False
    return response.status_code < 500
