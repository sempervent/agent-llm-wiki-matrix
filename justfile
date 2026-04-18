# agent-llm-wiki-matrix — run `just` to list recipes (https://github.com/casey/just)
#
# Canonical host workflow uses uv (see AGENTS.md): `uv venv`, `uv pip install`, `uv run …`.
# Recipes invoke tools via `uv run` so an activated venv is optional.

set dotenv-load

# Default: show available recipes
default:
    @just --list

# Install package (non-editable) — uses project .venv when present
install:
    uv pip install .

# Editable install + dev dependencies
install-dev:
    uv pip install -e ".[dev]"

test:
    uv run pytest tests/ --ignore=tests/integration

# Deterministic: committed examples/, fixtures/, and emitted campaign trees vs JSON Schema + Pydantic
validate-artifacts:
    uv run pytest tests/test_schema_drift_contracts.py -v

# Live Ollama / llama.cpp benchmark verification (opt-in env vars; skips if unreachable)
test-integration:
    uv run pytest tests/integration/ -v -m integration

# Full-stack smoke: pytest -m smoke, host `alwm` benchmark + campaign + validate, Docker compose + offline benchmark.
# On failure, prints a recovery analysis. `SMOKE_SKIP_DOCKER=1` skips Docker phases. See `docs/workflows/smoke.md`.
smoke:
    ./scripts/smoke.sh

lint:
    uv run ruff check src tests

fmt:
    uv run ruff format src tests

typecheck:
    uv run mypy src

ci: lint typecheck test

# MkDocs documentation site (`uv` installs the `docs` extra for the command)
docs:
    uv run --extra docs mkdocs serve -a 127.0.0.1:8000

docs-build:
    uv run --extra docs mkdocs build --strict

# Opt-in: pytest integration/ (Ollama + OpenAI-compatible benchmarks); skips unless env set / reachable
verify-live-providers:
    uv run pytest tests/integration/test_live_benchmark_providers.py -v -m integration --strict-markers

# Opt-in: Playwright file:// smoke (requires `uv pip install -e ".[browser]"` and `uv run playwright install chromium` on host)
verify-playwright-local:
    #!/usr/bin/env bash
    set -euo pipefail
    export ALWM_PLAYWRIGHT_SMOKE=1
    uv run pytest tests/integration/test_playwright_browser.py -v -m integration --strict-markers

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

# First-class local workflow: start Compose Ollama, pull gpt-oss:20b, verify via `alwm benchmark probe` (bind-mounted `./.ollama-models`).
ollama-gptoss-setup:
    ./scripts/ollama-gptoss-setup.sh

# Opt-in live smoke: minimal Ollama benchmark (requires `ollama-gptoss-setup` or equivalent). Not part of `just ci`.
smoke-ollama-live:
    ./scripts/smoke-ollama-live.sh

# Ollama + host OpenAI-compatible probe (inside compose; pulls ollama service)
benchmark-probe:
    docker compose --profile benchmark-probe run --rm benchmark-probe

benchmark-llamacpp:
    docker compose --profile benchmark-llamacpp run --rm benchmark-llamacpp

# campaign smoke test
campaign-smoke output_dir="/tmp/alwm-campaign-smoke" created_at="2026-04-17T00:00:00Z":
    rm -rf {{output_dir}}
    uv run alwm benchmark campaign run \
        --definition examples/campaigns/v1/minimal_offline.v1.yaml \
        --output-dir {{output_dir}} \
        --created-at {{created_at}}
    uv run alwm validate {{output_dir}}/manifest.json benchmark_campaign_manifest
    uv run alwm validate {{output_dir}}/campaign-summary.json campaign_summary


verify-campaign-smoke output_dir="/tmp/alwm-campaign-smoke" created_at="2026-04-17T00:00:00Z":
    rm -rf {{output_dir}}
    uv run alwm benchmark campaign run \
        --definition examples/campaigns/v1/minimal_offline.v1.yaml \
        --output-dir {{output_dir}} \
        --created-at {{created_at}}
    uv run alwm validate {{output_dir}}/manifest.json benchmark_campaign_manifest
    uv run alwm validate {{output_dir}}/campaign-summary.json campaign_summary


# Pull only (no probe). Prefer `just ollama-gptoss-setup` for start + pull + verify.
ollama-pull-model model="gpt-oss:20b":
    docker compose --profile benchmark-ollama up -d ollama
    docker compose --profile benchmark-ollama exec ollama ollama pull {{model}}
    docker compose --profile benchmark-ollama exec ollama ollama list

# Start Ollama (Compose), list models, then open an interactive REPL (Ctrl+D / exit to quit).
# Override model: `just ollama-chat model=gpt-oss:20b`. Pull first if missing: `just ollama-pull-model model=…`.
ollama-chat model="gpt-oss:20b":
    #!/usr/bin/env bash
    set -euo pipefail
    docker compose --profile benchmark-ollama up -d ollama
    echo "=== ollama list ==="
    docker compose --profile benchmark-ollama exec -it ollama ollama list
    echo ""
    echo "=== interactive chat: {{model}} (OLLAMA_MODEL for this session) ==="
    export OLLAMA_MODEL="{{model}}"
    docker compose --profile benchmark-ollama exec -it ollama ollama run "{{model}}"

# Back-compat name; same as smoke-ollama-live.
verify-ollama-gptoss-smoke:
    ./scripts/smoke-ollama-live.sh
