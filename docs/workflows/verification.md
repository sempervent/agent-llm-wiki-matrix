# Verification surface (host)

This document is the **single place** that ties together:

- **Canonical commands** (via **`just`** recipes — they call **`uv run`** internally).
- **Fallback commands** when **`just`** is not installed (same tools, explicit **`uv run`**).
- **Optional** checks that require live services, browsers, or Docker (never the default merge bar).

**Prerequisites:** editable install with dev dependencies — **`uv pip install -e ".[dev]"`** from the repo root (see **`AGENTS.md`**). Use **`uv run …`** so the project interpreter and dependencies are used consistently.

**Publication stack:** [Latest release / v0.2.5](../releases/v0.2.5.md) · [Roadmap (complete)](../roadmap/v0.2.5.md) · [Operator checklist: result packs](campaign-result-pack-publication.md) · [Benchmark campaigns (CLI)](benchmark-campaigns.md) · [Prior: v0.2.4](../releases/v0.2.4.md).

---

## Three layers (what each command proves)

Use this to avoid mixing up **one-off file checks**, **committed-tree drift guards**, and the **full merge bar**.

| Layer | Command | What it proves | When to use |
| --- | --- | --- | --- |
| **A — Per-file** | **`alwm validate <path> <kind>`** | One JSON file matches JSON Schema + Pydantic for a registered **`alwm validate`** kind. | After writing or regenerating a single artifact; copying commands from docs; checking **`out/…`** trees. Kinds: **`alwm validate --help`** (see **`src/agent_llm_wiki_matrix/artifacts.py`**). |
| **B — Drift sweep (committed)** | **`uv run just validate-artifacts`** | Globbed **`examples/`** + **`fixtures/`** (and paths in **[schema-drift-contracts-inventory.md](../audits/schema-drift-contracts-inventory.md)**) still validate—runs **only** **`tests/test_schema_drift_contracts.py`**. | Fast contract-only feedback; PRs that touch committed JSON; debugging drift without running Ruff/Mypy. |
| **C — Default CI** | **`uv run just ci`** | **Ruff** + **Mypy** + full **`pytest`** (excluding **`tests/integration/`**). **Includes** layer **B** because that test module is part of the default suite. | Merge-quality gate; any change that could break types, lint, or tests. |

**Relationships:**

- **B** is a **subset** of **C**: the drift tests run as part of **`just ci`**, but **`validate-artifacts`** alone skips Ruff, Mypy, and all non-drift tests.
- **A** does **not** replace **B** or **C**: it validates **one path** you name; it does not walk **`examples/`** / **`fixtures/`**.
- Not every JSON on disk is a registered **`alwm validate`** kind (e.g. some **`reports/campaign-analysis.json`** blobs)—see inventory **§ Not covered**.

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
| **Docs CI** (GitHub Actions) | — | — | **`.github/workflows/docs.yml`** runs **`mkdocs build --strict`** on PRs/pushes that touch `docs/**` or **`mkdocs.yml`**; on **`main`**, deploys with **`actions/deploy-pages`** (see **[docs-site.md](docs-site.md)** — **Pages** source must be **GitHub Actions**). Not part of **`just ci`**. |

---

## Relationships (avoid drift)

1. **`uv run just ci`** (layer **C**) is the **authoritative default** for merge-quality verification: **Ruff** + **Mypy** + **all** tests under **`tests/`** except **`tests/integration/`**.
2. **`uv run just validate-artifacts`** (layer **B**) runs **one** pytest module for **schema / committed-artifact** alignment. Use it for a **fast** contract-only check; it does **not** run Ruff, Mypy, or non-drift tests.
3. **`uv run pytest tests/ --ignore=tests/integration`** matches **`just test`** and is the **middle step** of the fallback equivalent of **`just ci`** (with **lint** and **typecheck** run separately as in the matrix).
4. **`alwm validate`** (layer **A**) is for **explicit path + kind**; combine with **`alwm validate --help`** when you are unsure of the kind name.
5. **Campaign publication** — operator checklist (**run → validate → pack → compare → publish**): **[campaign-result-pack-publication.md](campaign-result-pack-publication.md)**. Uses **A** for spot checks, **B** for repo contract drift, **C** for code changes.

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
