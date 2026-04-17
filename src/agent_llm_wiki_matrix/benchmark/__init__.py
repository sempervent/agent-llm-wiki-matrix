"""Benchmark harness: definitions, execution, matrices, and run orchestration."""

from typing import Any

from agent_llm_wiki_matrix.benchmark.definitions import (
    BenchmarkDefinitionV1,
    load_benchmark_definition,
)
from agent_llm_wiki_matrix.benchmark.errors import BenchmarkPromptResolutionError
from agent_llm_wiki_matrix.benchmark.prompt_resolution import (
    ResolvedBenchmarkPrompt,
    resolve_benchmark_prompts,
    resolve_registry_yaml_path,
)

__all__ = [
    "BenchmarkDefinitionV1",
    "BenchmarkPromptResolutionError",
    "ResolvedBenchmarkPrompt",
    "load_benchmark_definition",
    "resolve_benchmark_prompts",
    "resolve_registry_yaml_path",
    "run_benchmark",
]


def __getattr__(name: str) -> Any:
    # Lazy import avoids import cycle: artifacts → benchmark.manifest → package __init__ →
    # runner → pipelines → artifacts.
    if name == "run_benchmark":
        from agent_llm_wiki_matrix.benchmark.runner import run_benchmark as _run_benchmark

        return _run_benchmark
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
