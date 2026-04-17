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
    {{python}} -m pytest tests/

smoke:
    {{python}} -m pytest tests/test_smoke.py -v

lint:
    {{python}} -m ruff check src tests

fmt:
    {{python}} -m ruff format src tests

typecheck:
    {{python}} -m mypy src

ci: lint typecheck test

docker-build:
    docker build -t agent-llm-wiki-matrix:local -f Dockerfile .

docker-bake:
    docker buildx bake

compose-help:
    #!/usr/bin/env bash
    set -euo pipefail
    profiles=(dev test benchmark benchmark-offline benchmark-ollama benchmark-llamacpp)
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

benchmark-llamacpp:
    docker compose --profile benchmark-llamacpp run --rm benchmark-llamacpp
