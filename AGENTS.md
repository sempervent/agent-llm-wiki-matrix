# AGENTS.md — Operating manual for coding agents

This repository is **agent-llm-wiki-matrix**: a markdown-first, git-native system for LLM wiki content, comparison matrices, benchmarks, providers (mock / Ollama / OpenAI-compatible), and browser evidence abstractions. Use this document to decide *what to do*, *how to know you are done*, and *what to avoid*.

---

## Mission and success criteria

**Mission:** Evolve and maintain a **reproducible**, **docs-first** toolkit where structured artifacts (schemas, fixtures, benchmarks, reports) live in git; orchestration is testable Python; runtime is Docker/Compose/Bake; and live backends are optional, explicit, and probe-tested.

**Success looks like:**

| Criterion | Signal |
| --- | --- |
| **Contracts are real** | JSON Schema + Pydantic (or documented exceptions) for user-facing payloads; `alwm validate` kinds stay in sync with `artifacts.py`. |
| **Default CI is offline** | `uv run just ci` (or `just ci` with an activated uv `.venv`) passes without Ollama, llama.cpp, or Playwright browsers; integration/live tests are opt-in (`tests/integration/`, env gates such as `ALWM_PLAYWRIGHT_SMOKE`, `ALWM_LIVE_BENCHMARK_*`). |
| **No silent drift** | Benchmarks, prompts, and CLI outputs that matter are covered by tests or documented as intentionally manual. |
| **Operations are discoverable** | `README.md`, `docs/workflows/`, `docs/architecture/`, and this file tell a contributor how to run, verify, and extend the system. |
| **Claims match evidence** | Features are labeled with the taxonomy in `docs/audits/capability-classification.md`; **complete** is not used without tests/commands to back it. |

## Releases and milestones (keep in sync with shipped work)

Use this section as the **single place** in `AGENTS.md` that ties **what shipped** to **what is in flight**. When you cut or plan a version, update **this block**, **`README.md`** (current milestone blurb), **`CHANGELOG.md`** (tagged section), **`docs/releases/v<version>.md`** (narrative), and **`docs/roadmap/`** / **`docs/tracking/`** as needed—see **Maintenance checklist** below.

### Latest shipped release (objectives)

| | |
| --- | --- |
| **Version** | **v0.2.4** (narrative: **[docs/releases/v0.2.4.md](docs/releases/v0.2.4.md)**) |
| **Objectives** | **End-to-end publication** workflow, **MkDocs** site + docs CI, **compare reader interpretation**, **campaign / compare / INDEX** readability, **operator rituals** aligned—**default CI** stays **offline**. |
| **Exit bar** | **`uv run just ci`**, **`just validate-artifacts`**, **`mkdocs build --strict`** (with **`[docs]`** extra); verification matrix and checklists—see release notes. |
| **Changelog** | **[CHANGELOG.md](CHANGELOG.md)** — **[0.2.4]**; new work accrues under **`[Unreleased]`** until the next tagged section. |

Older milestones for context: **[docs/releases/v0.2.2.md](docs/releases/v0.2.2.md)**, **[docs/roadmap/v0.2.0.md](docs/roadmap/v0.2.0.md)** (fingerprints + campaigns arc), **[docs/releases/v0.2.1.md](docs/releases/v0.2.1.md)**.

### In-flight milestone (v0.2.5 — evidence packs + report readability)

| | |
| --- | --- |
| **Version** | **v0.2.5** (active) |
| **Roadmap** | **[docs/roadmap/v0.2.5.md](docs/roadmap/v0.2.5.md)** |
| **Tracking** | **[docs/tracking/v0.2.5-campaign.md](docs/tracking/v0.2.5-campaign.md)** — workstreams, merge order, open questions |
| **Mission** | **Publication-quality evidence packs and final report readability**: **presentation** of packs and reports, **comparison** workflow refinement, **deduplication** in generated Markdown, **drift / validation** ergonomics, **MkDocs** **nav** quality (**`mkdocs.yml`**, **`just docs`**, **[docs/workflows/docs-site.md](docs/workflows/docs-site.md)**). |
| **Non-goals** | Dashboards, cloud deployment, remote/IDE MCP, replacing offline default CI with live defaults. |

**Canonical verification:** **`uv run just ci`** (default merge bar); **`just validate-artifacts`** (or **`uv run pytest tests/test_schema_drift_contracts.py`**) for committed JSON contracts—see **[docs/workflows/verification.md](docs/workflows/verification.md)** for the full matrix and **`uv run`** fallbacks.

**Prefer next:** **[docs/tracking/v0.2.5-campaign.md](docs/tracking/v0.2.5-campaign.md)** priorities. **Avoid** unrelated feature surface.

**MkDocs (keep in sync):** When you add or rename **user-facing** docs under **`docs/`**, update **`mkdocs.yml`** **`nav:`** so the site sidebar matches (see **[docs/workflows/docs-site.md](docs/workflows/docs-site.md)**). Run **`just docs-build`** before merging doc-only changes that touch **`nav`**. Do not duplicate long workflow text in **`docs/index.md`** — link to the publication checklist instead. **`README.md`** / **`AGENTS.md`** / **`CHANGELOG.md`** stay at repo root; the site links them under **Repository on GitHub**.

### Maintenance checklist (on each release or milestone shift)

1. Add or refresh **`docs/releases/v<version>.md`** (objectives, scope, verification).
2. Add a **`[x.y.z]`** section to **`CHANGELOG.md`** when the version is tagged (authoritative list of user-visible changes).
3. Update **Latest shipped release** (table above) to point at the new release doc and one-line objectives.
4. Create or retarget **`docs/roadmap/vNEXT.md`** and **`docs/tracking/…`** for the next in-flight milestone; update **In-flight milestone** (table above).
5. Align **`README.md`** “Current milestone” and this file so agents do not see conflicting “current” versions.

---

## Principles (unchanged)

- **Markdown-first, git-native**: prefer committed artifacts over undocumented local state.
- **Determinism**: tests and default pipelines must not depend on live network unless explicitly marked (`@pytest.mark.integration`, `ALWM_LIVE_BENCHMARK_*`, etc.).
- **Typed contracts**: JSON Schema for structured data; YAML for human-edited config where appropriate.
- **Adapters, not fake integrations**: use interfaces and mocks until a real provider or browser stack is wired **and** tested or explicitly stubbed with `NotImplementedError` and docs.
- **Docker-first runtime**: `Dockerfile`, `docker-compose.yml`, and `docker-bake.hcl` are the source of truth for reproducible images and Compose profiles.

---

## Python environment management (uv — required on the host)

**Canonical tooling:** **[uv](https://docs.astral.sh/uv/)** is **required** for local virtualenv creation, package installation, and running this project’s Python tools on the host (Python **3.11+**, matching `requires-python` and the `Dockerfile`). Do not document or recommend **`python -m venv`**, bare **`pip` / `pip install`** (outside what **`uv pip`** invokes), **`virtualenv`**, **Poetry**, **Pipenv**, or **Conda** for this repository unless the user **explicitly** asks for a different tool. **Docker** and **Compose** images use their own install path (`Dockerfile`); that is not a substitute for the host workflow below.

**Agents and contributors must:**

1. Create the project environment with **`uv venv`** (default path: **`.venv`** at the repo root).
2. Install the package and extras with **`uv pip`** (see **Canonical setup** — primarily `uv pip install -e ".[dev]"`).
3. Run project commands with **`uv run …`** so the correct interpreter and dependencies are used without relying on manual `PATH` hacks. Examples: `uv run alwm version`, `uv run pytest`, `uv run ruff check src`, `uv run mypy src`, `uv run just ci`. Activating `.venv` is optional if you prefer `uv run` for everything.

**`just` recipes** in this repo assume **`uv`** is on your `PATH` and use **`uv run`** for lint, tests, and typecheck (see `justfile`).

**Canonical setup (repository root):**

```bash
uv venv --python 3.11
uv pip install -e ".[dev]"
```

You can then use either activated shell (`source .venv/bin/activate` on Unix; `.\.venv\Scripts\activate` on Windows) **or** prefix commands with `uv run` (recommended in docs and CI parity examples).

Optional Playwright extra (not required for `just ci`):

```bash
uv pip install -e ".[browser]"
uv run playwright install chromium
```

---

## Required contribution loop

For any non-trivial change (feature, fix, refactor that touches behavior or contracts):

1. **Locate** — Identify the owning area: `benchmark/`, `pipelines/`, `providers/`, `browser/`, `schemas/`, `prompts/`, `docs/`.
2. **Contract** — If you add or change structured data, update **JSON Schema** and **Pydantic** (and `alwm validate` registration in `artifacts.py` when applicable).
3. **Verify** — Run **`uv run just ci`** (or activate `.venv` and run **`just ci`**); **without `just`**, use **`docs/workflows/verification.md`**. If you touch benchmarks or providers, consider **`uv run alwm benchmark probe`** or (opt-in) **`uv run just test-integration`**. Optional Playwright: **`ALWM_PLAYWRIGHT_SMOKE=1`** + **`tests/integration/`** (requires **`uv pip install -e '.[browser]'`** and **`uv run playwright install chromium`**).
4. **Document** — Append a dated entry to `docs/implementation-log.md`. If architecture or workflows change, update the relevant file under `docs/architecture/` or `docs/workflows/` (do not let docs rot).
5. **Report** — Commit message: full sentences, *what* + *why*; PR/description should list verification performed (`uv run just ci`, manual command, etc.).

**Phased work:** If the change fits a named phase in `docs/implementation-log.md`, note completion there and adjust `docs/architecture/current-state.md` when behavior materially changes.

---

## Decision rules

| Question | Default answer |
| --- | --- |
| Inline prompt text vs registry? | Prefer **`prompt_ref`** (+ file under `prompts/versions/`) and an entry in `prompts/registry.yaml` when the prompt is reused, versioned, or part of a benchmark suite. Use **inline `text`** only for one-off scratch definitions, transient experiments, or docs examples—then say so in the PR/note. See **Prompt registry** below. |
| New structured artifact type? | Add **JSON Schema** under `schemas/v1/`, model in `models.py` or the owning package, register in **`artifacts.py`**, add **fixture + example**, **pytest**. |
| Network in tests? | **No** in default suite. Use mocks, `httpx.MockTransport`, or files under `fixtures/`. Live calls only in `tests/integration/` behind env flags. |
| New CLI surface? | Implement in `cli.py`, document in **README** command tables and/or `docs/workflows/`, add **smoke or unit test** where feasible. Do not rename existing commands casually. |
| Browser automation? | **Default / CI:** **`MockBrowserRunner`** and **`FileBrowserRunner`** + `BrowserEvidence` JSON—no browser binary. **Optional live:** **`PlaywrightBrowserRunner`** (`uv pip install -e '.[browser]'`, `uv run playwright install …`, `alwm browser run-playwright`); integration smoke is opt-in (`ALWM_PLAYWRIGHT_SMOKE=1`). **`MCPBrowserRunner`** is **partial:** fixtures and/or **local stdio MCP** (`alwm browser run-mcp`, `mcp` in **`dev`** extras, `ALWM_MCP_BROWSER_COMMAND`); **IDE-hosted/remote MCP** is not a v0.2.0 goal—see `docs/architecture/browser.md` and `docs/roadmap/v0.2.0.md`. |
| Docker/Compose change? | Run `just compose-help`. Document new profiles in `docs/workflows/local-dev.md` or `benchmarking.md`. |

---

## Multi-agent parallel work

Multiple agents may edit the repo concurrently. Follow **`docs/workflows/multi-agent-parallel.md`** for branch naming, **file ownership zones**, merge order, and **required handoff summaries**. Short version:

- **Branches:** one scope per branch; rebase/merge `main` often.
- **Hot files:** `cli.py`, `schemas/v1/`, `artifacts.py`, `prompts/registry.yaml`—serialize or split PRs to avoid thrash.
- **Merge order:** contracts → implementation → CLI → docs when changes depend on each other.
- **Handoff:** use the template in `docs/workflows/multi-agent-parallel.md` in PR bodies or agent notes.

---

## Anti-patterns

- **Claiming “complete” without evidence** — No matching tests/commands: use **partial**, **stub**, or **documented-only** per `docs/audits/capability-classification.md`.
- **Duplicating long prompt strings** in benchmark YAML when an equivalent **`prompt_ref`** exists or should exist in the registry—duplication drifts from `prompts/versions/*.txt` and breaks auditability.
- **Placeholder “TODO” behavior without tests**—either implement, stub with explicit `NotImplementedError` + doc, or do not merge.
- **Skipping `uv run just ci`** because “it’s only docs”—if docs claim a command, verify the command still runs or qualify the doc.
- **Broad refactors** mixed with a targeted fix—keep diffs reviewable.
- **Live integration tests** in the default `tests/` tree without `--ignore=tests/integration` compatibility—default `just test` must stay offline-safe.
- **Inventing vendor APIs**—use existing provider adapters; extend `BaseProvider` and config loading instead of hard-coding URLs in random modules.
- **Parallel agents editing the same command surface** without coordination—see Multi-agent parallel work.


---

## Campaign orchestration

Use campaign orchestration when a task requires coordinated execution across multiple benchmark suites, providers, scoring backends, execution modes, or browser configurations.

Prefer a campaign definition over ad hoc repeated CLI invocations when:
- the run set is intended to be reproducible
- the outputs should be compared longitudinally
- the experiment needs a shared manifest and summary
- multiple dimensions are being swept together

**Artifacts to keep consistent in docs:** campaign **`manifest.json`** (fingerprints + run index), **`campaign-summary.*`**, member **`benchmark_manifest`** trees under **`runs/`**, **six-axis** fingerprints at both campaign (`campaign_experiment_fingerprints`) and run (`comparison_fingerprints`) levels, and **longitudinal** globs on **`runs/*/manifest.json`**.

Campaign-related changes must update:
- schemas
- artifact registration
- CLI docs
- README
- wiki (`docs/wiki/campaign-orchestration.md`, index `docs/wiki/benchmark-campaigns.md`)
- workflow walkthrough (`docs/workflows/campaign-walkthrough.md`) when user-facing steps change
- tracking (`docs/tracking/campaign-orchestration.md`; legacy `docs/tracking/benchmark-campaign-orchestration.md` if still referenced)
- ADR (`docs/adr/0001-campaign-orchestration.md` and/or `docs/architecture/adr/0001-benchmark-campaign-orchestration.md`)
- CHANGELOG
- implementation log

---

## Verification and reporting expectations

**Canonical vs fallback vs optional live:** **`docs/workflows/verification.md`** (matrix aligned with **`justfile`**). **`just`** is recommended but not strictly required if you run the equivalent **`uv run`** commands listed there.

| Layer | Minimum bar |
| --- | --- |
| **Python (default CI parity)** | **`uv run just ci`** (or **`just ci`** with an activated uv‑managed **`.venv`**) = **ruff** + **mypy** + **`uv run pytest tests/ --ignore=tests/integration`**. **Without `just`:** same three steps explicitly — see **`docs/workflows/verification.md`**. |
| **Committed JSON contracts** | **`uv run just validate-artifacts`** — **only** **`tests/test_schema_drift_contracts.py`** (fast sweep of **`examples/`** + **`fixtures/`** vs JSON Schema + Pydantic). **Fallback:** **`uv run pytest tests/test_schema_drift_contracts.py -v`**. That module also runs as part of the **full** default pytest invocation; **`validate-artifacts`** does **not** replace **`just ci`**. Inventory: **`docs/audits/schema-drift-contracts-inventory.md`**. |
| **Full-stack smoke** | Optional pre-release: `just smoke` (`scripts/smoke.sh`) — pytest `-m smoke`, host `alwm` benchmark + campaign, Docker Compose + offline benchmark; failure recovery analysis on errors. `SMOKE_SKIP_DOCKER=1` if Docker unavailable. See `docs/workflows/smoke.md`. |
| **CLI** | Smoke the commands you changed (`alwm … --help`, one happy path). |
| **Benchmarks** | Offline: `alwm benchmark run --definition fixtures/benchmarks/…` or `benchmarks/v1/offline`-style defs; outputs under `--output-dir` validate as artifacts (`benchmark_manifest` for `manifest.json`, per-cell kinds as today). |
| **Campaigns (offline)** | `uv run alwm benchmark campaign run` or `plan` (or `run --dry-run`) to a temp dir; validate **`campaign_manifest`** / **`campaign_summary`**; **`campaign_semantic_summary`** when the run emits it (deterministic-only campaigns may still produce the file with zero semantic cells). **`alwm benchmark campaign pack`** builds a **`campaign_result_pack`** + **`INDEX.md`** for publishing; **`alwm benchmark campaign compare-packs`** emits **`pack-compare.json`** / **`pack-compare-report.md`** (kind **`campaign_result_pack_comparison`**); **`alwm benchmark campaign compare`** emits **`campaign-compare.json`** / **`campaign-compare-report.md`** (kind **`campaign_compare`**) for two finished campaign directories. **Full publication checklist:** **`docs/workflows/campaign-result-pack-publication.md`**. Field reference: **`docs/workflows/benchmark-campaigns.md`**. |
| **Live backends** | Optional: `just ollama-gptoss-setup` (Compose Ollama + **gpt-oss:20b** + probe), `just smoke-ollama-live` (minimal benchmark); `alwm benchmark probe`; `just test-integration` with `ALWM_LIVE_BENCHMARK_OLLAMA` / `ALWM_LIVE_BENCHMARK_LLAMACPP`—never required for merge by default. See `docs/workflows/benchmarking.md`. |
| **Browser (offline)** | `alwm validate … browser_evidence`; `alwm browser prompt-block` / `run-mock` / `run-mcp` on fixtures—no browser binary. |
| **Browser (Playwright)** | Optional extra `[browser]`; not part of default `just ci`. |

**Reporting to humans:** In PRs or follow-up notes, state: scope, commands run, and known gaps (e.g. “integration not run—no local Ollama”).

---

## Documentation update rules

| Change type | Update |
| --- | --- |
| New/changed CLI subcommand or flag | `README.md` command table and/or `docs/workflows/*.md` |
| Local Python setup / install commands | `README.md`, **Python environment (uv — required on the host)** in this file, and `docs/workflows/local-dev.md` — always **`uv`** (`uv venv`, `uv pip`, `uv run`), not `python -m venv` or bare `pip` |
| New schema or artifact kind | `docs/architecture/data-model.md` (if entities change), `docs/implementation-log.md` |
| New Compose profile or recipe | `docs/workflows/local-dev.md` or `benchmarking.md`, `justfile` comment if needed |
| Behavioral milestone | **`README.md`** + **Releases and milestones** (this file), `docs/roadmap/`, `docs/tracking/`, `docs/releases/` as applicable; `docs/architecture/current-state.md`, `docs/implementation-log.md`; MkDocs nav (`mkdocs.yml`) when adding top-level doc areas |
| Audit or gap analysis | `docs/audits/`; log pointer in `docs/implementation-log.md` |
| Capability labels (complete / partial / stub / …) | `docs/audits/capability-classification.md` — keep README/AGENTS aligned |

**Do not** add large unrelated README rewrites when a pointer to `docs/…` suffices.

---

## Completion vs partial vs stubbed (and more)

Canonical definitions: **`docs/audits/capability-classification.md`** (includes **documented-only** and **broken**).

Short form for PRs:

| State | Meaning in this repo |
| --- | --- |
| **Complete** | Contract + default tests + docs/commands agree; see audit doc for evidence bar. |
| **Partial** | Ships safely; optional deps or gaps are explicit (e.g. Playwright behind `[browser]`). |
| **Stub** | Intentional `NotImplementedError` or reserved API—must not be described as production-ready elsewhere (see `capability-classification.md` for examples). |
| **Documented-only** | Docs without code, or scaffolding only—fix or downgrade claims. |

**Rule:** If behavior looks “real” but is not (e.g. random HTTP without adapter), downgrade to stub or complete the adapter + tests.

---

## Parallel agent workflow

When multiple agents are working simultaneously:

- assign each agent a distinct branch and primary file territory
- minimize edits to shared top-level docs
- append to `docs/implementation-log.md`; do not rewrite prior entries
- report changed files, commands run, and verification results
- recommend merge order based on dependency structure
- rebase or merge main before final handoff if another agent landed shared-file changes

Suggested roles:
- Runtime Hardening Agent
- Benchmark Expansion Agent
- Governance and Agent-Ops Agent


---

## Prompt registry (required reading)

The **prompt registry** (`prompts/registry.yaml` + `prompts/versions/*.txt`, schema `schemas/v1/prompt_registry.schema.json`) is the canonical place for **versioned, reusable** prompt text.

- **Benchmark definitions** (`BenchmarkDefinitionV1`): each `PromptItem` must use **`text`** *or* **`prompt_ref`** (not both). When adding or editing benchmarks that will be shared, compared, or run more than once, **prefer `prompt_ref`** and register the id in `prompts/registry.yaml`. Inline `text:` is for minimal fixtures or transitional defs—if you duplicate a registry prompt inline, you create drift risk.
- **Resolution** — `benchmark/prompt_resolution.py` + `prompt_registry_ref` / CLI `--prompt-registry` resolve paths relative to the repo; see `docs/implementation-log.md` entries on “Registry-backed benchmark prompts”.
- **Verification** — `alwm prompts check`, `alwm prompts list`, `alwm prompts show <id>`.

---

## Project-specific examples (good behavior)

### Implementation

- Add a new evaluation artifact field: extend `schemas/v1/evaluation.schema.json`, Pydantic `Evaluation`, `artifacts.py` mapping, `fixtures/v1/` sample, `tests/test_domain.py` or equivalent, then `docs/implementation-log.md`.

### Auditing

- Compare `docs/architecture/current-state.md` to code: e.g. if README claims `alwm compare` supports N eval files, grep `cli.py` and run `alwm compare --help`. File gaps in `docs/audits/` or implementation log. Use **`docs/audits/capability-classification.md`** when labeling features.

### Drift repair

- Benchmark defs still use inline `text:` for a prompt that now exists as `bench.sample.prompt.v1`: convert to `prompt_ref: bench.sample.prompt.v1`, ensure `benchmark_definition` schema validates, run `tests/test_benchmark_prompt_registry.py` and offline `alwm benchmark run`.

### Benchmark addition

- Add `benchmarks/v1/<id>.yaml` with `schema_version`, `rubric_ref`, `prompts` (prefer **`prompt_ref`** + registry), `variants` with explicit `backend`. Add mirror under `fixtures/benchmarks/` if needed for tests. Document in `benchmarks/v1/README.md` if present. Run offline benchmark to `tmp/` or `out/` and validate key outputs.

### Browser-related work

- Extend **`BrowserEvidence`** only with schema + tests + fixture. Deterministic runners: **`MockBrowserRunner`**, **`FileBrowserRunner`**. Optional live: **`PlaywrightBrowserRunner`** (`[browser]` extra, not default CI). **`MCPBrowserRunner`**: fixtures + optional **stdio MCP** client (`browser/mcp_stdio.py`); not **complete** for arbitrary IDE MCP servers—see `docs/architecture/browser.md`.

---

## Layout (quick reference)

| Path | Purpose |
| --- | --- |
| `docs/` | Architecture, workflows, implementation log, audits |
| `docs/audits/` | Capability taxonomy, mission/gap audits |
| `docs/workflows/` | How-to including **verification.md** (canonical / fallback / live checks), **multi-agent-parallel.md**, **docs-site.md** (MkDocs handbook: serve/build, **nav**, findings) |
| `docs/examples/` | Pointer doc for repo-root **`examples/`** |
| `docs/wiki/` | Short topic indexes (e.g. **`benchmark-campaigns.md`**, **`campaign-orchestration.md`**) |
| `docs/tracking/` | Contract and milestone tracking (**`campaign-orchestration.md`**, **`v0.2.4-campaign.md`**, etc.) |
| `schemas/` | JSON Schema (`schemas/v1/`) |
| `templates/` | Markdown report templates |
| `prompts/` | Versioned prompts + `registry.yaml` |
| `examples/` | Example artifacts and datasets (validated in tests) |
| `fixtures/` | Deterministic test inputs |
| `benchmarks/v1/`, `fixtures/benchmarks/` | Benchmark definitions |
| `src/agent_llm_wiki_matrix/` | Python package (`alwm` CLI) |
| `tests/` | Default pytest (offline) |
| `tests/integration/` | Opt-in live provider / Playwright smoke tests |
| `justfile` | [just](https://github.com/casey/just) recipes |

## Commands (quick reference)

- Install: see **Python environment (uv — required on the host)** — e.g. `uv pip install -e ".[dev]"` (Python 3.11+; matches `Dockerfile`). Optional Playwright: `uv pip install -e ".[browser]"` then `uv run playwright install chromium` (not required for `just ci`).
- CI parity: **`uv run just ci`** (ruff, mypy, pytest; excludes **`tests/integration/`**). Fallback **`uv run`** commands: **`docs/workflows/verification.md`**. Focused artifact contracts: **`uv run just validate-artifacts`** (does not replace full CI). Documentation site (opt-in): **`just docs`** / **`just docs-build`** after **`uv pip install -e ".[docs]"`** — **`docs/workflows/docs-site.md`**.
- CLI: `uv run alwm …` (or `alwm` after `source .venv/bin/activate`) — see `alwm --help`; registry **`alwm prompts …`**; pipelines **`ingest`**, **`evaluate`**, **`compare`**, **`report`**; benchmarks **`alwm benchmark run`**, **`probe`**, **`longitudinal`**, **`campaign run`** (optional **`--dry-run`**), **`campaign plan`**; providers **`alwm providers show`**; browser **`alwm browser prompt-block`**, **`run-mock`**, **`run-mcp`** (fixtures and/or **local stdio** MCP client—**remote / IDE-hosted MCP** not implemented), **`run-playwright`** (requires **`[browser]`** + browsers). Campaign / observability / semantic summaries: **`docs/workflows/benchmark-campaigns.md`**, **`docs/workflows/benchmarking.md`** (do not imply remote MCP or live browser is “complete” without the evidence in **`docs/audits/capability-classification.md`**).
- Images: `just docker-build` / `just docker-bake` (host **`just`** is separate from **`uv`**; recipes call **`uv run`** internally).

## Commits

Use complete-sentence messages describing *what* changed and *why*. Keep diffs focused; avoid drive-by refactors.
