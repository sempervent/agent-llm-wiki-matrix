"""Live browser capture via Playwright (optional dependency)."""

from __future__ import annotations

import hashlib
import time
from typing import Any, Literal
from urllib.parse import urljoin

from agent_llm_wiki_matrix.browser.base import BrowserRunner
from agent_llm_wiki_matrix.browser.models import (
    BrowserEvidence,
    BrowserRunRequest,
    BrowserRunResult,
    ConsoleMessage,
    NavigationStep,
)


def _pw_console_level(pw_type: str) -> Literal["log", "warn", "error", "debug"]:
    if pw_type in ("warning",):
        return "warn"
    if pw_type in ("error",):
        return "error"
    if pw_type in ("debug",):
        return "debug"
    return "log"


def _resolve_next_url(current: str, step: str) -> str:
    s = step.strip()
    if s.startswith(("http://", "https://", "file://")):
        return s
    base = current if current.endswith("/") else current + "/"
    return urljoin(base, s)


class PlaywrightBrowserRunner(BrowserRunner):
    """Drive Chromium/WebKit/Firefox via Playwright and map output to `BrowserEvidence`."""

    def __init__(
        self,
        *,
        browser_type: Literal["chromium", "firefox", "webkit"] = "chromium",
        headless: bool = True,
        timeout_ms: int = 30_000,
    ) -> None:
        self._browser_type = browser_type
        self._headless = headless
        self._timeout_ms = timeout_ms

    @property
    def name(self) -> str:
        return "playwright"

    def run(self, request: BrowserRunRequest) -> BrowserRunResult:
        if not request.start_url:
            msg = "PlaywrightBrowserRunner requires start_url"
            raise ValueError(msg)
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as e:
            msg = (
                "Playwright is not installed. Install optional deps: "
                "pip install 'agent-llm-wiki-matrix[browser]' "
                "and run: playwright install chromium"
            )
            raise RuntimeError(msg) from e

        t0 = time.monotonic()
        label = request.scenario_id or "playwright.default"
        digest = hashlib.sha256(f"{label}\n{request.start_url}".encode()).hexdigest()[:12]

        console_messages: list[ConsoleMessage] = []
        navigation_sequence: list[NavigationStep] = []

        def _on_console(msg: Any) -> None:
            pw_type = str(getattr(msg, "type", "log"))
            text = str(getattr(msg, "text", ""))
            console_messages.append(ConsoleMessage(level=_pw_console_level(pw_type), text=text))

        with sync_playwright() as p:
            launcher = getattr(p, self._browser_type)
            browser = launcher.launch(headless=self._headless)
            try:
                page = browser.new_page()
                page.on("console", _on_console)
                self._visit(page, request.start_url, navigation_sequence, "navigate")
                for step in request.steps:
                    next_url = _resolve_next_url(page.url, step)
                    self._visit(page, next_url, navigation_sequence, "navigate")
            finally:
                browser.close()

        title = f"Playwright capture ({label})"
        if navigation_sequence:
            first_title = navigation_sequence[0].title
            if first_title:
                title = first_title

        evidence = BrowserEvidence(
            id=f"playwright-evidence-{label}-{digest}",
            title=title,
            navigation_sequence=navigation_sequence,
            console_messages=console_messages,
            notes="PlaywrightBrowserRunner: live browser session.",
        )
        duration_ms = int((time.monotonic() - t0) * 1000)
        return BrowserRunResult(evidence=evidence, runner=self.name, duration_ms=duration_ms)

    def _visit(
        self,
        page: Any,
        url: str,
        navigation_sequence: list[NavigationStep],
        action: str,
    ) -> None:
        page.goto(url, wait_until="domcontentloaded", timeout=self._timeout_ms)
        nav_title = page.title() or None
        navigation_sequence.append(
            NavigationStep(url=page.url, title=nav_title, action=action),
        )
