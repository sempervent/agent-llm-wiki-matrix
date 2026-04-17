"""Provider execution helpers: same prompts across backends with execution-mode tagging."""

from __future__ import annotations

import time
from typing import Literal

from agent_llm_wiki_matrix.providers.base import BaseProvider, CompletionRequest

ExecutionMode = Literal["cli", "browser_mock", "repo_governed"]


def run_prompt_with_execution_mode(
    provider: BaseProvider,
    request: CompletionRequest,
    execution_mode: ExecutionMode,
) -> tuple[str, int]:
    """Run ``provider.complete`` and tag output by ``execution_mode`` (deterministic wrappers)."""
    t0 = time.monotonic()
    raw = provider.complete(request)
    if execution_mode == "cli":
        text = raw
    elif execution_mode == "browser_mock":
        text = f"[browser_mock]{raw}"
    elif execution_mode == "repo_governed":
        text = f"[repo_governed]{raw}"
    else:
        msg = f"Unknown execution_mode: {execution_mode}"
        raise ValueError(msg)
    duration_ms = int((time.monotonic() - t0) * 1000)
    return text, duration_ms
