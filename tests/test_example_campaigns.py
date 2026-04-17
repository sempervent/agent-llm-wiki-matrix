from __future__ import annotations

from pathlib import Path

from agent_llm_wiki_matrix.benchmark import load_benchmark_definition


def test_example_campaign_definitions_load() -> None:
    root = Path(__file__).resolve().parents[1] / "examples" / "benchmark_suites" / "v1"
    for name in (
        "campaign.neutral.v1.yaml",
        "campaign.failure_heavy.v1.yaml",
        "campaign.success_heavy.v1.yaml",
    ):
        path = root / name
        assert path.is_file()
        definition = load_benchmark_definition(path)
        assert definition.id.startswith("bench.examples.campaign.")
        assert len(definition.prompts) == 5
        assert len(definition.variants) >= 2
