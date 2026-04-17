"""Benchmark harness errors."""


class BenchmarkPromptResolutionError(ValueError):
    """Prompt registry lookup, version pin, or path resolution failed."""
