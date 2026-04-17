# AGENTS.md

Conventions for humans and coding agents working on **agent-llm-wiki-matrix**.

## Principles

- **Markdown-first, git-native**: prefer committed artifacts over undocumented local state.
- **Determinism**: tests and smoke pipelines must not depend on live network unless explicitly marked.
- **Typed contracts**: JSON Schema for structured data; YAML for human-edited config where appropriate.
- **Adapters, not fake integrations**: use interfaces and mocks until a real provider is wired and tested.
- **Docker-first runtime**: `Dockerfile`, `docker-compose.yml`, and `docker-bake.hcl` are source of truth for reproducible environments.

## Layout

| Path | Purpose |
| --- | --- |
| `docs/` | Architecture, workflows, implementation log |
| `schemas/` | JSON Schema definitions (versioned under `schemas/v1/` etc.) |
| `templates/` | Markdown report templates |
| `prompts/` | Versioned prompts + `registry.yaml` |
| `examples/` | Example JSON/Markdown validated in tests |
| `fixtures/` | Deterministic inputs for offline tests |
| `src/agent_llm_wiki_matrix/` | Python package (CLI, pipelines) |
| `tests/` | Pytest suite |

## Commands

- Install: `pip install -e ".[dev]"` (Python 3.11+ recommended; matches `Dockerfile`).
- CI parity: `make ci` (ruff, mypy, pytest).
- CLI entrypoint: `alwm` (`alwm version`, `alwm info`).
- Images: `make docker-build` or `make docker-bake` (multi-arch; see `docker-bake.hcl`).

## Implementation phases

Follow the phased roadmap in `docs/implementation-log.md`. Complete a phase, commit, and update architecture docs before expanding scope.

## Commits

Use complete-sentence messages describing *what* changed and *why*. Keep diffs focused; avoid drive-by refactors.
