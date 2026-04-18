# agent-llm-wiki-matrix

Markdown-first, git-native **LLM wiki + comparison matrix** system for capturing ideas, experiments, evaluations, prompts, and reports as structured files. It supports reproducible benchmarking of multiple agent stacks and model backends (including local models via **Ollama** or switchable **OpenAI-compatible / llama.cpp** HTTP servers).

**Repository:** [github.com/sempervent/agent-llm-wiki-matrix](https://github.com/sempervent/agent-llm-wiki-matrix)  
**Changelog:** [CHANGELOG.md](CHANGELOG.md) · **Current milestone (v0.2.5):** [docs/roadmap/v0.2.5.md](docs/roadmap/v0.2.5.md) · [docs/tracking/v0.2.5-campaign.md](docs/tracking/v0.2.5-campaign.md) · **v0.2.4 notes:** [docs/releases/v0.2.4.md](docs/releases/v0.2.4.md) · **v0.2.3 notes:** [docs/releases/v0.2.3.md](docs/releases/v0.2.3.md) · **v0.2.2 notes:** [docs/releases/v0.2.2.md](docs/releases/v0.2.2.md) · **v0.2.1 notes:** [docs/releases/v0.2.1.md](docs/releases/v0.2.1.md) · **v0.1.0 notes:** [docs/releases/v0.1.0.md](docs/releases/v0.1.0.md) · **Release scope:** [docs/release-readiness.md](docs/release-readiness.md)

Contributors and coding agents should follow **`AGENTS.md`** for the full operating manual (contribution loop, decision rules, prompt registry policy, verification expectations, **multi-agent parallel work**, capability labels). **Verification commands** (canonical **`just`** recipes vs **`uv run`** fallbacks vs optional live): **`docs/workflows/verification.md`**. Parallel agents: see **`docs/workflows/multi-agent-parallel.md`**.

**Documentation site (MkDocs):** browse `docs/` as a navigable site with **`just docs`** (local preview; default **http://127.0.0.1:8000/**) or **`just docs-build`** (static output under **`site/`**, gitignored). **Navigation and config:** **`mkdocs.yml`** at the repo root (the **`nav:`** block is the sidebar). **Handbook** (commands, findings, agent conventions): **`docs/workflows/docs-site.md`**. Install **`uv pip install -e ".[docs]"`** (or **`.[dev,docs]`**) so **`mkdocs`** is available. **CI:** **`.github/workflows/docs.yml`** builds on changes to **`docs/**`** or **`mkdocs.yml`** (**`mkdocs build --strict`**; optional **`gh-pages`** deploy on **`main`**).

## Current milestone (v0.2.5)

**Mission:** **Publication-quality evidence packs and final report readability** — stronger **presentation** of **result packs** and **reports**, **comparison** workflow refinement, **deduplication** and polish in generated Markdown, **drift / validation** ergonomics, and **MkDocs** **navigation** quality—without changing **default offline CI**.

**Roadmap / tracking:** **[docs/roadmap/v0.2.5.md](docs/roadmap/v0.2.5.md)** · **[docs/tracking/v0.2.5-campaign.md](docs/tracking/v0.2.5-campaign.md)**. **Prior release:** **[v0.2.4](docs/releases/v0.2.4.md)** (E2E publication workflow, MkDocs site, compare **reader interpretation**, report readability).

**Canonical verification (host):**

| Step | Command | Role |
| --- | --- | --- |
| Default CI parity | **`uv run just ci`** (or **`just ci`** with an activated `.venv`) | ruff, mypy, pytest (`tests/`, excluding `tests/integration/`) |
| Committed artifact contracts | **`just validate-artifacts`** (or `uv run pytest tests/test_schema_drift_contracts.py`) | JSON Schema + Pydantic on swept `examples/` / `fixtures/`; see **[docs/workflows/verification.md](docs/workflows/verification.md)** |
| Campaign packs | **`alwm benchmark campaign pack`**, **`alwm benchmark campaign pack-check`**, **`alwm benchmark campaign compare-packs`**, **`alwm benchmark campaign compare`** | **E2E checklist:** **[docs/workflows/campaign-result-pack-publication.md](docs/workflows/campaign-result-pack-publication.md)** · CLI reference **[docs/workflows/benchmark-campaigns.md](docs/workflows/benchmark-campaigns.md)** · examples **[examples/campaign_result_packs/README.md](examples/campaign_result_packs/README.md)**, **[examples/campaign_compares/README.md](examples/campaign_compares/README.md)** |

Arc context: **[docs/roadmap/v0.2.0.md](docs/roadmap/v0.2.0.md)**.

### What shipped in v0.2.1 / v0.2.2 / v0.2.3 / v0.2.4

**v0.2.0** established **six-axis fingerprints** and **longitudinal** reporting columns. **v0.2.1** added **campaign doc consolidation**, **`campaign_semantic_summary`** rollups, **runtime observability**, **fixture-backed MCP** (`alwm browser run-mcp`), and **richer `BrowserEvidence`**. **v0.2.2** deepens **campaign reporting**, **semantic summaries**, **observability**, **browser evidence**, and a **minimal MCP stdio** path—see **[docs/releases/v0.2.2.md](docs/releases/v0.2.2.md)**. **v0.2.3** adds **result packs**, **pack and directory comparison**, **fingerprint interpretation**, **drift** tests, and **verification** matrix hardening—see **[docs/releases/v0.2.3.md](docs/releases/v0.2.3.md)**. **v0.2.4** delivers the **end-to-end publication** checklist, **MkDocs** site + CI, **compare reader interpretation**, and **campaign / compare Markdown** polish—see **[docs/releases/v0.2.4.md](docs/releases/v0.2.4.md)**.

## Goals

- **Markdown-first, git-native** artifacts: notes, matrices, rubrics, and reports live in the repo.
- **Comparison matrices** across agent stacks, models, backends, prompts, browser behaviors, and orchestration patterns.
- **Docker Compose** for local orchestration; **Docker Buildx Bake** for multi-platform images (`linux/amd64`, `linux/arm64` by default).
- **Deterministic pipelines** where possible: typed contracts, schemas, fixtures, and testable ingest → evaluate → compare → summarize flows.
- **Provider abstraction** for Ollama and OpenAI-compatible endpoints (see `docs/architecture/target-state.md`).

## Prerequisites

- **[uv](https://docs.astral.sh/uv/)** — **required** for local virtualenv creation, installs, and running Python tools (`uv pip`, `uv run`). See **`AGENTS.md`** (Python environment — uv).
- **[just](https://github.com/casey/just)** — **recommended** for **`just ci`**, **`just validate-artifacts`**, and other recipes (`brew install just` or see upstream). If **`just`** is unavailable, use the equivalent **`uv run …`** commands in **`docs/workflows/verification.md`**.
- Docker with Buildx, Docker Compose v2 (for container workflows)
- Python **3.11+** (see `pyproject.toml` `requires-python`; the `Dockerfile` uses 3.11). On the host, Python is normally provided via **`uv`** (e.g. `uv python install 3.11` or the interpreter implied by `uv venv --python 3.11`).

Do **not** use `python -m venv`, raw `pip install`, or alternate env managers for this repo unless you have a special reason; **`uv`** is the default and documented workflow.

---

## Exact quickstart (local Python)

From the repository root:

```bash
uv venv --python 3.11
uv pip install -e ".[dev]"
```

Then either **activate** the venv (`source .venv/bin/activate` on Unix; `.\.venv\Scripts\activate` on Windows) **or** prefix commands with **`uv run`** (recommended):

```bash
uv run alwm version
uv run alwm info
uv run alwm validate examples/v1/thought.json thought
uv run alwm validate examples/v1/rubric.json rubric
uv run alwm validate examples/browser_evidence/v1/export_flow.json browser_evidence
uv run alwm browser prompt-block examples/browser_evidence/v1/export_flow.json
uv run alwm providers show
uv run just ci
```

With an activated `.venv`, you can run `alwm …` and `just ci` without the `uv run` prefix. **Without `just`:** run **`uv run ruff check src tests`**, **`uv run mypy src`**, and **`uv run pytest tests/ --ignore=tests/integration`** (same as **`just ci`** — see **`docs/workflows/verification.md`**).

For **committed `examples/` / `fixtures/` contract drift** only, **`uv run just validate-artifacts`** (or **`uv run pytest tests/test_schema_drift_contracts.py -v`**) is a fast supplement; it does **not** replace the full **`just ci`** suite.

Optional Playwright-based browser capture (not required for `just ci`):

```bash
# uv pip install -e ".[browser]" && uv run playwright install chromium
# uv run alwm browser run-playwright …
```

**MCP stdio (optional, local protocol):** with **`uv pip install -e ".[dev]"`** (includes the `mcp` package), set **`ALWM_MCP_BROWSER_COMMAND`** to launch **`fixtures/mcp_servers/stdio_browser_evidence_server.py`**, then run **`alwm browser run-mcp --stdio`**. That is a **real** MCP client over stdio to a **local** subprocess; the shipped server still serves **committed** `BrowserEvidence` JSON (multi-scenario selection is documented in **`docs/architecture/browser.md`**). **Remote or IDE-hosted MCP** is not implemented here. The **`browser_realism.v1`** rubric judges whether answers **ground in that JSON**—it does not prove live DOM automation unless you pair it with Playwright-produced evidence.

---

## Benchmark quickstart (offline)

Runs versioned YAML under `benchmarks/v1/` or `fixtures/benchmarks/` (see `benchmarks/v1/README.md`). Each **prompt** is inline `text:` and/or a `prompt_ref` into `prompts/registry.yaml`. Variants choose **agent stack**, **backend** (`mock` / `ollama` / `openai_compatible`), and **execution mode** (`cli`, `browser_mock`, `repo_governed`). With **`ALWM_FIXTURE_MODE=1`**, backends resolve to deterministic mock output unless you opt out.

```bash
ALWM_FIXTURE_MODE=1 uv run alwm benchmark run \
  --definition fixtures/benchmarks/offline.v1.yaml \
  --output-dir out/benchmark-offline \
  --created-at 1970-01-01T00:00:00Z \
  --run-id local-bench

uv run alwm validate out/benchmark-offline/manifest.json benchmark_manifest
uv run alwm validate out/benchmark-offline/cells/v-cli__p-one/benchmark_response.json benchmark_response
```

Compose shortcuts (writes under `out/` in the mounted repo):

```bash
just benchmark-offline
just ollama-gptoss-setup   # start Ollama, pull gpt-oss:20b, verify (./.ollama-models)
just benchmark-ollama      # full benchmark using benchmarks/v1/ollama.v1.yaml (after setup)
just benchmark-llamacpp    # start llama-server on the host (default :8080/v1)
```

**Ollama + gpt-oss:20b:** Repo benchmarks and provider defaults use the **`gpt-oss:20b`** tag. Run **`just ollama-gptoss-setup`** once per machine (or after clearing models), then **`just benchmark-ollama`** or **`just smoke-ollama-live`** for a minimal live check. See **`docs/workflows/benchmarking.md`** (Ollama section + volume migration).

---

## Benchmark campaigns (multi-run orchestration)

**Campaigns** expand one YAML definition into many benchmark runs (suites × providers × eval scoring × browser overrides). The campaign root writes **`manifest.json`** (**`campaign_manifest`** / **`benchmark_campaign_manifest`**) with **`campaign_definition_fingerprint`** and **`campaign_experiment_fingerprints`** (six axes), **`campaign-summary.json`** (**`campaign_summary`**) / **`campaign-summary.md`**, and typically **`campaign-semantic-summary.json`** / **`.md`** (artifact kind **`campaign_semantic_summary`**: repeat-judge / semantic instability rollups—**counts may be zero** when all member runs use deterministic scoring only). Manifests may also record **timing / retry / judge-phase** summaries and **`generated_report_paths`** for comparative + semantic artifacts (details: **`docs/workflows/benchmarking.md`**). Each member run lives under **`runs/runNNNN/`** with **`benchmark_manifest`** (**`comparison_fingerprints`**). Point **`alwm benchmark longitudinal`** at **`runs/*/manifest.json`** for regression-style bundles.

```bash
ALWM_FIXTURE_MODE=1 uv run alwm benchmark campaign run \
  --definition examples/campaigns/v1/minimal_offline.v1.yaml \
  --output-dir examples/campaign_runs/minimal_offline

# Plan sweep only (no member runs/): either command writes campaign-dry-run.json + top-level manifest
uv run alwm benchmark campaign plan \
  --definition examples/campaigns/v1/minimal_offline.v1.yaml \
  --output-dir /tmp/campaign-plan
# equivalent: uv run alwm benchmark campaign run --dry-run …

uv run alwm validate examples/campaign_runs/minimal_offline/manifest.json campaign_manifest
uv run alwm validate examples/campaign_runs/minimal_offline/campaign-summary.json campaign_summary
# when present: uv run alwm validate …/campaign-semantic-summary.json campaign_semantic_summary
# Canonical outward-facing bundle (pack manifest + INDEX + mirrored layout): pack a finished campaign:
#   uv run alwm benchmark campaign pack examples/campaign_runs/minimal_offline --output-dir /tmp/pack --pack-id my-pack --source-label examples/campaign_runs/minimal_offline
#   uv run alwm benchmark campaign pack-check /tmp/pack
```

**Step-by-step (committed paths):** **`docs/workflows/campaign-walkthrough.md`**. Full field reference: **`docs/workflows/benchmark-campaigns.md`**. Index / tracking: **`docs/wiki/benchmark-campaigns.md`**, **`docs/wiki/campaign-orchestration.md`**, **`docs/tracking/benchmark-campaign-orchestration.md`**, **`docs/tracking/campaign-orchestration.md`**, ADR **`docs/architecture/adr/0001-benchmark-campaign-orchestration.md`**.

---

## Prompt registry quickstart

The registry file is `prompts/registry.yaml` (versioned prompt bodies under `prompts/versions/`).

```bash
uv run alwm prompts check
uv run alwm prompts list
uv run alwm prompts show scaffold.echo.v1
```

Benchmark definitions may reference prompts with `prompt_ref` (and optional `registry_version` pins). See `examples/benchmark_suites/v1/` and `docs/workflows/benchmarking.md`.

---

## Manifest validation example

Benchmark runs write `manifest.json`, validated as artifact kind **`benchmark_manifest`** (JSON Schema `schemas/v1/manifest.schema.json`).

```bash
uv run alwm validate examples/v1/manifest.json benchmark_manifest
```

Example run trees under `examples/benchmark_runs/*/manifest.json` are also valid for spot checks.

---

## Optional live verification commands

These are **not** part of default `just ci`. They need live HTTP endpoints, env vars, and/or the `[browser]` extra.

| Command | Purpose |
| --- | --- |
| `uv run just verify-live-providers` | Integration tests for Ollama / OpenAI-compatible benchmark paths (skip when unreachable) |
| `just ollama-gptoss-setup` | Start Compose Ollama, pull **gpt-oss:20b**, verify with **`alwm benchmark probe`** |
| `just smoke-ollama-live` | Opt-in minimal Ollama benchmark (`benchmarks/v1/ollama.v1.yaml`); not **`just ci`** |
| `uv run just verify-playwright-local` | Playwright smoke (`ALWM_PLAYWRIGHT_SMOKE=1`; install `[browser]` + browsers first) |
| `uv run just test-integration` | Full `tests/integration/` |
| `just benchmark-probe` | `alwm benchmark probe` inside Compose (see `justfile`) |
| `docker compose --profile browser-verify run --rm browser-verify` | Playwright tests in container (profile `browser-verify`) |

Details: `docs/workflows/benchmarking.md`, `docs/workflows/live-verification.md`.

---

## End-to-end pipeline (offline scoring)

Full scripted walkthrough (committed paths only, temp dir for outputs): **`docs/workflows/walkthrough-v0.1.0.md`**.

Compact inline example:

```bash
uv run alwm ingest examples/dataset/pages examples/dataset/thoughts --created-at 1970-01-01T00:00:00Z
uv run alwm evaluate --subject examples/dataset/pages/retrieval-basics.md \
  --rubric examples/v1/rubric.json \
  --out examples/dataset/evals/retrieval-basics.eval.json --id eval-retrieval-basics
uv run alwm compare examples/dataset/evals/retrieval-basics.eval.json \
  examples/dataset/evals/chunking-strategies.eval.json \
  --out examples/generated/wiki_matrix.json \
  --out-md examples/generated/wiki_matrix.md \
  --id wiki-matrix-001 \
  --title "Wiki pages (example dataset)"
uv run alwm report --matrix examples/generated/wiki_matrix.json \
  --out-json examples/generated/wiki_report.json \
  --out-md examples/generated/wiki_report.md \
  --id wiki-report-001
uv run alwm validate examples/generated/wiki_matrix.json matrix
uv run alwm validate examples/generated/wiki_report.json report
```

---

## Docker

```bash
cp .env.example .env
docker build -t agent-llm-wiki-matrix:local -f Dockerfile .
docker run --rm agent-llm-wiki-matrix:local version
```

## Buildx Bake (multi-arch)

Default platforms: **linux/amd64** and **linux/arm64** (`docker-bake.hcl`).

```bash
docker buildx bake
docker buildx bake orchestrator-amd64
docker buildx bake orchestrator-arm64
```

## Compose (profiles)

```bash
docker compose --profile dev run --rm orchestrator version
docker compose --profile test run --rm tests
docker compose --profile benchmark run --rm benchmark
docker compose --profile benchmark-offline run --rm benchmark-offline
just compose-help
```

See `docs/workflows/local-dev.md` for profile details (`dev`, `test`, `benchmark`, `benchmark-offline`, `benchmark-ollama`, `benchmark-llamacpp`, `browser-verify`).

---

## Architecture (summary)

| Layer | Role |
| --- | --- |
| **Docs** | `docs/` — architecture, workflows, implementation log |
| **Schemas** | JSON Schema for structured artifacts under `schemas/` |
| **Templates** | Markdown templates under `templates/` |
| **Prompts** | Versioned prompt registry under `prompts/` |
| **Python package** | `src/agent_llm_wiki_matrix` — CLI, pipelines, benchmark harness, validators |
| **Benchmarks** | `benchmarks/v1/*.yaml` — versioned definitions; `fixtures/benchmarks/` for tests |
| **Docker** | `Dockerfile`, `docker-compose.yml`, `docker-bake.hcl` |

Detailed diagrams and data flow: `docs/architecture/runtime.md`, `docs/architecture/data-model.md`, `docs/architecture/evaluation-pipeline.md`.

## Commands (just and CLI)

Run `just` with no arguments to list recipes. **Canonical vs fallback vs optional live verification:** **`docs/workflows/verification.md`**.

| Command | Description |
| --- | --- |
| `just install-dev` | `uv pip install -e ".[dev]"` — editable install with dev dependencies (see **`AGENTS.md`**) |
| `just test` | `uv run pytest tests/ --ignore=tests/integration` (same as fallback **`uv run pytest …`** in **`verification.md`**) |
| `just test-integration` | Opt-in live Ollama / OpenAI-compatible benchmark checks (`ALWM_LIVE_BENCHMARK_*`) |
| `just smoke` | Full-stack smoke (`scripts/smoke.sh`): pytest `-m smoke`, host `alwm` benchmark + campaign, Docker Compose + offline benchmark; recovery analysis on failure — see `docs/workflows/smoke.md` |
| `just lint` | Ruff check |
| `just fmt` | Ruff format |
| `just typecheck` | Mypy |
| `just ci` | **Ruff** + **mypy** + **`just test`** — default merge-quality bar (see **`verification.md`**) |
| `just validate-artifacts` | **Only** `tests/test_schema_drift_contracts.py` (fast committed JSON contract sweep); also runs inside full **`pytest tests/`**; does **not** replace **`just ci`** — **`docs/audits/schema-drift-contracts-inventory.md`** |
| `just docker-build` | Build local image (`runtime` target) |
| `just docker-bake` | Multi-arch bake via `docker-bake.hcl` |
| `just compose-help` | Validate Compose for dev/test/benchmark + benchmark-offline/ollama/llamacpp |
| `just benchmark-offline` | Run mock benchmark via Compose → `out/benchmark-offline` |
| `just ollama-gptoss-setup` | Ollama service: pull **gpt-oss:20b** + probe (see **`.ollama-models`**) |
| `just benchmark-ollama` | Ollama + `benchmarks/v1/ollama.v1.yaml` → `out/benchmark-ollama` (run **`ollama-gptoss-setup`** first) |
| `just smoke-ollama-live` | Host minimal live Ollama benchmark (opt-in) |
| `just benchmark-probe` | `alwm benchmark probe` in Compose (Ollama + host OpenAI URL) |
| `just benchmark-llamacpp` | OpenAI-compatible endpoint on host → `out/benchmark-llamacpp` |
| `alwm validate <file> <kind>` | Validate JSON against schema + Pydantic (includes `browser_evidence`, `benchmark_manifest`) |
| `alwm browser prompt-block <file>` | Load browser evidence JSON → stable prompt-sized text |
| `alwm browser run-mock` | Run `MockBrowserRunner` (deterministic; no browser binary) |
| `alwm browser run-mcp` | `MCPBrowserRunner`: fixture JSON (`--scenario-id` / `--fixture`) or MCP stdio (`--stdio` + `ALWM_MCP_BROWSER_COMMAND`); see `docs/architecture/browser.md` |
| `alwm browser run-playwright` | Run `PlaywrightBrowserRunner` (requires `uv pip install -e ".[browser]"` and `uv run playwright install …`; not used in default CI) |
| `alwm ingest <input_dir> <output_dir>` | Markdown pages → Thought JSON |
| `alwm evaluate --subject … --rubric … --out …` | Deterministic rubric scoring |
| `alwm compare <eval.json>… --out … [--out-md …]` | Evaluations → matrix JSON (+ optional matrix Markdown) |
| `alwm report --matrix … --out-json … --out-md …` | Matrix → report JSON + Markdown |
| `alwm providers show` | Print resolved provider config (API keys redacted) |
| `alwm benchmark probe` | Check Ollama + OpenAI-compatible HTTP APIs (for live runs) |
| `alwm benchmark run --definition … --output-dir … [--prompt-registry PATH]` | Full harness: responses → evals → matrices + report; manifests may include **timing / retry / judge-phase** summaries; `browser_mock` variants run the browser phase and write **`browser_evidence.json`** (fixtures by default); Playwright requires `ALWM_BENCHMARK_PLAYWRIGHT=1` + `[browser]` extra |
| `alwm benchmark campaign run` / `plan` / `pack` / `compare-packs` / `compare` | Campaign sweep, dry-run planning, **result pack** assembly, **two-pack** comparison (`pack-compare.json`), or **two campaign directory** comparison (`campaign-compare.json`); see **`docs/workflows/benchmark-campaigns.md`** |
| `alwm benchmark longitudinal --runs-glob … --out-dir …` | Longitudinal Markdown + `summary.json` from benchmark manifests (glob relative to repo root) |
| `alwm prompts check` / `list` / `show <id>` | Validate and read `prompts/registry.yaml` (paths relative to repo root) |

## Repository layout

```
├── AGENTS.md              # Operating manual for agents (mission, loops, verification, prompts)
├── CHANGELOG.md           # Version history
├── docker-compose.yml
├── docker-bake.hcl
├── Dockerfile
├── justfile               # just task runner (https://github.com/casey/just)
├── pyproject.toml
├── schemas/               # JSON Schemas (v1)
├── templates/             # Markdown report templates
├── prompts/               # Versioned prompts
├── config/                # Optional provider YAML (see providers.example.yaml)
├── examples/              # Example artifacts + dataset + generated matrix/report + browser evidence
├── benchmarks/v1/         # Versioned benchmark YAML
├── fixtures/              # Deterministic test inputs (+ benchmarks/, browser_evidence/)
├── src/agent_llm_wiki_matrix/
├── tests/
└── docs/
```

## License

MIT — see `LICENSE`.
