# Live runtime verification (opt-in)

**Canonical offline verification** (default merge bar), **fallback commands without `just`**, and how **`just validate-artifacts`** relates to **`just ci`**: **[verification.md](verification.md)**.

Default **`uv run just ci`** and **`uv run just test`** stay **deterministic**: no Docker daemons, no Ollama, no llama-server, no Playwright browsers. **This document** describes **optional** checks for real backends and the Playwright runner. Host commands assume **[uv](https://docs.astral.sh/uv/)** (see **`AGENTS.md`**).

## Modes

| Mode | Fixture / network | How to run |
| --- | --- | --- |
| **Offline / deterministic** | `ALWM_FIXTURE_MODE=1` forces mock providers in benchmarks; unit tests use fixtures | `uv run just ci`, `uv run just test` |
| **Live verification** | Real HTTP to Ollama, OpenAI-compatible servers, or local Playwright | Env flags + commands below; always **skips** when services are missing |

## Live provider benchmarks (Ollama + OpenAI-compatible)

1. Start **Ollama** and/or an **OpenAI-compatible** HTTP server (e.g. llama.cpp `llama-server` on the host).
2. Set **one or both**:
   - `ALWM_LIVE_BENCHMARK_OLLAMA=1` — uses `OLLAMA_HOST` (default `http://127.0.0.1:11434`) and `OLLAMA_MODEL` (default **`gpt-oss:20b`**).
   - `ALWM_LIVE_BENCHMARK_LLAMACPP=1` — uses `OPENAI_BASE_URL` and `OPENAI_MODEL`.
3. Run:

```bash
uv run just verify-live-providers
# or: uv run just test-integration
# or: uv run pytest tests/integration/test_live_benchmark_providers.py -v -m integration
```

Tests **skip** when the flag is unset, when probes fail, or when Ollama has no matching model.

### Docker Compose (full benchmark cells)

| Recipe | Profile |
| --- | --- |
| `just ollama-gptoss-setup` | Pull **gpt-oss:20b** + **`alwm benchmark probe`** (see **`docs/workflows/benchmarking.md`**) |
| `just benchmark-ollama` | `benchmark-ollama` — healthy Ollama + `benchmarks/v1/ollama.v1.yaml` → `out/benchmark-ollama` |
| `just smoke-ollama-live` | Host minimal live Ollama benchmark (opt-in) |
| `just benchmark-llamacpp` | `benchmark-llamacpp` — host OpenAI-compatible URL → `out/benchmark-llamacpp` |
| `just benchmark-probe` | `benchmark-probe` — `alwm benchmark probe` only (reachability; no full benchmark) |

See [benchmarking.md](benchmarking.md) for details.

## MCP stdio browser runner (local protocol, fixture data)

1. Install **dev** extras so the MCP Python SDK is available:

   ```bash
   uv pip install -e ".[dev]"
   ```

2. From the repo root, point **`ALWM_MCP_BROWSER_COMMAND`** at the **FastMCP** fixture server (shell-parsed argv):

   ```bash
   export ALWM_MCP_BROWSER_COMMAND="python fixtures/mcp_servers/stdio_browser_evidence_server.py"
   uv run alwm browser run-mcp --stdio --step alwm:checkout_flow
   ```

   The server returns committed JSON from **`fixtures/browser_evidence/v1/`** (see scenario table in **`docs/architecture/browser.md`**). This verifies the **MCP client + validation** path over stdio; it is **not** a remote or IDE-hosted integration.

3. **Coverage:** `tests/test_mcp_stdio.py` runs the same stack in CI (subprocess + MCP protocol; still no browser binary).

## Playwright browser runner

1. Install optional deps on the **host** (not required for CI):

   ```bash
   uv pip install -e ".[browser]"
   uv run playwright install chromium
   ```

2. Run integration tests against an offline `file://` HTML fixture:

   ```bash
   export ALWM_PLAYWRIGHT_SMOKE=1
   uv run just verify-playwright-local
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
