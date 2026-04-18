# Data model

_Last updated: 2026-04-18 (six-axis `comparison_fingerprints`, `campaign_experiment_fingerprints` on campaign manifests)._

## Principles

- **Git-native**: artifacts are plain JSON/Markdown files suitable for review.
- **Dual validation**: JSON Schema (Draft 2020-12) for contract checks; Pydantic models for typed parsing with extra constraints (for example matrix row/column shapes).
- **Identifiers**: `id` fields are stable, non-empty strings (slug or UUID).

## Entities (v1)

| Schema | Pydantic model | Purpose |
| --- | --- | --- |
| `schemas/v1/thought.schema.json` | `Thought` | Atomic idea or hypothesis |
| `schemas/v1/event.schema.json` | `Event` | Timestamped run/incident/observation |
| `schemas/v1/experiment.schema.json` | `Experiment` | Protocol, parameters, lifecycle |
| `schemas/v1/evaluation.schema.json` | `Evaluation` | Rubric-scored assessment; optional **`scoring_backend`**, **`judge_provenance_relpath`**, and when repeated semantic runs are used: **`judge_repeat_count`**, **`judge_semantic_aggregation`**, **`judge_low_confidence`** |
| `schemas/v1/evaluation_judge_provenance.schema.json` | `EvaluationJudgeProvenance` | Judge prompt, provider, raw response(s), aggregated parsed scores, optional hybrid aggregation, optional **`repeat_aggregation`** (per-run records, disagreement metrics, confidence flags) |
| `schemas/v1/matrix.schema.json` | `ComparisonMatrix` | Pairwise/grid scores with labels |
| `schemas/v1/report.schema.json` | `Report` | Human-facing narrative report |
| `schemas/v1/note.schema.json` | _(no Pydantic model yet)_ | Lightweight wiki note (Phase 1) |
| `schemas/v1/browser_evidence.schema.json` | `BrowserEvidence` (`browser.models`) | Navigation + console; optional **`dom_snapshot_ref`**; **`dom_excerpts[]`** (visible text / HTML snippets); **`screenshots[]`** (viewport, MIME, integrity hash, optional **`relpath`**); **`extensions`** JSON bag for structured runner fields |
| `schemas/v1/benchmark_definition.schema.json` | _(YAML; Pydantic `BenchmarkDefinitionV1`)_ | Benchmark suite: rubric, prompts (inline `text` xor `prompt_ref`), variants |
| `schemas/v1/prompt_registry.schema.json` | `PromptRegistryDocument` | `prompts/registry.yaml`: ids, paths to prompt bodies, document `version` |
| `schemas/v1/benchmark_request.schema.json` | `BenchmarkRequestRecord` | Per-cell provider request; includes `prompt_source`, optional `prompt_registry_id`, `registry_document_version`, `prompt_source_relpath` |
| `schemas/v1/benchmark_response.schema.json` | `BenchmarkResponse` | Same prompt provenance fields as request for traceability |
| `schemas/v1/manifest.schema.json` | `BenchmarkRunManifest` | Run index (`manifest.json`): `cells[]`, matrix/report paths; optional **`definition_source_relpath`**, **`prompt_registry_effective_ref`** (omit or null when unknown); optional **`success_criteria`**, **`failure_taxonomy_hints`** (cross-system evaluation metadata); optional **`comparison_fingerprints`** (six **`sha256:`** hashes: suite definition sans title, resolved prompt set, per-variant provider configs, effective scoring + judge config, browser blocks, prompt registry state) |
| `schemas/v1/benchmark_campaign.schema.json` | `BenchmarkCampaignDefinitionV1` | Campaign sweep definition (YAML/JSON): **`suite_refs`**, sweep axes, optional **`prompt_registry_ref`**; see **`load_benchmark_campaign_definition`** |
| `schemas/v1/benchmark_campaign_manifest.schema.json` | `BenchmarkCampaignManifest` | Campaign index (`manifest.json` at campaign root): member **`runs[]`**, optional **`campaign_definition_fingerprint`**, optional **`campaign_experiment_fingerprints`** (per-axis suite/provider/scoring/browser/registry hashes); member runs may include **`comparison_fingerprints`** copied from each child run’s `manifest.json` |
| `schemas/v1/campaign_summary.schema.json` | `CampaignSummaryV1` | Rollup JSON (`campaign-summary.json`) aligned with the campaign manifest for dashboards |

Committed campaign output example (validate + fingerprint fields): **`docs/workflows/campaign-walkthrough.md`**.

## Validation

- `agent_llm_wiki_matrix.artifacts.parse_artifact(kind, data)` runs JSON Schema validation then Pydantic parsing.
- CLI: `alwm validate <path> <kind>` — includes `browser_evidence` and benchmark/matrix kinds (see `list_artifact_kinds()`).

## Templates

Markdown templates for each entity live under `templates/` (placeholders for Phase 5 reporting).
