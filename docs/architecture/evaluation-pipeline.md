# Evaluation pipeline

## Stages

1. **Ingest:** Parse Markdown wiki pages into `Thought` JSON (`alwm ingest`).
2. **Extract:** (Incremental) Pull structured claims or checklist items suitable for scoring—deterministic parsers first; optional LLM assist behind provider adapters.
3. **Evaluate:** Score subjects against JSON **rubrics** with explicit weights; persist `Evaluation` artifacts (`alwm evaluate`, or via benchmark cells). The default path uses **deterministic byte-hash scores** per criterion (no network). Optional backends (**`semantic_judge`**, **`hybrid`**) call an LLM judge that returns JSON criterion scores; **`EvaluationJudgeProvenance`** records the judge prompts, provider kind/model, raw response(s), aggregated parsed scores, and (for hybrid) deterministic vs semantic components. Multiple **repeated** judge runs (`judge_repeats` > 1) aggregate per-criterion scores with **mean**, **median**, or **trimmed mean**, persist **per-run** records under **`repeat_aggregation`**, and compute **disagreement** metrics plus optional **low-confidence** flags when thresholds are exceeded. In **`ALWM_FIXTURE_MODE=1`**, the judge uses a **mock provider** with deterministic pseudo-semantic scores unless **`ALWM_JUDGE_LIVE=1`** (opt-in live judge for local runs).
4. **Compare:** Build **grid matrices** over evaluations and emit `ComparisonMatrix` JSON plus optional Markdown (`alwm compare`).
5. **Summarize:** Emit Markdown reports from `templates/report.md` plus structured `Report` JSON (`alwm report`).
6. **Benchmark (harness):** Load versioned YAML (`benchmarks/v1/` or `examples/benchmark_suites/v1/`) describing **prompts** (inline `text` or **`prompt_ref`** resolved through `prompts/registry.yaml`, with optional `prompt_registry_ref` on the definition and optional **`registry_version`** pin against the registry document version), **variants** (agent stack, backend, execution mode), run each cell through providers (`alwm benchmark run`), persist **`benchmark_request`** and **`benchmark_response`** with resolved prompt text plus provenance (`prompt_source`, registry id, document version, source file relpath when from registry), re-use rubric scoring, emit **grid** (variant × prompt) and **pairwise** (variant × variant mean score delta) matrices plus reports. **`manifest.json`** records optional **`definition_source_relpath`** (when the CLI knows the definition path relative to the repo) and **`prompt_registry_effective_ref`** when any cell used **`prompt_ref`**, so runs remain comparable across machines.
7. **Campaign (multi-run):** Optional **`alwm benchmark campaign run`** loads a **campaign definition** and invokes the harness once per expanded cell (suite × provider × scoring × browser axes), writing a **campaign manifest** (**`campaign_experiment_fingerprints`**: six axes) and **campaign summary** at the campaign root and standard **`benchmark_manifest`** trees under **`runs/runNNNN/`** (each with **six-axis** **`comparison_fingerprints`**). Longitudinal reporting consumes **`runs/*/manifest.json`** the same way as standalone runs; matrices and reports remain per member run unless you aggregate downstream. Walkthrough: **`docs/workflows/campaign-walkthrough.md`**.

## Determinism

- Prefer fixtures and frozen inputs for CI.
- When LLMs are used, record provider id, model id, prompt version, and seed/settings in evaluation metadata.
- Offline benchmark runs set `ALWM_FIXTURE_MODE=1` and mock backends (or pass `--no-fixture-mock` for live integration).

## Current state

- **Rubric** schema and fixtures/examples are checked in (`schemas/v1/rubric.schema.json`).
- **Ingest / evaluate / compare / report** CLI commands run offline in tests.
- **Benchmark harness** runs end-to-end in `tests/test_benchmark.py` using `fixtures/benchmarks/offline.v1.yaml`. Registry-backed prompts are covered in `tests/test_benchmark_prompt_registry.py`, `tests/test_benchmark_expansion.py`, `examples/benchmark_suites/v1/registry.mixed.v1.yaml`, and the **`suite.registry.*.v1.yaml`** example suites (plus `fixtures/benchmarks/suite_four_modes.v1.yaml`). **`manifest.json`** is validated as artifact kind **`benchmark_manifest`** (`schemas/v1/manifest.schema.json` + `BenchmarkRunManifest`); see `tests/test_manifest.py`. Semantic scoring without network is covered in **`tests/test_evaluation_backends.py`** (`eval_scoring.backend: semantic_judge` on an in-memory definition; repeated runs and **`repeat_aggregation`** included).
