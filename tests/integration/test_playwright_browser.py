"""Opt-in Playwright smoke tests (offline ``file://`` fixtures; no network)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from agent_llm_wiki_matrix.browser import PlaywrightBrowserRunner
from agent_llm_wiki_matrix.browser.factory import create_browser_runner
from agent_llm_wiki_matrix.browser.models import BrowserRunRequest

pytestmark = [pytest.mark.integration, pytest.mark.live_playwright]

_REPO = Path(__file__).resolve().parents[2]
_HTML = Path(__file__).resolve().parent / "fixtures" / "playwright_smoke.html"


@pytest.fixture(scope="module")
def playwright_ready() -> None:
    if os.environ.get("ALWM_PLAYWRIGHT_SMOKE") != "1":
        pytest.skip("Set ALWM_PLAYWRIGHT_SMOKE=1 to run Playwright smoke tests")
    pytest.importorskip("playwright.sync_api")


def test_playwright_runner_offline_html(playwright_ready: None) -> None:
    runner = PlaywrightBrowserRunner()
    result = runner.run(
        BrowserRunRequest(scenario_id="integration.smoke", start_url=_HTML.as_uri())
    )
    assert result.runner == "playwright"
    assert len(result.evidence.navigation_sequence) >= 1
    assert result.evidence.navigation_sequence[0].title == "Playwright smoke"
    texts = " ".join(m.text for m in result.evidence.console_messages)
    assert "smoke-ok" in texts


def test_create_browser_runner_playwright(playwright_ready: None) -> None:
    runner = create_browser_runner("playwright", repo_root=_REPO)
    assert runner.name == "playwright"
