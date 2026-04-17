.PHONY: help install install-dev test lint typecheck fmt smoke docker-build docker-bake compose-help ci \
	benchmark-offline benchmark-ollama benchmark-llamacpp

PYTHON ?= $(shell test -x .venv/bin/python && echo .venv/bin/python || command -v python3)
PIP ?= $(PYTHON) -m pip

help:
	@echo "agent-llm-wiki-matrix — common commands"
	@echo ""
	@echo "  make install       Install package (editable not default; use pip install -e .)"
	@echo "  make install-dev   Install package + dev deps"
	@echo "  make test          Run pytest"
	@echo "  make smoke         Run smoke tests only"
	@echo "  make lint          Ruff check"
	@echo "  make fmt           Ruff format"
	@echo "  make typecheck     Mypy"
	@echo "  make ci            lint + typecheck + test"
	@echo "  make docker-build  docker build (current platform)"
	@echo "  make docker-bake   docker buildx bake (multi-arch per docker-bake.hcl)"
	@echo "  make compose-help  docker compose config (validate file)"
	@echo "  make benchmark-offline   Compose: mock benchmark → out/benchmark-offline"
	@echo "  make benchmark-ollama    Compose: Ollama + smoke benchmark (pull model first)"
	@echo "  make benchmark-llamacpp  Compose: OpenAI-compatible server on host :8080"

install:
	$(PIP) install .

install-dev:
	$(PIP) install -e ".[dev]"

test:
	$(PYTHON) -m pytest tests/

smoke:
	$(PYTHON) -m pytest tests/test_smoke.py -v

lint:
	$(PYTHON) -m ruff check src tests

fmt:
	$(PYTHON) -m ruff format src tests

typecheck:
	$(PYTHON) -m mypy src

ci: lint typecheck test

docker-build:
	docker build -t agent-llm-wiki-matrix:local -f Dockerfile .

docker-bake:
	docker buildx bake

compose-help:
	docker compose --profile dev config >/dev/null \
		&& docker compose --profile test config >/dev/null \
		&& docker compose --profile benchmark config >/dev/null \
		&& docker compose --profile benchmark-offline config >/dev/null \
		&& docker compose --profile benchmark-ollama config >/dev/null \
		&& docker compose --profile benchmark-llamacpp config >/dev/null \
		&& docker compose --profile dev config --services \
		&& docker compose --profile test config --services \
		&& docker compose --profile benchmark config --services \
		&& docker compose --profile benchmark-offline config --services \
		&& docker compose --profile benchmark-ollama config --services \
		&& docker compose --profile benchmark-llamacpp config --services

benchmark-offline:
	docker compose --profile benchmark-offline run --rm benchmark-offline

benchmark-ollama:
	docker compose --profile benchmark-ollama run --rm benchmark-ollama

benchmark-llamacpp:
	docker compose --profile benchmark-llamacpp run --rm benchmark-llamacpp
