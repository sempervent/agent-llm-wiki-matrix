# Benchmark definitions (v1)

Versioned YAML files consumed by `alwm benchmark run`.

| File | Purpose |
| --- | --- |
| `offline.v1.yaml` | All **mock** backends; deterministic with `ALWM_FIXTURE_MODE=1` (default offline Compose profile). |
| `ollama.v1.yaml` | Single **Ollama** variant; use with `benchmark-ollama` Compose profile (pull a model first). |
| `llamacpp.v1.yaml` | **OpenAI-compatible** backend (e.g. llama.cpp `llama-server`); use `benchmark-llamacpp` and set `LLAMACPP_OPENAI_BASE_URL` if needed. |

Mirror for tests: `fixtures/benchmarks/offline.v1.yaml` matches `offline.v1.yaml`.

## Prompts

Each prompt entry must set exactly one of:

- **`text`:** inline string sent to the provider.
- **`prompt_ref`:** id from `prompts/registry.yaml` (or from the file given by optional top-level **`prompt_registry_ref`** on the definition). Optional **`registry_version`** must match the registry file’s top-level `version` when set.

See `schemas/v1/benchmark_definition.schema.json` and `examples/benchmark_suites/v1/registry.mixed.v1.yaml`.
