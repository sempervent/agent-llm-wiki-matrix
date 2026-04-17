# Evaluation pipeline

## Stages

1. **Ingest:** Parse Markdown wiki pages into `Thought` JSON (`alwm ingest`).
2. **Extract:** (Incremental) Pull structured claims or checklist items suitable for scoring—deterministic parsers first; optional LLM assist behind provider adapters.
3. **Evaluate:** Score subjects against JSON **rubrics** with explicit weights; persist `Evaluation` artifacts (`alwm evaluate`, or via benchmark cells). The default implementation uses **deterministic byte-hash scores** per criterion (no network).
4. **Compare:** Build **grid matrices** over evaluations and emit `ComparisonMatrix` JSON plus optional Markdown (`alwm compare`).
5. **Summarize:** Emit Markdown reports from `templates/report.md` plus structured `Report` JSON (`alwm report`).
6. **Benchmark (harness):** Load versioned YAML (`benchmarks/v1/` or `examples/benchmark_suites/v1/`) describing **prompts** (inline `text` or **`prompt_ref`** resolved through `prompts/registry.yaml`, with optional `prompt_registry_ref` on the definition and optional **`registry_version`** pin against the registry document version), **variants** (agent stack, backend, execution mode), run each cell through providers (`alwm benchmark run`), persist **`benchmark_request`** and **`benchmark_response`** with resolved prompt text plus provenance (`prompt_source`, registry id, document version, source file relpath when from registry), re-use rubric scoring, emit **grid** (variant × prompt) and **pairwise** (variant × variant mean score delta) matrices plus reports.

## Determinism

- Prefer fixtures and frozen inputs for CI.
- When LLMs are used, record provider id, model id, prompt version, and seed/settings in evaluation metadata.
- Offline benchmark runs set `ALWM_FIXTURE_MODE=1` and mock backends (or pass `--no-fixture-mock` for live integration).

## Current state

- **Rubric** schema and fixtures/examples are checked in (`schemas/v1/rubric.schema.json`).
- **Ingest / evaluate / compare / report** CLI commands run offline in tests.
- **Benchmark harness** runs end-to-end in `tests/test_benchmark.py` using `fixtures/benchmarks/offline.v1.yaml`. Registry-backed prompts are covered in `tests/test_benchmark_prompt_registry.py` and `examples/benchmark_suites/v1/registry.mixed.v1.yaml`.
