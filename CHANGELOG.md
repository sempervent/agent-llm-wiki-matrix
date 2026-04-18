# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Campaign result pack comparison** — `CampaignResultPackComparisonV1` + `schemas/v1/campaign_result_pack_comparison.schema.json`; `alwm benchmark campaign compare-packs` writes `pack-compare.json` and `pack-compare-report.md` (fingerprints, artifact paths, `campaign-analysis.json` deltas, FT-\*, semantic totals, member runs, portability). Optional `--repo-root` for git-friendly relative paths. Example: `examples/campaign_result_packs/compare_minimal_vs_multi/`. Kind `campaign_result_pack_comparison` in `artifacts.py`.

- **Campaign result packs** — `CampaignResultPackV1` + `schemas/v1/campaign_result_pack.schema.json`; `alwm benchmark campaign pack` assembles a git-friendly directory (`campaign-result-pack.json`, `INDEX.md`, mirrored campaign layout). Example: `examples/campaign_result_packs/minimal_offline/`. Kind `campaign_result_pack` registered in `artifacts.py`.

- **MCP stdio (protocol) path** — `MCPBrowserRunner` uses the `mcp` client for a **local** stdio server when `ALWM_MCP_BROWSER_COMMAND` is set and no fixture ids are passed; `alwm browser run-mcp --stdio`; fixture server `fixtures/mcp_servers/stdio_browser_evidence_server.py`. `mcp>=1.27` is in **`dev`** optional extras. **Not** a v0.2.0 exit criterion for IDE-hosted MCP (`docs/roadmap/v0.2.0.md`).

### Changed

- **Campaign semantic / hybrid judge reporting** — **`campaign-semantic-summary.json`** adds **`criterion_instability`**, **`instability_highlights`** (unstable suites / providers / modes + **confidence_flag_counts**), split **`judge_low_confidence`** vs repeat **confidence** counts; **`campaign-semantic-summary.md`** surfaces these first; **`reports/campaign-report.md`** and **`campaign-analysis.json`** (**`judge_campaign_semantic`**) include the same signals. **Semantic summary** is written **before** the comparative report so **judge** sections can embed. **No change** to default deterministic scoring.

- **Campaign reporting (readability)** — **`campaign-summary.md`** includes **At a glance** (mean-score spreads by sweep axis, backend means, semantic instability counts, execution-mode gaps, top **FT-\*** tags, semantic judge rollup hints). **`reports/campaign-report.md`** leads with the same digest plus member mean-score tables and fingerprint-axis sections. **`campaign-semantic-summary.md`** adds ranked **Instability hotspots** before detailed rollups. **`campaign-analysis.json`** includes **`mean_score_extremes_by_sweep_axis`** and member mean blocks. New committed example **`examples/campaign_runs/multi_suite/`** (two suites). **No change** to default rubric scoring or harness math.

- **Browser evidence (fixtures)** — **`DomExcerpt`** adds optional **`aria_role`**, **`accessibility_name`**, **`dom_order`**; **`ScreenshotMetadata`** adds **`capture_scope`**, **`target_selector`**, **`sequence`**, **`device_pixel_ratio`**. JSON Schema documents optional **`extensions.network`**, **`extensions.accessibility`**, **`extensions.performance`**. **`evidence_to_prompt_block`** renders structured extensions readably; benchmark **`reports/report.md`** appends **Browser evidence (fixture summary)** for **`browser_mock`** runs. New fixtures **`checkout_flow.json`**, **`form_validation.json`**; suites **`suite.taxonomy.browser_checkout.v1`**, **`suite.taxonomy.browser_form.v1`**, **`suite.agentic.browser_checkout.v1`**; benchmarks **`browser_checkout.v1`**, **`browser_form.v1`**. Prompt registry **0.4.2**.

## [0.2.1] — 2026-04-18

**Comparative campaigns and longitudinal evaluation:** this release strengthens campaign workflows, reporting, observability, and browser-evidence realism while keeping **default CI deterministic and offline** and preserving **opt-in live verification** paths.

### Highlights

- **Campaign documentation** — Consolidation and walkthrough improvements (see [docs/workflows/campaign-walkthrough.md](docs/workflows/campaign-walkthrough.md), [docs/wiki/benchmark-campaigns.md](docs/wiki/benchmark-campaigns.md), [docs/tracking/benchmark-campaign-orchestration.md](docs/tracking/benchmark-campaign-orchestration.md), ADR [docs/architecture/adr/0001-benchmark-campaign-orchestration.md](docs/architecture/adr/0001-benchmark-campaign-orchestration.md)).
- **MCP browser runner** — Truthful **partial** classification: fixture-backed bridge and **`alwm browser run-mcp`** (`--scenario-id` / `--fixture`); remote MCP protocol execution remains **out of scope** until implemented and tested ([docs/architecture/browser.md](docs/architecture/browser.md)).
- **Campaign semantic summary** — **`campaign_semantic_summary`** artifacts and reporting for judge-repeat / semantic rollups on campaign outputs ([docs/workflows/benchmark-campaigns.md](docs/workflows/benchmark-campaigns.md)).
- **Runtime observability** — Benchmark **`manifest.json`** and campaign manifests gain timing / retry / judge-phase summaries where applicable; Markdown reports surface aggregates ([docs/workflows/benchmarking.md](docs/workflows/benchmarking.md)).
- **Browser evidence** — Richer fixture-backed **`BrowserEvidence`**: **`dom_excerpts`**, **`screenshots`** (metadata), **`extensions`**; **`browser_realism.v1`** rubric (**grounding**, **hallucination_resistance**, **source_fidelity**); prompt registry **0.4.1** ([docs/architecture/browser.md](docs/architecture/browser.md)).

### Other

- **Ollama (gpt-oss:20b)** — `just ollama-gptoss-setup` / **`smoke-ollama-live`** helpers; defaults and volume migration notes for **`./.ollama-models`**.

### Known boundaries

- **MCP** remains **fixture-backed / partial**, not a full remote protocol implementation.
- **Playwright** remains **optional**; not part of default **`just ci`**.
- **Browser realism** is improved but still **bounded by deterministic fixture mode** in default pipelines.

Narrative notes: [docs/releases/v0.2.1.md](docs/releases/v0.2.1.md).

## [0.2.0] — 2026-04-18

### Added

- **Campaign orchestration (CLI)** — `alwm benchmark campaign run` with **`--dry-run`** (writes top-level `manifest.json`, `campaign-summary.*`, `campaign-dry-run.json` without member **`runs/`** when planning). Artifact kinds **`campaign_definition`**, **`campaign_manifest`**, **`campaign_summary`** (aliases **`benchmark_campaign_*`**); **`run_benchmark`** for each member run.
- **Benchmark `comparison_fingerprints` (six axes)** — `manifest.json` includes **`prompt_registry_state`**: hash of the effective prompt registry YAML when `prompt_ref` prompts are used, or an inline-only sentinel when all prompts are inline.
- **Campaign `campaign_experiment_fingerprints` (six axes)** — `campaign_definition`, **`suite_definitions`**, **`provider_configs`**, **`scoring_configs`**, **`browser_configs`**, and **`prompt_registry_state`** on campaign **`manifest.json`** and **`campaign-summary.json`** for longitudinal grouping and audits.
- **Longitudinal reporting** — `group_snapshots_by` key **`prompt_registry_state_fingerprint`**; **`provider-comparison.md`** includes a **Registry** column alongside the other fingerprint columns.

### Changed

- **`campaign_definition_fingerprint`** — canonical identity hash (cosmetic fields excluded; stable list ordering); aligns with the **`campaign_definition`** field inside **`campaign_experiment_fingerprints`**.

### Documentation

- **Campaign** — Consolidated README, AGENTS, workflows, wiki, and audits around **campaign manifests**, **campaign summaries**, **six-axis** fingerprints at campaign (`campaign_experiment_fingerprints`) and run (`comparison_fingerprints`) levels, and **longitudinal** globs on **`runs/*/manifest.json`**. Added **[docs/workflows/campaign-walkthrough.md](docs/workflows/campaign-walkthrough.md)** (committed-example steps: validate `examples/campaign_runs/minimal_offline/`, inspect fingerprints, optional `alwm benchmark longitudinal`).

## [0.1.0] — 2026-04-17

First tagged release: offline-first CLI, pipelines, benchmark harness, prompt registry, JSON Schema artifacts, and Docker tooling. See [docs/releases/v0.1.0.md](docs/releases/v0.1.0.md) for narrative notes and [docs/release-readiness.md](docs/release-readiness.md) for capability scope.

### Added

- **`alwm` CLI** — `validate`, ingest / evaluate / compare / report, `prompts` (check / list / show), `benchmark` (run / probe), `browser` helpers, `providers show`.
- **Pipelines** — Markdown ingest → rubric evaluation → comparison matrix → report (deterministic, tested offline).
- **Benchmark harness** — Versioned YAML definitions; inline prompts and `prompt_ref` into `prompts/registry.yaml`; mock / Ollama / OpenAI-compatible backends; matrices and `manifest.json` as **`benchmark_manifest`** artifacts.
- **Prompt registry** — `prompts/registry.yaml` with versioned prompt files under `prompts/versions/`.
- **Schemas** — JSON Schema under `schemas/v1/` for artifacts, rubrics, benchmark I/O, and run manifests.
- **Docker** — `Dockerfile` (`python:3.11-slim`), Compose profiles for dev/test/benchmark and optional live probes, `docker-bake.hcl` for multi-arch **`linux/amd64`** and **`linux/arm64`** (`orchestrator` target).
- **Quality** — `just ci` (ruff, mypy, pytest excluding `tests/integration/`); opt-in integration tests for live providers and Playwright.

### Documentation

- Architecture and workflow docs under `docs/`.
- Audits: mission gap, capability classification, current capability status, **release-readiness** ([docs/release-readiness.md](docs/release-readiness.md)), and [docs/audits/release-readiness-audit.md](docs/audits/release-readiness-audit.md) (command-backed evidence).

[0.1.0]: https://github.com/sempervent/agent-llm-wiki-matrix/releases/tag/v0.1.0
[0.2.0]: https://github.com/sempervent/agent-llm-wiki-matrix/releases/tag/v0.2.0
[0.2.1]: https://github.com/sempervent/agent-llm-wiki-matrix/releases/tag/v0.2.1
