# agent-llm-wiki-matrix — run `just` to list recipes (https://github.com/casey/just)

set dotenv-load

# Prefer project venv when present (same behavior as the former Makefile).
python := `test -x .venv/bin/python && echo .venv/bin/python || command -v python3`
pip := python + " -m pip"

# Default: show available recipes
default:
    @just --list

# Install package (non-editable)
install:
    {{pip}} install .

# Editable install + dev dependencies
install-dev:
    {{pip}} install -e ".[dev]"

test:
    {{python}} -m pytest tests/ --ignore=tests/integration

# Live Ollama / llama.cpp benchmark verification (opt-in env vars; skips if unreachable)
test-integration:
    {{python}} -m pytest tests/integration/ -v -m integration

smoke:
    {{python}} -m pytest tests/test_smoke.py -v

lint:
    {{python}} -m ruff check src tests

fmt:
    {{python}} -m ruff format src tests

typecheck:
    {{python}} -m mypy src

ci: lint typecheck test

# Opt-in: pytest integration/ (Ollama + OpenAI-compatible benchmarks); skips unless env set / reachable
verify-live-providers:
    {{python}} -m pytest tests/integration/test_live_benchmark_providers.py -v -m integration --strict-markers

# Opt-in: Playwright file:// smoke (requires `pip install -e ".[browser]"` and `playwright install chromium` on host)
verify-playwright-local:
    #!/usr/bin/env bash
    set -euo pipefail
    export ALWM_PLAYWRIGHT_SMOKE=1
    {{python}} -m pytest tests/integration/test_playwright_browser.py -v -m integration --strict-markers

# Build browser-test image and run Playwright integration tests in Compose (headless; no external network)
browser-verify:
    docker compose --profile browser-verify run --rm browser-verify

docker-build:
    docker build -t agent-llm-wiki-matrix:local -f Dockerfile .

docker-bake:
    docker buildx bake

compose-help:
    #!/usr/bin/env bash
    set -euo pipefail
    profiles=(dev test benchmark benchmark-offline benchmark-ollama benchmark-probe benchmark-llamacpp browser-verify)
    for p in "${profiles[@]}"; do
      docker compose --profile "$p" config >/dev/null
    done
    for p in "${profiles[@]}"; do
      docker compose --profile "$p" config --services
    done

benchmark-offline:
    docker compose --profile benchmark-offline run --rm benchmark-offline

benchmark-ollama:
    docker compose --profile benchmark-ollama run --rm benchmark-ollama

# Ollama + host OpenAI-compatible probe (inside compose; pulls ollama service)
benchmark-probe:
    docker compose --profile benchmark-probe run --rm benchmark-probe

benchmark-llamacpp:
    docker compose --profile benchmark-llamacpp run --rm benchmark-llamacpp
