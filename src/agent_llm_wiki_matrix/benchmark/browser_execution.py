"""Browser evidence phase for benchmark cells (execution_mode ``browser_mock``)."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from agent_llm_wiki_matrix.benchmark.definitions import BrowserBenchConfig, VariantSpec
from agent_llm_wiki_matrix.browser.factory import create_browser_runner
from agent_llm_wiki_matrix.browser.formatting import evidence_to_prompt_block
from agent_llm_wiki_matrix.browser.models import BrowserRunRequest, BrowserRunResult


def _default_scenario_id(variant_id: str, prompt_id: str) -> str:
    return f"{variant_id}__{prompt_id}"


def build_browser_run_request(
    cfg: BrowserBenchConfig,
    variant_id: str,
    prompt_id: str,
) -> BrowserRunRequest:
    """Map benchmark variant browser config to a ``BrowserRunRequest``."""
    default_sid = _default_scenario_id(variant_id, prompt_id)
    if cfg.runner == "mock":
        return BrowserRunRequest(
            scenario_id=cfg.scenario_id or default_sid,
            start_url=cfg.start_url,
            steps=list(cfg.steps),
        )
    if cfg.runner == "file":
        return BrowserRunRequest(
            scenario_id=cfg.scenario_id,
            fixture_relpath=cfg.fixture_relpath,
            start_url=cfg.start_url,
            steps=list(cfg.steps),
        )
    if cfg.runner == "playwright":
        return BrowserRunRequest(
            scenario_id=cfg.scenario_id or default_sid,
            start_url=cfg.start_url,
            steps=list(cfg.steps),
        )
    # mcp
    return BrowserRunRequest(
        scenario_id=cfg.scenario_id,
        fixture_relpath=cfg.fixture_relpath,
        start_url=cfg.start_url,
        steps=list(cfg.steps),
    )


def run_benchmark_browser_phase(
    *,
    repo_root: Path,
    variant: VariantSpec,
    prompt_id: str,
    environ: Mapping[str, str],
) -> tuple[BrowserRunResult, str]:
    """Execute the browser runner for a ``browser_mock`` variant; return result and markdown block.

    Raises ``RuntimeError`` when Playwright is requested but opt-in env is not set.
    """
    cfg = variant.browser or BrowserBenchConfig()
    if cfg.runner == "playwright" and environ.get("ALWM_BENCHMARK_PLAYWRIGHT") != "1":
        msg = (
            "Benchmark variant requests browser.runner playwright; set ALWM_BENCHMARK_PLAYWRIGHT=1 "
            "and install the optional '[browser]' extra plus Playwright browsers."
        )
        raise RuntimeError(msg)

    req = build_browser_run_request(cfg, variant.id, prompt_id)
    runner = create_browser_runner(
        cfg.runner,
        repo_root=repo_root,
        headless=True,
    )
    result = runner.run(req)
    block = evidence_to_prompt_block(result.evidence)
    return result, block


def augment_prompt_with_browser_evidence(base_prompt: str, *, runner_name: str, block: str) -> str:
    """Append a stable section so the provider sees browser context."""
    base = base_prompt.rstrip()
    return f"{base}\n\n## Browser evidence (runner={runner_name})\n\n{block}"
