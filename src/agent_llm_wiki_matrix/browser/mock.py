"""Deterministic mock browser runner (no network, no browser binary)."""

from __future__ import annotations

import hashlib
import time

from agent_llm_wiki_matrix.browser.base import BrowserRunner
from agent_llm_wiki_matrix.browser.models import (
    BrowserEvidence,
    BrowserRunRequest,
    BrowserRunResult,
    ConsoleMessage,
    NavigationStep,
)


class MockBrowserRunner(BrowserRunner):
    """Synthetic evidence derived only from `BrowserRunRequest` fields."""

    @property
    def name(self) -> str:
        return "mock"

    def run(self, request: BrowserRunRequest) -> BrowserRunResult:
        t0 = time.monotonic()
        label = request.scenario_id or "mock.default"
        digest = hashlib.sha256(label.encode("utf-8")).hexdigest()[:12]
        start = request.start_url or "https://example.test/"
        nav = [
            NavigationStep(url=start, title="Start", action="navigate"),
            NavigationStep(
                url=f"{start.rstrip('/')}/step-2",
                title=f"Mock step ({digest})",
                action="navigate",
            ),
        ]
        for i, step_name in enumerate(request.steps):
            nav.append(
                NavigationStep(
                    url=f"{start.rstrip('/')}/step-{i + 3}",
                    title=step_name,
                    action="step",
                )
            )
        evidence = BrowserEvidence(
            id=f"mock-evidence-{label}",
            title=f"Mock browser evidence ({label})",
            navigation_sequence=nav,
            console_messages=[
                ConsoleMessage(level="log", text=f"mock_trace={digest}"),
            ],
            notes="MockBrowserRunner: deterministic; no real browser.",
        )
        duration_ms = int((time.monotonic() - t0) * 1000)
        return BrowserRunResult(evidence=evidence, runner=self.name, duration_ms=duration_ms)
