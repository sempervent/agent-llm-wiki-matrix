# Release readiness audit (v0.1.0)

**Last verified:** 2026-04-17  
**Method:** Run project commands and read `pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `docker-bake.hcl`, `src/agent_llm_wiki_matrix/`. This file is **evidence for tagging**, not a product roadmap.

**Related:** [docs/release-readiness.md](../release-readiness.md) (summary), [CHANGELOG.md](../../CHANGELOG.md), [docs/releases/v0.1.0.md](../releases/v0.1.0.md).

---

## Version metadata

| Source | Value |
| --- | --- |
| `pyproject.toml` `[project] version` | `0.1.0` |
| `src/agent_llm_wiki_matrix/__init__.py` `__version__` | `0.1.0` |
| `alwm version` (after editable install) | `0.1.0` |

`tests/test_smoke.py::test_version_matches_package` asserts CLI output matches `__version__`.

---

## Default CI (`just ci`)

Command: `just ci` (ruff + mypy + `pytest tests/ --ignore=tests/integration`).

**Recorded result (2026-04-17):**

```text
85 passed, 1 skipped
```

```text
Success: no issues found in 42 source files   # mypy src
```

Ruff: all checks passed on `src`, `tests`.

---

## Docker Compose configuration

Command: `just compose-help` (validates each profile’s `docker compose config`).

**Profiles exercised:** `dev`, `test`, `benchmark`, `benchmark-offline`, `benchmark-ollama`, `benchmark-probe`, `benchmark-llamacpp`, `browser-verify`.

---

## Docker Buildx Bake

Command: `docker buildx bake --print` (default group → `orchestrator`).

**Recorded:** target `orchestrator`, `Dockerfile` target `runtime`, platforms **`linux/amd64`**, **`linux/arm64`**.

Single-arch convenience targets in `docker-bake.hcl`: `orchestrator-amd64`, `orchestrator-arm64`. Optional `browser-test` target: **`linux/amd64` only** (Playwright image).

---

## Opt-in integration verification (not part of `just ci`)

| Recipe | Purpose |
| --- | --- |
| `just verify-live-providers` | `tests/integration/test_live_benchmark_providers.py`; skips without live env |
| `just verify-playwright-local` | Sets `ALWM_PLAYWRIGHT_SMOKE=1`; requires `[browser]` + browser install |
| `just test-integration` | Full `tests/integration/` |

---

## Code inventory (static)

- **CLI entrypoint:** `alwm` → `agent_llm_wiki_matrix.cli:main` (`pyproject.toml` `[project.scripts]`).
- **Requires-Python:** `>=3.11` (`pyproject.toml`).
- **Docker base image:** `python:3.11-slim-bookworm` (`Dockerfile`).

---

## Gaps explicitly out of scope for v0.1.0

See [docs/release-readiness.md](../release-readiness.md#known-non-goals-for-v010).
