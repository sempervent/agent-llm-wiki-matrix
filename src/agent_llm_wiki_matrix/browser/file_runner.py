"""Load browser evidence from committed JSON fixtures (deterministic)."""

from __future__ import annotations

import time
from pathlib import Path

from agent_llm_wiki_matrix.browser.base import BrowserRunner
from agent_llm_wiki_matrix.browser.load import load_browser_evidence
from agent_llm_wiki_matrix.browser.models import BrowserRunRequest, BrowserRunResult


class FileBrowserRunner(BrowserRunner):
    """Resolve evidence from `fixture_relpath` or `scenario_id` under a base directory."""

    def __init__(self, repo_root: Path, *, evidence_dir: Path | None = None) -> None:
        self._root = repo_root
        self._evidence_dir = evidence_dir or (repo_root / "fixtures" / "browser_evidence" / "v1")

    @property
    def name(self) -> str:
        return "file"

    def run(self, request: BrowserRunRequest) -> BrowserRunResult:
        t0 = time.monotonic()
        if request.fixture_relpath:
            path = (self._root / request.fixture_relpath).resolve()
        elif request.scenario_id:
            path = (self._evidence_dir / f"{request.scenario_id}.json").resolve()
        else:
            msg = "FileBrowserRunner requires fixture_relpath or scenario_id"
            raise ValueError(msg)
        if not path.is_file():
            msg = f"Browser evidence fixture not found: {path}"
            raise FileNotFoundError(msg)
        evidence = load_browser_evidence(path)
        duration_ms = int((time.monotonic() - t0) * 1000)
        return BrowserRunResult(evidence=evidence, runner=self.name, duration_ms=duration_ms)
