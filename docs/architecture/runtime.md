# Runtime architecture

## Python environment

- **Package:** `agent-llm-wiki-matrix` (import name `agent_llm_wiki_matrix`).
- **Interpreter:** 3.11+ recommended; Docker image uses `python:3.11-slim-bookworm`.
- **CLI:** `alwm` (Click). Global option `--log-level` / `ALWM_LOG_LEVEL`.
- **Logging:** `structlog` with ISO timestamps (UTC) to stderr.

## Environment variables

See `.env.example`. Notable keys:

| Variable | Purpose |
| --- | --- |
| `ALWM_LOG_LEVEL` | Logging verbosity |
| `ALWM_REPO_ROOT` | Repository root for schema paths and pipelines (Compose sets `/workspace`) |
| `ALWM_FIXTURE_MODE` | When `1`, benchmarks prefer fixtures and force mock backends unless `--no-fixture-mock` |
| `ALWM_PROVIDER` | `mock`, `ollama`, or `openai_compatible` |
| `ALWM_PROVIDER_CONFIG` | Optional path to YAML (see `config/providers.example.yaml`) |
| `OLLAMA_HOST`, `OLLAMA_MODEL` | Ollama endpoint overrides (default model **gpt-oss:20b**) |
| `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `OPENAI_MODEL` | OpenAI-compatible server overrides |
| `LLAMACPP_OPENAI_BASE_URL` | Override for Compose **benchmark-llamacpp** (default `host.docker.internal:8080/v1`) |
| `ALWM_LIVE_BENCHMARK_OLLAMA` | Set `1` to enable opt-in pytest live Ollama benchmark tests |
| `ALWM_LIVE_BENCHMARK_LLAMACPP` | Set `1` for opt-in OpenAI-compatible benchmark tests |
| `ALWM_PLAYWRIGHT_SMOKE` | Set `1` for opt-in Playwright integration tests |
| `ALWM_MCP_BROWSER_COMMAND` | Optional: argv for a **local** MCP stdio server (see `docs/architecture/browser.md`) |
| `ALWM_MCP_BROWSER_TOOL` | Optional: MCP tool name for stdio mode (default `alwm_browser_evidence`) |
| `ALWM_MCP_BROWSER_CWD` | Optional: working directory for the MCP server process |

## Browser abstraction

- **Offline / CI:** `MockBrowserRunner`, `FileBrowserRunner`, JSON under `fixtures/browser_evidence/v1/` (see `docs/architecture/browser.md`).
- **CLI:** `alwm browser prompt-block <path>`, `alwm browser run-mock`, `alwm browser run-mcp` (fixtures and/or `--stdio` MCP), `alwm browser run-playwright` (requires `uv pip install -e '.[browser]'` and browser install via `uv run playwright install …`).
- **Optional live:** `PlaywrightBrowserRunner` in `browser/playwright_runner.py` maps sessions to `BrowserEvidence` (extra `[browser]`).
- **Partial:** `MCPBrowserRunner` — fixtures and optional **local stdio MCP** (`ALWM_MCP_BROWSER_COMMAND`; `mcp` from **dev** extras)—see `docs/architecture/browser.md`.

## Docker

- **Image:** `Dockerfile` `runtime` target (CLI); `test` target installs `.[dev]` for pytest; **`browser-test`** adds Playwright + Chromium for the optional **`browser-verify`** Compose profile.
- **Compose:** `orchestrator` (**dev**), `tests` (**test**), `benchmark` (**benchmark**), **`benchmark-offline`** (mock benchmark run), **`benchmark-ollama`**, **`benchmark-llamacpp`**, **`benchmark-probe`**, **`browser-verify`** (Playwright integration tests). All bind-mount the project to `/workspace`.
- **Bake:** `docker-bake.hcl` — variable `PLATFORM` (comma-separated) defaults to `linux/amd64,linux/arm64`; targets `orchestrator`, `orchestrator-amd64`, `orchestrator-arm64`, optional **`browser-test`** (amd64-only convenience image).

## Benchmark execution

- **Provider layer:** `BaseProvider.complete` via `providers/factory.py` (`mock`, `ollama`, `openai_compatible`).
- **Execution tagging:** `providers/execution.py` wraps outputs for `cli` vs `browser_mock` vs `repo_governed` so rubric scores differ by execution mode without a real browser.
- **Per-variant config:** `providers/benchmark_config.py` merges `ProviderConfig` with each variant’s backend; when `ALWM_FIXTURE_MODE=1`, backends are forced to **mock** unless `alwm benchmark run --no-fixture-mock`.

## CI-friendly commands

`just ci` runs Ruff, Mypy, and pytest **without** `tests/integration/`. `just benchmark-offline` runs the full harness in a container (mock-only, deterministic). Optional live checks are documented in `docs/workflows/live-verification.md`.
