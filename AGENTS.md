# AGENTS.md — Operating manual for coding agents

This repository is **agent-llm-wiki-matrix**: a markdown-first, git-native system for LLM wiki content, comparison matrices, benchmarks, providers (mock / Ollama / OpenAI-compatible), and browser evidence abstractions. Use this document to decide *what to do*, *how to know you are done*, and *what to avoid*.

---

## Mission and success criteria

**Mission:** Evolve and maintain a **reproducible**, **docs-first** toolkit where structured artifacts (schemas, fixtures, benchmarks, reports) live in git; orchestration is testable Python; runtime is Docker/Compose/Bake; and live backends are optional, explicit, and probe-tested.

**Success looks like:**

| Criterion | Signal |
| --- | --- |
| **Contracts are real** | JSON Schema + Pydantic (or documented exceptions) for user-facing payloads; `alwm validate` kinds stay in sync with `artifacts.py`. |
| **Default CI is offline** | `just ci` passes without Ollama, llama.cpp, or Playwright browsers; integration/live tests are opt-in (`tests/integration/`, env gates such as `ALWM_PLAYWRIGHT_SMOKE`, `ALWM_LIVE_BENCHMARK_*`). |
| **No silent drift** | Benchmarks, prompts, and CLI outputs that matter are covered by tests or documented as intentionally manual. |
| **Operations are discoverable** | `README.md`, `docs/workflows/`, `docs/architecture/`, and this file tell a contributor how to run, verify, and extend the system. |
| **Claims match evidence** | Features are labeled with the taxonomy in `docs/audits/capability-classification.md`; **complete** is not used without tests/commands to back it. |

---

## Principles (unchanged)

- **Markdown-first, git-native**: prefer committed artifacts over undocumented local state.
- **Determinism**: tests and default pipelines must not depend on live network unless explicitly marked (`@pytest.mark.integration`, `ALWM_LIVE_BENCHMARK_*`, etc.).
- **Typed contracts**: JSON Schema for structured data; YAML for human-edited config where appropriate.
- **Adapters, not fake integrations**: use interfaces and mocks until a real provider or browser stack is wired **and** tested or explicitly stubbed with `NotImplementedError` and docs.
- **Docker-first runtime**: `Dockerfile`, `docker-compose.yml`, and `docker-bake.hcl` are the source of truth for reproducible images and Compose profiles.

---

## Required contribution loop

For any non-trivial change (feature, fix, refactor that touches behavior or contracts):

1. **Locate** — Identify the owning area: `benchmark/`, `pipelines/`, `providers/`, `browser/`, `schemas/`, `prompts/`, `docs/`.
2. **Contract** — If you add or change structured data, update **JSON Schema** and **Pydantic** (and `alwm validate` registration in `artifacts.py` when applicable).
3. **Verify** — Run `just ci`. If you touch benchmarks or providers, consider `alwm benchmark probe` or (opt-in) `just test-integration`. Optional Playwright: `ALWM_PLAYWRIGHT_SMOKE=1` + `tests/integration/` (requires `pip install '.[browser]'` and `playwright install chromium`).
4. **Document** — Append a dated entry to `docs/implementation-log.md`. If architecture or workflows change, update the relevant file under `docs/architecture/` or `docs/workflows/` (do not let docs rot).
5. **Report** — Commit message: full sentences, *what* + *why*; PR/description should list verification performed (`just ci`, manual command, etc.).

**Phased work:** If the change fits a named phase in `docs/implementation-log.md`, note completion there and adjust `docs/architecture/current-state.md` when behavior materially changes.

---

## Decision rules

| Question | Default answer |
| --- | --- |
| Inline prompt text vs registry? | Prefer **`prompt_ref`** (+ file under `prompts/versions/`) and an entry in `prompts/registry.yaml` when the prompt is reused, versioned, or part of a benchmark suite. Use **inline `text`** only for one-off scratch definitions, transient experiments, or docs examples—then say so in the PR/note. See **Prompt registry** below. |
| New structured artifact type? | Add **JSON Schema** under `schemas/v1/`, model in `models.py` or the owning package, register in **`artifacts.py`**, add **fixture + example**, **pytest**. |
| Network in tests? | **No** in default suite. Use mocks, `httpx.MockTransport`, or files under `fixtures/`. Live calls only in `tests/integration/` behind env flags. |
| New CLI surface? | Implement in `cli.py`, document in **README** command tables and/or `docs/workflows/`, add **smoke or unit test** where feasible. Do not rename existing commands casually. |
| Browser automation? | **Default / CI:** **`MockBrowserRunner`** and **`FileBrowserRunner`** + `BrowserEvidence` JSON—no browser binary. **Optional live:** **`PlaywrightBrowserRunner`** (`pip install '.[browser]'`, `playwright install …`, `alwm browser run-playwright`); integration smoke is opt-in (`ALWM_PLAYWRIGHT_SMOKE=1`). **`MCPBrowserRunner`** remains a **stub** (`NotImplementedError`) until implemented with tests and docs—no silent half-wiring. |
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
- **Skipping `just ci`** because “it’s only docs”—if docs claim a command, verify the command still runs or qualify the doc.
- **Broad refactors** mixed with a targeted fix—keep diffs reviewable.
- **Live integration tests** in the default `tests/` tree without `--ignore=tests/integration` compatibility—default `just test` must stay offline-safe.
- **Inventing vendor APIs**—use existing provider adapters; extend `BaseProvider` and config loading instead of hard-coding URLs in random modules.
- **Parallel agents editing the same command surface** without coordination—see Multi-agent parallel work.

---

## Verification and reporting expectations

| Layer | Minimum bar |
| --- | --- |
| **Python** | `just ci` = ruff + mypy + pytest (`tests/` excluding `tests/integration/`). |
| **CLI** | Smoke the commands you changed (`alwm … --help`, one happy path). |
| **Benchmarks** | Offline: `alwm benchmark run --definition fixtures/benchmarks/…` or `benchmarks/v1/offline`-style defs; outputs under `--output-dir` validate as artifacts (`benchmark_manifest` for `manifest.json`, per-cell kinds as today). |
| **Live backends** | Optional: `alwm benchmark probe`; `just test-integration` with `ALWM_LIVE_BENCHMARK_OLLAMA` / `ALWM_LIVE_BENCHMARK_LLAMACPP`—never required for merge by default. |
| **Browser (offline)** | `alwm validate … browser_evidence`; `alwm browser prompt-block` / `run-mock` on fixtures—no browser binary. |
| **Browser (Playwright)** | Optional extra `[browser]`; not part of default `just ci`. |

**Reporting to humans:** In PRs or follow-up notes, state: scope, commands run, and known gaps (e.g. “integration not run—no local Ollama”).

---

## Documentation update rules

| Change type | Update |
| --- | --- |
| New/changed CLI subcommand or flag | `README.md` command table and/or `docs/workflows/*.md` |
| New schema or artifact kind | `docs/architecture/data-model.md` (if entities change), `docs/implementation-log.md` |
| New Compose profile or recipe | `docs/workflows/local-dev.md` or `benchmarking.md`, `justfile` comment if needed |
| Behavioral milestone | `docs/architecture/current-state.md`, `docs/implementation-log.md` |
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
| **Stub** | Intentional `NotImplementedError` or reserved API—**MCP browser runner** today. |
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

- Extend **`BrowserEvidence`** only with schema + tests + fixture. Deterministic runners: **`MockBrowserRunner`**, **`FileBrowserRunner`**. Optional live: **`PlaywrightBrowserRunner`** (`[browser]` extra, not default CI). New third-party runner: subclass `BrowserRunner`, document in `docs/architecture/browser.md`, add tests; **MCP** remains stubbed until explicitly implemented.

---

## Layout (quick reference)

| Path | Purpose |
| --- | --- |
| `docs/` | Architecture, workflows, implementation log, audits |
| `docs/audits/` | Capability taxonomy, mission/gap audits |
| `docs/workflows/` | How-to including **multi-agent-parallel.md** |
| `docs/examples/` | Pointer doc for repo-root **`examples/`** |
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

- Install: `pip install -e ".[dev]"` (Python 3.11+ recommended; matches `Dockerfile`). Optional Playwright: `pip install -e ".[browser]"` then `playwright install chromium` (not required for `just ci`).
- CI parity: `just ci` (ruff, mypy, pytest; excludes `tests/integration/`).
- CLI: `alwm` — see `alwm --help`; registry `alwm prompts …`; benchmarks `alwm benchmark run|probe`; providers `alwm providers show`; browser `alwm browser prompt-block`, `run-mock`, `run-playwright` (requires `[browser]` + browsers).
- Images: `just docker-build` / `just docker-bake`.

## Commits

Use complete-sentence messages describing *what* changed and *why*. Keep diffs focused; avoid drive-by refactors.
