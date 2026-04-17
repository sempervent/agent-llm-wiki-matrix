# Benchmark definitions (v1)

Versioned YAML files consumed by `alwm benchmark run`.

| File | Purpose |
| --- | --- |
| `offline.v1.yaml` | All **mock** backends; deterministic with `ALWM_FIXTURE_MODE=1` (default offline Compose profile). |
| `ollama.v1.yaml` | Single **Ollama** variant; use with `benchmark-ollama` Compose profile (pull a model first). |
| `llamacpp.v1.yaml` | **OpenAI-compatible** backend (e.g. llama.cpp `llama-server`); use `benchmark-llamacpp` and set `LLAMACPP_OPENAI_BASE_URL` if needed. |

Mirror for tests: `fixtures/benchmarks/offline.v1.yaml` matches `offline.v1.yaml`. Browser-backed examples: `fixtures/benchmarks/browser_file.v1.yaml`, `examples/benchmarks/v1/browser_file.v1.yaml`.

## Browser-backed variants (`execution_mode: browser_mock`)

Optional per-variant **`browser`** block (see `schemas/v1/benchmark_definition.schema.json`): **`runner`** (`mock` \| `file` \| `playwright` \| `mcp`), plus **`scenario_id`**, **`fixture_relpath`**, **`start_url`**, **`steps`** as required by the runner. Playwright cells need **`ALWM_BENCHMARK_PLAYWRIGHT=1`** and the optional **`[browser]`** Python extra plus Playwright browsers.

## Prompts

Each prompt entry must set exactly one of:

- **`text`:** inline string sent to the provider.
- **`prompt_ref`:** id from `prompts/registry.yaml` (or from the file given by optional top-level **`prompt_registry_ref`** on the definition). Optional **`registry_version`** must match the registry file’s top-level `version` when set.

See `schemas/v1/benchmark_definition.schema.json` and `examples/benchmark_suites/v1/registry.mixed.v1.yaml`.
