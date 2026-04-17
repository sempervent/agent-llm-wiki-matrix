# Evaluation pipeline

## Stages

1. **Ingest:** Parse Markdown wiki pages into `Thought` JSON (`alwm ingest`).
2. **Extract:** (Incremental) Pull structured claims or checklist items suitable for scoring—deterministic parsers first; optional LLM assist behind provider adapters.
3. **Evaluate:** Score subjects against JSON **rubrics** with explicit weights; persist `Evaluation` artifacts (`alwm evaluate`, or via benchmark cells). The default implementation uses **deterministic byte-hash scores** per criterion (no network).
4. **Compare:** Build **grid matrices** over evaluations and emit `ComparisonMatrix` JSON plus optional Markdown (`alwm compare`).
5. **Summarize:** Emit Markdown reports from `templates/report.md` plus structured `Report` JSON (`alwm report`).
6. **Benchmark (harness):** Load versioned YAML (`benchmarks/v1/`) describing **prompts**, **variants** (agent stack, backend, execution mode), run each cell through providers (`alwm benchmark run`), persist **`benchmark_response`** artifacts, re-use rubric scoring, emit **grid** (variant × prompt) and **pairwise** (variant × variant mean score delta) matrices plus reports.

## Determinism

- Prefer fixtures and frozen inputs for CI.
- When LLMs are used, record provider id, model id, prompt version, and seed/settings in evaluation metadata.
- Offline benchmark runs set `ALWM_FIXTURE_MODE=1` and mock backends (or pass `--no-fixture-mock` for live integration).

## Current state

- **Rubric** schema and fixtures/examples are checked in (`schemas/v1/rubric.schema.json`).
- **Ingest / evaluate / compare / report** CLI commands run offline in tests.
- **Benchmark harness** runs end-to-end in `tests/test_benchmark.py` using `fixtures/benchmarks/offline.v1.yaml`.
