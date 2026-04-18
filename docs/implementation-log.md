# Implementation log

Chronological record of repository work. Latest entries first.

## 2026-04-18 — Campaign comparative reporting (Markdown + JSON)

**Delivered:** **`benchmark/campaign_reporting.py`** — after a full campaign, load **succeeded** member manifests with **`load_run_snapshots`**, run **`analyze_longitudinal`** (fixed thresholds aligned with longitudinal CLI defaults), emit **`reports/campaign-report.md`** (dimensions varied, backend means, scoring instability, mode gaps, **FT-\*** ranking, **`render_failure_atlas`**) and **`reports/campaign-analysis.json`**. **`merge_generated_report_paths`** composes with semantic-summary paths. **`campaign-summary.md`** links comparative outputs. Docs **`docs/workflows/benchmark-campaigns.md`**, **`examples/campaigns/v1/README.md`**. Tests **`tests/test_campaign_reporting.py`**. Example **`examples/campaign_runs/minimal_offline/`** regenerated.

**Verification:** `uv run just ci`.

## 2026-04-17 — Browser evidence + rubric realism (fixtures; CI deterministic)

**Delivered:** **`BrowserEvidence`** gains **`dom_excerpts`**, **`screenshots`** (metadata), **`extensions`**; JSON Schema + **`DomExcerpt`** / **`ScreenshotMetadata`**. **`evidence_to_prompt_block`**, **`MockBrowserRunner`**, **`fixtures/browser_evidence/v1/export_flow.json`**. Rubric **`examples/dataset/rubrics/browser_realism.v1.json`** (grounding, hallucination_resistance, source_fidelity). Wired into **`suite.taxonomy.browser_evidence.v1`**, **`suite.agentic.browser_interpretation.v1`**, **`fixtures/benchmarks/browser_file.v1.yaml`**. **`prompts/registry.yaml` 0.4.1** and **`bench.task.browser_evidence.v1`**. Regenerated **`examples/benchmark_runs/agentic-pack-browser-interpretation/`**. Docs: **`docs/architecture/browser.md`**, **`data-model.md`**, **`benchmarking.md`**, **`examples/dataset/README.md`**.

**Verification:** `uv run ruff check src tests`; `uv run mypy src`; `uv run pytest tests/ --ignore=tests/integration`; `uv run alwm prompts check`.

## 2026-04-17 — Benchmark runtime observability (timing + retry/judge summaries)

**Delivered:** **`BenchmarkRunTimingSummaryV1`**, **`BenchmarkRetrySummaryV1`**, **`BenchmarkCellRuntimeV1`** on **`manifest.json`** (`runtime_summary`, `retry_summary`, **`cells[].runtime`**); **`CampaignAggregatedRuntimeV1`** on **`campaign_manifest`** (`aggregated_runtime`). **`runner.py`** records wall time for browser phase, provider completion, deterministic evaluation, and semantic judge phase (**`EvaluationPhaseMetrics`** + **`_run_semantic_with_repeats`** timing). **`reports/report.md`** and **`campaign-summary.md`** append Markdown tables (**`benchmark/observability.py`**). **`evaluate_with_scoring_backend`** returns **`(evaluation, provenance, metrics)`**. Schemas: **`manifest.schema.json`**, **`benchmark_campaign_manifest.schema.json`**. Tests: **`tests/test_benchmark_observability.py`**. Docs: **`docs/workflows/benchmarking.md`**.

**Verification:** `uv run pytest tests/ --ignore=tests/integration`; `uv run mypy src`.

## 2026-04-17 — Campaign semantic / hybrid scoring summary

**Delivered:** **`campaign_semantic_summary`** artifact kind + **`schemas/v1/campaign_semantic_summary.schema.json`**; **`benchmark/campaign_semantic_summary.py`** builds **`CampaignSemanticSummaryV1`** from succeeded member runs (repeat-judge disagreement, low-confidence flags, rollups by suite / provider / execution mode). **`run_benchmark_campaign`** writes **`campaign-semantic-summary.json`** / **`.md`** and merges paths into **`generated_report_paths`** (after comparative artifacts). **`campaign-summary.md`** links the semantic rollup when present. Example definition **`examples/campaigns/v1/semantic_repeats_offline.v1.yaml`**. Tests in **`tests/test_benchmark_campaign.py`**. Docs: **`docs/workflows/benchmark-campaigns.md`**, **`examples/campaigns/v1/README.md`**.

**Note:** Deterministic-only campaigns still emit a semantic summary with zero semantic cells; default scoring path is unchanged.

**Verification:** `uv run ruff check src tests` and `uv run pytest`.

## 2026-04-17 — MCP browser runner audit: CLI + doc alignment

**Context:** `MCPBrowserRunner` was already a **fixture-backed bridge** (delegates to `FileBrowserRunner` when `scenario_id` or `fixture_relpath` is set; `RuntimeError` without—remote MCP not wired). Several docs still claimed **`NotImplementedError`** / **stub**.

**Delivered:** **`alwm browser run-mcp`** (`cli.py`) with `--scenario-id` / `--fixture`; tests in **`tests/test_browser.py`**. **`docs/architecture/browser.md`** — accurate component table, **Remote MCP** section, **roadmap** list. Aligned **`AGENTS.md`**, **`README.md`**, **`docs/architecture/runtime.md`**, **`current-state.md`**, **`docs/audits/capability-classification.md`**, **`current-capability-status.md`**, **`mission-gap-audit.md`**, **`release-readiness.md`**; **`CHANGELOG.md` [Unreleased]**.

**Classification:** **`MCPBrowserRunner`** = **partial** (fixture path only); remote MCP protocol execution = **documented-only** until roadmap items ship.

**Verification:** `uv run just ci`.

## 2026-04-18 — v0.2.0 documentation consolidation (fingerprints + campaigns)

**Delivered:** **`CHANGELOG.md`** **[0.2.0]** entry (comparison + campaign experiment fingerprints, longitudinal updates) plus **Documentation** subsection (campaign walkthrough). **`docs/workflows/campaign-walkthrough.md`** — committed-example steps for **campaign manifest** vs **campaign summary** vs member **`benchmark_manifest`**, **six-axis** **`campaign_experiment_fingerprints`** vs **`comparison_fingerprints`**, and **longitudinal** globs. Audited **`README.md`**, **`AGENTS.md`**, **`docs/roadmap/v0.2.0.md`**, workflows (notably **`benchmarking.md`**, **`benchmark-campaigns.md`**, **`longitudinal-reporting.md`**), **`docs/architecture/data-model.md`**, **`docs/wiki/campaign-orchestration.md`**, **`docs/wiki/benchmark-campaigns.md`**, **`docs/tracking/campaign-orchestration.md`**, **`docs/tracking/benchmark-campaign-orchestration.md`**, **`docs/audits/capability-classification.md`**, ADRs **`docs/adr/0001-campaign-orchestration.md`** and **`docs/architecture/adr/0001-benchmark-campaign-orchestration.md`**, **`examples/campaigns/v1/README.md`** for consistent **six-axis** `comparison_fingerprints`, **`campaign_experiment_fingerprints`**, and **`prompt_registry_state_fingerprint`** wording. Removed duplicate milestone block from **`README.md`** (earlier pass).

**Verification:** documentation-only pass; `uv run alwm validate examples/campaign_runs/minimal_offline/manifest.json campaign_manifest` (paths cited in walkthrough).

## 2026-04-17 — v0.2.0 fingerprints: prompt registry state + campaign experiment axes

**Delivered:** **`BenchmarkComparisonFingerprints.prompt_registry_state`** — hash of effective registry YAML (or inline-only sentinel). **`CampaignExperimentFingerprints`** on **`BenchmarkCampaignManifest`** / **`CampaignSummaryV1`** (campaign definition, suite stack, provider files, scoring axis, browser axis, registry override). Canonical **`fingerprint_campaign_definition`** excludes cosmetic fields and sorts list fields. **`build_campaign_experiment_fingerprints`**, **`fingerprint_prompt_registry_effective_state`** in **`benchmark/fingerprints.py`**. Longitudinal **`group_snapshots_by`** key **`prompt_registry_state_fingerprint`**; **`render_provider_comparison_markdown`** registry column. Schemas: **`manifest.schema.json`**, **`benchmark_campaign_manifest.schema.json`**, **`campaign_summary.schema.json`**. Roadmap **`docs/roadmap/v0.2.0.md`**; **`README`** milestone blurb. Regenerated **`examples/campaign_runs/minimal_offline/`**, **`examples/reports/longitudinal/sample-output/`**, longitudinal fixtures.

**Verification:** `uv run just ci`.

## 2026-04-17 — Ollama gpt-oss:20b first-class workflow

**Delivered:** Default **`OLLAMA_MODEL`** / **`OllamaSection.model`** → **`gpt-oss:20b`**; **`benchmarks/v1/ollama.v1.yaml`**, **`config/providers.example.yaml`**, **`alwm benchmark probe`** default, integration test default aligned. **`scripts/ollama-gptoss-setup.sh`** (start Compose Ollama, pull, **`alwm benchmark probe`**), **`scripts/smoke-ollama-live.sh`** (minimal live benchmark + validate). **`just ollama-gptoss-setup`**, **`just smoke-ollama-live`**; **`verify-ollama-gptoss-smoke`** calls the live smoke script. Docs: **`docs/workflows/benchmarking.md`** (workflow + migration from named volume **`ollama_models`** → bind **`./.ollama-models`**), **`README.md`**, **`AGENTS.md`**, **`docs/workflows/live-verification.md`**, **`docs/workflows/local-dev.md`**, **`.env.example`**.

**Verification:** `uv run just ci` (deterministic); live path opt-in.

## 2026-04-17 — Campaign orchestration: dry-run, wiki, ADR, tracking

**Delivered:** **`alwm benchmark campaign run --dry-run`** (wraps `run_benchmark_campaign(..., dry_run=True)`; no separate `plan` command). Extended **campaign manifest** / **`CampaignSummaryV1`** + **`schemas/v1/campaign_summary.schema.json`**; artifact kinds **`campaign_definition`**, **`campaign_manifest`**, **`campaign_summary`**. **Docs:** **`docs/wiki/campaign-orchestration.md`**, **`docs/tracking/campaign-orchestration.md`**, **`docs/adr/0001-campaign-orchestration.md`**; updates to **`docs/workflows/benchmark-campaigns.md`**, **`docs/workflows/benchmarking.md`**, **`docs/architecture/evaluation-pipeline.md`**, **`README.md`**, **`CHANGELOG.md`**, **`docs/architecture/adr/0001-benchmark-campaign-orchestration.md`**, **`examples/campaigns/v1/README.md`**. Tests: **`tests/test_benchmark_campaign.py`** (dry-run writes `campaign-dry-run.json`, manifest, summary).

**Verification:** `uv run just ci`.

## 2026-04-17 — Benchmark comparison fingerprints (manifest + campaign)

**Delivered:** **`benchmark/fingerprints.py`** — SHA-256 over canonical JSON for **suite definition** (title excluded; sorted tags), **prompt set** (resolved prompt ids + text digests + registry provenance), **provider config** (per-variant sorted), **scoring config** (effective backend, eval_scoring, judge repeat, judge provider), **browser config** (per-variant sorted). **`BenchmarkComparisonFingerprints`** on **`BenchmarkRunManifest`** and **`BenchmarkCampaignRunEntry`**; **`schemas/v1/manifest.schema.json`**, **`schemas/v1/benchmark_campaign_manifest.schema.json`**. **`run_benchmark`** always emits fingerprints; **`campaign_runner`** copies them from member manifests. **`RunSnapshot.comparison_fingerprints`**, **`group_snapshots_by`** keys **`suite_definition_fingerprint`** … **`browser_config_fingerprint`**, **`provider-comparison.md`** + **`summary.json`** updates. Fixture **`fixtures/benchmarks/longitudinal.v1.yaml`**, longitudinal manifests updated. Tests **`tests/test_fingerprints.py`**, **`tests/test_longitudinal.py`**, **`tests/test_manifest.py`**, **`tests/test_benchmark_campaign.py`**. Docs: **`data-model.md`**, **`longitudinal-reporting.md`**, **`benchmarking.md`**, **`examples/reports/longitudinal/README.md`**.

**Note:** Extended in **v0.2.0** with **`prompt_registry_state`**, **`campaign_experiment_fingerprints`**, and **`prompt_registry_state_fingerprint`** (see log entries above).

**Verification:** `uv run pytest` (full suite).

## 2026-04-17 — Benchmark campaign sweeps

**Delivered:** **`BenchmarkCampaignDefinitionV1`** + **`schemas/v1/benchmark_campaign.schema.json`**; **`BenchmarkCampaignManifest`** / **`BenchmarkCampaignRunEntry`** + **`schemas/v1/benchmark_campaign_manifest.schema.json`**. **`benchmark/campaign_definitions.py`**, **`benchmark/campaign_runner.py`**. CLI **`alwm benchmark campaign run`**. Artifact kinds **`benchmark_campaign_definition`**, **`benchmark_campaign_manifest`**; **`write_benchmark_campaign_manifest`** in **`persistence.py`**. Fixture **`fixtures/benchmarks/campaign_micro.v1.yaml`**; examples **`examples/campaigns/v1/minimal_offline.v1.yaml`**, **`examples/campaign_runs/minimal_offline/`**. Docs **`docs/workflows/benchmark-campaigns.md`**, cross-link in **`docs/workflows/benchmarking.md`**, **`examples/campaigns/v1/README.md`**. Tests **`tests/test_benchmark_campaign.py`**.

**Verification:** `just ci`.

## 2026-04-17 — Agentic benchmark pack (cross-system evaluation)

**Delivered:** **`BenchmarkDefinitionV1` / `BenchmarkRunManifest`** optional **`success_criteria`** and **`failure_taxonomy_hints`** (metadata; JSON Schema + Pydantic + runner copy-through). **Prompt registry 0.4.0** — `bench.task.repo_implementation.v1`, `bench.task.docs_drift_repair.v1`, `bench.task.benchmark_authoring.v1`. Five suites under **`examples/benchmark_suites/v1/agentic/`** (repo implementation, docs drift, benchmark authoring, browser interpretation with file-backed evidence, multi-agent coordination). Committed offline runs **`examples/benchmark_runs/agentic-pack-*`**. Docs: **`docs/workflows/agentic-benchmark-pack.md`**, **`examples/benchmark_suites/v1/agentic/README.md`**, updates to **`benchmarking.md`**, **`benchmarks/v1/README.md`**, **`examples/benchmark_suites/v1/README.md`**, **`data-model.md`**. Tests: **`tests/test_agentic_benchmark_pack.py`**, manifest validation in **`tests/test_manifest.py`**.

**Verification:** `just ci` or `uv run just ci`.

## 2026-04-17 — uv canonical workflow (enforced in docs + `justfile`)

**Policy:** Host development **must** use **[uv](https://docs.astral.sh/uv/)** for virtualenv creation (`uv venv`), installs (`uv pip install …`), and running tools (`uv run …`). **`AGENTS.md`** states this explicitly; **`README.md`** and **`docs/workflows/local-dev.md`** / **`walkthrough-v0.1.0.md`** default to `uv run alwm` and `uv run just ci` without requiring `python -m venv` or bare `pip`. **`justfile`** recipes now use **`uv pip`** for `install` / `install-dev` and **`uv run`** for pytest, ruff, and mypy (no `python -m pip` fallback). **Runtime:** `src/.../cli.py` and **`playwright_runner.py`** user-facing messages updated to `uv pip`. Docker image builds unchanged (`Dockerfile` still uses pip inside the image).

**Verification:** `uv run just ci`.

## 2026-04-17 — Repeated semantic judge: aggregation, disagreement, low-confidence flags

**Delivered:** `pipelines/judge_repeat.py` — **mean**, **median**, **trimmed_mean** aggregation; per-criterion and total-weighted disagreement; threshold-based **`assess_low_confidence`**. `Evaluation` gains optional **`judge_repeat_count`**, **`judge_semantic_aggregation`**, **`judge_low_confidence`**; **`JudgeRepeatAggregation`** + nested models on **`EvaluationJudgeProvenance.repeat_aggregation`** (omitted when `judge_repeats` is 1). `evaluate_with_scoring_backend` accepts **`JudgeRepeatParams`**; mock semantic scores vary by **`run_index`** for stable multi-run tests. **`EvalScoringSpec`** + **`schemas/v1/benchmark_definition.schema.json`**: **`judge_repeats`**, **`semantic_aggregation`**, **`trim_fraction`**, optional stdev/range thresholds. **`alwm evaluate`** flags mirror repeat/aggregation/thresholds. Example: **`examples/benchmarks/v1/semantic_repeats.v1.yaml`**. Tests: **`tests/test_evaluation_backends.py`**, **`tests/test_benchmark.py`**. Docs: **`data-model.md`**, **`benchmarking.md`**, **`evaluation-pipeline.md`**, **`benchmarks/v1/README.md`**.

**Verification:** `uv run pytest` (full suite).

## 2026-04-17 — Longitudinal benchmark reporting

**Delivered:** `pipelines/longitudinal.py` — load runs from manifests + evaluations + optional grid and judge provenance; **weekly** and **longitudinal** Markdown; **failure taxonomy** (`FT-*`) and **failure atlas**; regression-focused **`regression.md`** and **`provider-comparison.md`**; optional **`run_context.json`** grouping via `group_snapshots_by`. CLI **`alwm benchmark longitudinal`** (`--runs-glob`, thresholds for regression, semantic instability, series swing). Lazy **`benchmark_run_context`** registration in **`artifacts.py`** to break an import cycle. **`schemas/v1/evaluation.schema.json`** — nullable semantic judge fields aligned with `Evaluation`. Fixtures **`fixtures/longitudinal/paired/`**; example bundle **`examples/reports/longitudinal/sample-output/`**; tests **`tests/test_longitudinal.py`**. Docs **`docs/workflows/longitudinal-reporting.md`**, **`examples/reports/longitudinal/README.md`**.

**Verification:** `just ci`.

## 2026-04-17 — Semantic and hybrid rubric scoring (optional)

**Delivered:** `pipelines/evaluation_backends.py` — backends **`deterministic`** (default), **`semantic_judge`**, **`hybrid`**; `EvaluationJudgeProvenance` model + **`schemas/v1/evaluation_judge_provenance.schema.json`**; artifact kind **`evaluation_judge_provenance`**. `Evaluation` gains **`scoring_backend`**, **`judge_provenance_relpath`**. `BenchmarkDefinitionV1.eval_scoring` (`EvalScoringSpec`, `EvalHybridWeights`); `load_judge_provider_config` in `providers/benchmark_config.py`. Benchmark cells write **`evaluation_judge_provenance.json`** when non-deterministic; manifest cells include optional **`judge_provenance_relpath`**. CLI: **`alwm evaluate`** (`--scoring-backend`, `--judge-provider-config`, `--judge-live`, `--hybrid-deterministic-weight`); **`alwm benchmark run`** (`--eval-scoring-backend`, `--judge-provider-config`). Opt-in live judge: **`ALWM_JUDGE_LIVE=1`**; fixture mode keeps mock judge unless set. Tests: **`tests/test_evaluation_backends.py`**. Docs: **`data-model.md`**, **`evaluation-pipeline.md`**, **`benchmarking.md`**. Fixtures: **`fixtures/v1/evaluation_judge_provenance.json`**.

**Verification:** `just ci`.

## 2026-04-17 — Browser-backed benchmark execution

**Why:** `browser_mock` previously only tagged LLM output; benchmarks did not exercise `BrowserRunner` or persist evidence.

**Delivered:** `BrowserBenchConfig` + optional `variant.browser` in `benchmark/definitions.py` and `schemas/v1/benchmark_definition.schema.json`. `run_benchmark` calls `run_benchmark_browser_phase` for `execution_mode: browser_mock`, writes **`cells/.../browser_evidence.json`**, augments the provider prompt, and records **`browser_runner`** / **`browser_evidence_relpath`** on request/response/manifest cells. **`MCPBrowserRunner`** (`browser/mcp_runner.py`): fixture-backed bridge; remote MCP tools not wired. Playwright gated by **`ALWM_BENCHMARK_PLAYWRIGHT=1`**. Fixtures under `fixtures/benchmarks/browser_*.v1.yaml`; example `examples/benchmarks/v1/browser_file.v1.yaml`. Tests: `tests/test_benchmark_browser.py`. Docs: `docs/workflows/benchmarking.md`, `benchmarks/v1/README.md`, `docs/architecture/browser.md`, `docs/audits/capability-classification.md`. **`evaluation.schema.json`:** optional `scoring_backend` / `judge_provenance_relpath` (not in `required`) for Pydantic alignment.

**Verification:** `just ci` (default tests; no Playwright in CI).

## 2026-04-17 — Benchmark corpus expansion: taxonomy metadata + eight tagged suites

**Delivered:** `BenchmarkTaxonomyV1`, optional `time_budget_seconds`, `token_budget`, `retry_policy`, `tags`, `expected_artifact_kinds` on `BenchmarkDefinitionV1`; same fields on `BenchmarkRunManifest` and `schemas/v1/manifest.schema.json` (optional). New prompts `bench.task.runtime_config.v1`, `bench.task.multi_agent_coord.v1`; registry **0.3.0**. Eight example suites under `examples/benchmark_suites/v1/suite.taxonomy.*.v1.yaml` covering repo, runtime, docs, browser evidence, matrix reasoning, multi-agent coordination, campaign sweep, and integration stress. Fixture `fixtures/benchmarks/suite_taxonomy_minimal.v1.yaml`; example runs `examples/benchmark_runs/taxonomy-repo-governance/`, `taxonomy-runtime-config/`. Tests: `tests/test_benchmark_taxonomy.py`, manifest validation. Docs: `docs/workflows/benchmarking.md`, `examples/benchmark_suites/v1/README.md`. `schemas/v1/benchmark_taxonomy.schema.json` for standalone taxonomy JSON.

## 2026-04-17 — v0.1.0 release preparation

**Delivered:** First semver release tag readiness: `CHANGELOG.md`, `docs/releases/v0.1.0.md`, `docs/release-readiness.md`, `docs/audits/release-readiness-audit.md`, `docs/workflows/walkthrough-v0.1.0.md`. README quickstarts (exact local, benchmark, prompt registry, manifest validate, optional live verification) and `pyproject.toml` `urls` + sdist `CHANGELOG.md` include. Version metadata remains **0.1.0** (`pyproject.toml`, `__version__`). Evidence: `just ci` (85 passed, 1 skipped), `just compose-help`, `docker buildx bake --print`.

## 2026-04-17 — Post-merge stabilization (parallel tracks)

**Delivered:** Single coherent tree on `main`: lazy `run_benchmark` in `benchmark/__init__.py` to avoid `artifacts` ↔ `pipelines` import cycles after manifest consolidation; audit docs refreshed (`mission-gap-audit.md`, **`current-capability-status.md`**) with **85 passed, 1 skipped** from `just ci`; staged governance and benchmark expansion artifacts (registry suites, example runs, `test_benchmark_expansion`).

## 2026-04-17 — Benchmark manifest: JSON Schema + `benchmark_manifest` artifact kind

**Delivered:** `schemas/v1/manifest.schema.json` (Draft 2020-12); `BenchmarkRunManifest` / `BenchmarkCellArtifactPaths` moved to **`models.py`** (re-exported from `benchmark/manifest.py`) to avoid import cycles with `artifacts.py`. Registered `benchmark_manifest` in `artifacts.py`; `write_benchmark_manifest` in `benchmark/persistence.py` validates against JSON Schema before writing; `run_benchmark` uses it. CLI: `alwm validate … benchmark_manifest`. Fixture `fixtures/v1/manifest.json`; tests `tests/test_manifest.py` + `test_domain` / `test_benchmark` hooks. Docs: `data-model.md`, `benchmarking.md`, `examples/v1/README.md`. Committed example runs under `examples/benchmark_runs/` unchanged (backward compatible: optional provenance keys omitted).

## 2026-04-17 — Benchmark expansion: registry suites, comparison rubric, manifest provenance

**Delivered:** Four versioned prompts under `prompts/versions/` (`bench.task.repo_governed.v1`, `markdown_synthesis`, `matrix_reasoning`, `browser_evidence`) registered in `prompts/registry.yaml` (**0.2.0**). New rubric `examples/dataset/rubrics/comparison.v1.json` (structure / task_fit / grounding / brevity). Three example suites: `suite.registry.four_modes.v1.yaml`, `suite.registry.strict_duo.v1.yaml`, `suite.registry.generous_duo.v1.yaml`; fixture mirror `fixtures/benchmarks/suite_four_modes.v1.yaml`. Committed offline runs under `examples/benchmark_runs/registry-four-modes`, `registry-strict-duo`, `registry-generous-duo`. `BenchmarkRunManifest` + `run_benchmark(..., definition_source_relpath=...)` + CLI wiring for optional manifest fields. Tests: `tests/test_benchmark_expansion.py`. Docs: `data-model.md`, `evaluation-pipeline.md`, `benchmarking.md`, `examples/benchmark_suites/v1/README.md`.

## 2026-04-17 — Runtime hardening: live verification paths

**Delivered:** `PlaywrightBrowserRunner` exported from `playwright_runner` (MCP-only stub file); `create_browser_runner(..., "playwright")`; Dockerfile target **`browser-test`** (Playwright + Chromium); Compose profile **`browser-verify`**; `docker-bake.hcl` target `browser-test` (linux/amd64); `just` recipes `verify-live-providers`, `verify-playwright-local`, `browser-verify`; `pytest` marker **`live_playwright`**; `tests/integration/test_playwright_browser.py` marked `integration` + `live_playwright`; **`docs/workflows/live-verification.md`**; `docs/architecture/runtime.md` refresh; workflow cross-links; `.env.example` notes `ALWM_PLAYWRIGHT_SMOKE`. Default **`just ci`** unchanged (`tests/integration/` still excluded).

## 2026-04-17 — Governance: AGENTS manual, multi-agent workflow, capability audit

**Why:** Reduce drift between docs and implementation; make parallel agent work predictable; require evidence-backed labels (“complete” vs partial/stub).

**What changed:**

- **`AGENTS.md`** — Stronger operating manual: non-goals folded into success criteria (evidence-backed claims), multi-agent rules (summary + pointer), expanded anti-patterns, verification table (Playwright opt-in), links to **`docs/audits/capability-classification.md`**, updated browser decision rule (Playwright optional; MCP stub), layout includes `docs/audits/`, `docs/examples/`, `docs/workflows/multi-agent-parallel.md`.
- **`docs/workflows/multi-agent-parallel.md`** — Branch strategy, file ownership zones, conflict avoidance, merge order, required handoff template.
- **`docs/audits/capability-classification.md`** — Taxonomy: complete / partial / stub / documented-only / broken + evidence bar and repository examples (re-verify after changes).
- **`docs/examples/README.md`** — Clarifies repo-root **`examples/`** vs `docs/examples/`.
- **Drift repair** — **`README.md`**: `alwm browser run-playwright`, optional `[browser]` install comment, pointer to multi-agent doc. **`docs/architecture/browser.md`**, **`current-state.md`**, **`runtime.md`**: Playwright optional; MCP stub; prompt registry **implemented** in current-state. **`docs/audits/mission-gap-audit.md`**: browser §3 and doc-drift rows updated; P3 reframed to MCP runner.

**Verification:** Documentation-only change set; command names cross-checked against `src/agent_llm_wiki_matrix/cli.py` (`browser run-playwright`, `benchmark probe`, `prompts` group).

## 2026-04-17 — AGENTS.md operating manual

**Why:** The old `AGENTS.md` was principles-only; agents needed actionable rules for this repo (benchmarks, prompt registry, integration tests, browser stubs, documentation touchpoints).

**What changed:** Expanded `AGENTS.md` with mission/success criteria, required contribution loop, decision table (including **prefer `prompt_ref` over duplicated inline prompt text** where appropriate), anti-patterns, verification/reporting table, documentation update rules, completion vs partial vs stubbed definitions, and project-specific examples (implementation, auditing, drift repair, benchmarks, browser). README now points contributors to `AGENTS.md` for the full manual.

**How to use it:** Before sizable work, read Mission, Contribution loop, and Prompt registry sections; after work, satisfy Verification + Documentation update rules and add an implementation-log entry when behavior or contracts shift.

## 2026-04-17 — Registry-backed benchmark prompts

**Delivered:** `PromptItem` supports `text` xor `prompt_ref` (+ optional `registry_version` pin); `BenchmarkDefinitionV1.prompt_registry_ref`; `resolve_benchmark_prompts` (`benchmark/prompt_resolution.py`) using `load_prompt_registry_yaml`; `run_benchmark(..., prompt_registry_path=...)` and CLI `--prompt-registry`; `BenchmarkRequestRecord` / `BenchmarkResponse` fields `prompt_source`, `prompt_registry_id`, `registry_document_version`, `prompt_source_relpath`; JSON Schema updates + `schemas/v1/benchmark_definition.schema.json`. Fixtures under `fixtures/prompt_registry/` and `fixtures/benchmarks/registry_*.yaml`; tests `tests/test_benchmark_prompt_registry.py`; example `examples/benchmark_suites/v1/registry.mixed.v1.yaml` + committed run `examples/benchmark_runs/registry-mixed/`. Prompt `bench.sample.prompt.v1` added under `prompts/`.

## 2026-04-17 — Live benchmark verification (Compose + opt-in integration tests)

**Delivered:** `benchmark/live_probe.py`; CLI `alwm benchmark probe`; Ollama healthcheck + `service_healthy` for `benchmark-ollama`; Compose profile **`benchmark-probe`** (`just benchmark-probe`); integration tests under `tests/integration/` gated by `ALWM_LIVE_BENCHMARK_OLLAMA` / `ALWM_LIVE_BENCHMARK_LLAMACPP` with skips when unreachable; `just test` ignores `tests/integration/`; `tests/test_live_probe.py` unit tests.

## 2026-04-17 — Mission gap audit + prompt registry CLI

**Delivered:** `docs/audits/mission-gap-audit.md` (code-verified status of CLI, providers, browser layer, Compose, Bake; drift notes). **Prompt registry wiring:** `schemas/v1/prompt_registry.schema.json`, `prompt_registry.py` (YAML load + JSON Schema + path safety), CLI `alwm prompts check|list|show`, tests `tests/test_prompt_registry.py`. README and `AGENTS.md` updated for new commands.

## 2026-04-17 — Browser execution abstraction

**Delivered:** `BrowserRunner` ABC; `BrowserEvidence` JSON Schema + Pydantic models; `MockBrowserRunner` and `FileBrowserRunner`; fixture `fixtures/browser_evidence/v1/export_flow.json`; `PlaywrightBrowserRunner` / `MCPBrowserRunner` stubs (`NotImplementedError`); `load_browser_evidence`, `evidence_to_prompt_block`; artifact kind `browser_evidence` for `alwm validate`; CLI `alwm browser prompt-block` and `alwm browser run-mock`; tests `tests/test_browser.py`; `docs/architecture/browser.md`.

**Not in scope:** live Playwright or MCP browser automation (stubs only).

## 2026-04-17 — Benchmark run artifact persistence

**Delivered:** Structured output under `cells/`, `matrices/`, `markdown/`, `reports/` with stable `cell_id` slugs, **benchmark_request** + raw/normalized response text files, aggregate **benchmark_response**, per-cell **evaluation**, **matrix_grid_inputs** / **matrix_pairwise_inputs**, and manifest **cells[]** index; execution layer returns raw vs normalized text.

## 2026-04-17 — Replace Makefile with justfile

**Delivered:** [just](https://github.com/casey/just) `justfile` with the same recipes as the former Makefile (`ci`, lint, compose-help, benchmark profiles, etc.); removed `Makefile`; documentation and `AGENTS.md` now reference `just …`.

## 2026-04-17 — Benchmark case schema (v1) + task examples

**Delivered:**

- JSON Schema `schemas/v1/benchmark_case.schema.json` and Pydantic `BenchmarkCase` / `BenchmarkExecutionMetadata` with validation that `expected_artifact_kinds` references registered `alwm validate` kinds.
- Loader `benchmark/cases.py` (`load_benchmark_case`, `validate_benchmark_case_file`).
- Catalog `benchmarks/cases/v1/` with four task kinds: repo scaffolding, Markdown synthesis, comparison matrix, browser-evidence interpretation; mirrored under `fixtures/benchmark_cases/v1/` and `examples/benchmark_cases/v1/`.
- Tests: `tests/test_benchmark_cases.py`.

## 2026-04-17 — Phase 5 complete (benchmark harness)

**Delivered:**

- **Provider execution:** `providers/execution.py` applies deterministic execution-mode tags (`cli`, `browser_mock`, `repo_governed`) on top of the same `CompletionRequest` for all backends.
- **Backend selection:** `providers/benchmark_config.py` merges global YAML/env with per-variant `mock` / `ollama` / `openai_compatible` settings; `ALWM_FIXTURE_MODE=1` forces mock unless `--no-fixture-mock`.
- **Benchmark definitions:** Pydantic `BenchmarkDefinitionV1` + `load_benchmark_definition` for YAML/JSON under `benchmarks/v1/` (mirrored in `fixtures/benchmarks/` for tests).
- **Artifacts:** `schemas/v1/benchmark_response.schema.json`, `BenchmarkResponse` model, `alwm validate … benchmark_response`.
- **Pipeline:** `benchmark/runner.py` stores raw responses, rubric-evaluates each cell, builds **grid** and **pairwise** `ComparisonMatrix` JSON + Markdown, `report.json` / `report.md`, and `manifest.json`.
- **CLI:** `alwm benchmark run --definition … --output-dir …`.
- **Compose / just:** profiles **`benchmark-offline`**, **`benchmark-ollama`** (+ `ollama` service), **`benchmark-llamacpp`**; recipes `just benchmark-offline`, `just benchmark-ollama`, `just benchmark-llamacpp`.
- **Tests:** `tests/test_benchmark.py` asserts deterministic offline matrix output and validates artifacts.

**Next:** Richer prompt registry wiring; optional LLM rubric; real browser trace ingestion.

## 2026-04-17 — Phase 4 complete (pipelines + Compose test image)

**Delivered:**

- **Rubric** JSON Schema (`schemas/v1/rubric.schema.json`) + Pydantic models; `alwm validate … rubric`.
- **Pipelines:** `ingest_markdown_pages`, deterministic `evaluate_subject`, `evaluations_to_matrix`, `build_report_from_matrix` + Markdown renderers for `templates/matrix.md` and `templates/report.md`.
- **CLI:** `alwm ingest`, `evaluate`, `compare` (optional `--out-md`), `report`.
- **Docker:** `Dockerfile` `test` stage (editable `.[dev]` + pytest); Compose services `orchestrator` (dev), `tests` (test), `benchmark` (benchmark); `just compose-help` validates all profiles.
- **Examples:** `examples/dataset/` wiki pages, evaluations, thoughts, and `examples/generated/` matrix + report pair; tests validate checked-in generated JSON.
- **Docs:** Updated `docs/workflows/*`, `docs/architecture/current-state.md`, `docs/architecture/evaluation-pipeline.md`, `docs/architecture/runtime.md`, and `README.md` with exact commands.

**Next:** Optional LLM-assisted scoring behind providers; richer ingest extraction; browser evidence fixtures.

## 2026-04-17 — Phase 3 complete (provider abstraction)

**Delivered:**

- `BaseProvider` + `CompletionRequest` contract.
- `MockProvider` (deterministic, no network).
- `OllamaProvider` (`/api/chat`) and `OpenAICompatibleProvider` (`/v1/chat/completions`) using `httpx` with injectable `MockTransport` for tests.
- `ProviderConfig` loaded from optional YAML + environment overrides (`load_provider_config`).
- Example YAML: `config/providers.example.yaml`; local `config/providers.yaml` gitignored.
- CLI: `alwm providers show` prints redacted configuration.
- Tests in `tests/test_providers.py` (mocked HTTP only).

**Next:** Phase 4 — ingest pipeline, claim extraction stubs, rubric evaluation, matrix persistence.

## 2026-04-17 — Phase 2 complete (domain models + schemas)

**Delivered:**

- JSON Schemas under `schemas/v1/` for `thought`, `event`, `experiment`, `evaluation`, `matrix`, `report` (plus existing `note`).
- Pydantic models in `src/agent_llm_wiki_matrix/models.py` with extra validation for matrix score shapes.
- `src/agent_llm_wiki_matrix/artifacts.py` for dual JSON Schema + Pydantic validation.
- CLI: `alwm validate <path> <kind>`.
- Fixtures: `fixtures/v1/*.json`; examples mirrored under `examples/v1/`.
- Markdown templates: `templates/thought.md`, `event.md`, `experiment.md`, `evaluation.md`, `matrix.md`, `report.md` (plus weekly stub).
- Tests: `tests/test_domain.py`, `tests/conftest.py` (repo root + cwd for deterministic schema resolution).

**Next:** Phase 3 — provider abstraction (`BaseProvider`, Ollama, OpenAI-compatible HTTP, mock) with YAML/env configuration.

## 2026-04-17 — Phase 1 complete (scaffold)

**Audit:** Initial repository contained only `LICENSE`. No prior scaffold to migrate.

**Delivered:**

- Repository layout: `src/agent_llm_wiki_matrix/`, `tests/`, `docs/`, `schemas/`, `templates/`, `prompts/`, `examples/`, `fixtures/`.
- Top-level: `README.md`, `AGENTS.md`, `pyproject.toml`, `justfile`, `.gitignore`, `.env.example`, `Dockerfile`, `docker-compose.yml`, `docker-bake.hcl`.
- Python package: Click CLI (`alwm`), structlog-based logging, JSON Schema helpers (`schema.py`) with path-aware caching.
- Schemas: `schemas/v1/note.schema.json`; example `examples/sample-note.json`.
- Prompt registry skeleton: `prompts/registry.yaml` + `prompts/versions/scaffold.echo.v1.txt`.
- Report template skeleton: `templates/report-weekly.md`.
- Smoke tests: `just smoke` runs `scripts/smoke.sh` — `pytest -m smoke`, host `alwm benchmark` + `benchmark campaign`, Docker Compose config + `dev` + `benchmark-offline` (optional; `SMOKE_SKIP_DOCKER=1`); prints **failure recovery analysis** on errors. Docs: `docs/workflows/smoke.md`. Dockerfile bundles `templates/` for runtime image matrix/report rendering.
- Docker: orchestrator image (`Dockerfile`); Compose profiles `dev`, `test`, `benchmark`; Bake targets for multi-arch and single-arch convenience (`orchestrator-amd64`, `orchestrator-arm64`).

**Known gaps (by design until later phases):**

- Domain models beyond minimal `note` schema (Phase 2).
- Provider adapters (Phase 3).
- Ingest/evaluate/matrix/report pipelines (Phases 4–5).
- Compose services for Ollama / model endpoints (Phase 6; placeholder comment in `docker-compose.yml`).

**Next:** Phase 2 — domain models and schemas for thought, event, experiment, evaluation, matrix, report; validators; expanded fixtures and examples.
