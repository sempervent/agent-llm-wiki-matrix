# Verification surface (host)

This document is the **single place** that ties together:

- **Canonical commands** (via **`just`** recipes — they call **`uv run`** internally).
- **Fallback commands** when **`just`** is not installed (same tools, explicit **`uv run`**).
- **Optional** checks that require live services, browsers, or Docker (never the default merge bar).

**Prerequisites:** editable install with dev dependencies — **`uv pip install -e ".[dev]"`** from the repo root (see **`AGENTS.md`**). Use **`uv run …`** so the project interpreter and dependencies are used consistently.

**Publication stack (v0.2.5):** [Roadmap](../roadmap/v0.2.5.md) · [Operator checklist: result packs](campaign-result-pack-publication.md) · [Benchmark campaigns (CLI)](benchmark-campaigns.md) · [Releases / v0.2.4](../releases/v0.2.4.md).

---

## Matrix

| Intent | Canonical (`just` + `uv`) | Fallback (no `just`; repo root) | Notes |
| --- | --- | --- | --- |
| **Default CI parity** — lint, typecheck, full offline tests | **`uv run just ci`** (or activate `.venv` and **`just ci`**) | **`uv run ruff check src tests`** && **`uv run mypy src`** && **`uv run pytest tests/ --ignore=tests/integration`** | Same as **`just ci`** → `lint` + `typecheck` + `test` (`justfile`). Excludes **`tests/integration/`**. |
| **Unit / offline tests only** | **`uv run just test`** | **`uv run pytest tests/ --ignore=tests/integration`** | Identical to the **`test`** recipe. |
| **Committed JSON contracts** (examples + fixtures drift guard) | **`uv run just validate-artifacts`** | **`uv run pytest tests/test_schema_drift_contracts.py -v`** | Focused run of **`tests/test_schema_drift_contracts.py`** only. Inventory: **`docs/audits/schema-drift-contracts-inventory.md`**. This module also runs as part of the **full** pytest invocation above—it is **not** a substitute for **`just ci`**. |
| **Live providers** (Ollama / OpenAI-compatible HTTP) | **`uv run just test-integration`** or **`uv run just verify-live-providers`** | Same (recipes are thin wrappers) | Requires env flags and reachable services. See **[live-verification.md](live-verification.md)**. |
| **Playwright (host)** | **`uv run just verify-playwright-local`** | Same | Requires **`[browser]`** + **`playwright install`**. See **[live-verification.md](live-verification.md)**. |
| **Playwright (Docker image)** | **`just browser-verify`** | — | Uses Compose profile **`browser-verify`**. |
| **Full-stack smoke** (pytest + CLI + Docker phases) | **`just smoke`** | Run **`./scripts/smoke.sh`** directly (see **[smoke.md](smoke.md)**); optional **`SMOKE_SKIP_DOCKER=1`**) | Supplementary gate; not the same as **`just ci`**. |
| **Documentation site** (MkDocs preview / build) | **`just docs`** / **`just docs-build`** | **`uv run --extra docs mkdocs serve -a 127.0.0.1:8000`** / **`uv run --extra docs mkdocs build --strict`** | Opt-in for docs contributors; requires **`uv pip install -e ".[docs]"`** (or **`.[dev,docs]`**). Handbook: **[docs-site.md](docs-site.md)**. |
| **Docs CI** (GitHub Actions) | — | — | **`.github/workflows/docs.yml`** runs **`mkdocs build --strict`** on PRs/pushes that touch `docs/**` or **`mkdocs.yml`**; deploys **`gh-pages`** on **`main`** (see **[docs-site.md](docs-site.md)**). Not part of **`just ci`**. |

---

## Relationships (avoid drift)

1. **`uv run just ci`** is the **authoritative default** for merge-quality verification: **Ruff** + **Mypy** + **all** tests under **`tests/`** except **`tests/integration/`**.
2. **`uv run just validate-artifacts`** runs **one** pytest module for **schema / committed-artifact** alignment. Use it for a **fast** contract check or when debugging drift; it does **not** run Ruff, Mypy, or the rest of the test suite.
3. **`uv run pytest tests/ --ignore=tests/integration`** matches **`just test`** and is the **middle step** of the fallback equivalent of **`just ci`** (with **lint** and **typecheck** run separately as in the matrix).
4. **Campaign publication** — operator checklist (**run → validate → pack → compare → publish**) with committed example paths: **[campaign-result-pack-publication.md](campaign-result-pack-publication.md)**. Uses **`alwm validate`** and **`just validate-artifacts`** for contracts; **`just ci`** remains the merge bar for code changes.

---

## Optional and live paths

- **[live-verification.md](live-verification.md)** — live Ollama / OpenAI-compatible benchmarks, Playwright smoke, env flags.
- **[smoke.md](smoke.md)** — **`just smoke`** / **`scripts/smoke.sh`**, recovery analysis, Docker skip.
- **[benchmarking.md](benchmarking.md)** — offline vs live benchmark workflows, **`ALWM_FIXTURE_MODE`**.

---

## Documentation consistency

These commands should stay aligned with **`justfile`**:

| Recipe | Definition (see `justfile`) |
| --- | --- |
| **`ci`** | `lint` + `typecheck` + `test` |
| **`test`** | `uv run pytest tests/ --ignore=tests/integration` |
| **`validate-artifacts`** | `uv run pytest tests/test_schema_drift_contracts.py -v` |

If you change **`justfile`**, update this doc, **`README.md`**, **`AGENTS.md`**, and any audit that references the same recipes.
