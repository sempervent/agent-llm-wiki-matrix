# Benchmark definitions (v1)

Versioned YAML files consumed by `alwm benchmark run`.

| File | Purpose |
| --- | --- |
| `offline.v1.yaml` | All **mock** backends; deterministic with `ALWM_FIXTURE_MODE=1` (default offline Compose profile). |
| `ollama.v1.yaml` | Single **Ollama** variant; use with `benchmark-ollama` Compose profile (pull a model first). |
| `llamacpp.v1.yaml` | **OpenAI-compatible** backend (e.g. llama.cpp `llama-server`); use `benchmark-llamacpp` and set `LLAMACPP_OPENAI_BASE_URL` if needed. |

Mirror for tests: `fixtures/benchmarks/offline.v1.yaml` matches `offline.v1.yaml`.
