# Live runtime verification (opt-in)

Default **`just ci`** and **`just test`** stay **deterministic**: no Docker daemons, no Ollama, no llama-server, no Playwright browsers. This document describes **optional** checks for real backends and the Playwright runner.

## Modes

| Mode | Fixture / network | How to run |
| --- | --- | --- |
| **Offline / deterministic** | `ALWM_FIXTURE_MODE=1` forces mock providers in benchmarks; unit tests use fixtures | `just ci`, `just test` |
| **Live verification** | Real HTTP to Ollama, OpenAI-compatible servers, or local Playwright | Env flags + commands below; always **skips** when services are missing |

## Live provider benchmarks (Ollama + OpenAI-compatible)

1. Start **Ollama** and/or an **OpenAI-compatible** HTTP server (e.g. llama.cpp `llama-server` on the host).
2. Set **one or both**:
   - `ALWM_LIVE_BENCHMARK_OLLAMA=1` — uses `OLLAMA_HOST` (default `http://127.0.0.1:11434`) and `OLLAMA_MODEL`.
   - `ALWM_LIVE_BENCHMARK_LLAMACPP=1` — uses `OPENAI_BASE_URL` and `OPENAI_MODEL`.
3. Run:

```bash
just verify-live-providers
# or: just test-integration
# or: pytest tests/integration/test_live_benchmark_providers.py -v -m integration
```

Tests **skip** when the flag is unset, when probes fail, or when Ollama has no matching model.

### Docker Compose (full benchmark cells)

| Recipe | Profile |
| --- | --- |
| `just benchmark-ollama` | `benchmark-ollama` — healthy Ollama + `benchmarks/v1/ollama.v1.yaml` → `out/benchmark-ollama` |
| `just benchmark-llamacpp` | `benchmark-llamacpp` — host OpenAI-compatible URL → `out/benchmark-llamacpp` |
| `just benchmark-probe` | `benchmark-probe` — `alwm benchmark probe` only (reachability; no full benchmark) |

See [benchmarking.md](benchmarking.md) for details.

## Playwright browser runner

1. Install optional deps on the **host** (not required for CI):

   ```bash
   pip install -e ".[browser]"
   python -m playwright install chromium
   ```

2. Run integration tests against an offline `file://` HTML fixture:

   ```bash
   export ALWM_PLAYWRIGHT_SMOKE=1
   just verify-playwright-local
   ```

3. Or run the same tests **in Docker** (builds the `browser-test` image with Chromium):

   ```bash
   just browser-verify
   ```

CLI: `alwm browser run-playwright --start-url …` (requires `[browser]` installed).

## Markers

| Pytest marker | Meaning |
| --- | --- |
| `integration` | Under `tests/integration/`; excluded from default `just test` |
| `live_ollama` | Ollama benchmark cell test |
| `live_llamacpp` | OpenAI-compatible benchmark cell test |
| `live_playwright` | Playwright smoke tests |
