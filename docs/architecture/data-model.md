# Data model

_Last updated: 2026-04-17 (benchmark prompt registry)._

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
| `schemas/v1/evaluation.schema.json` | `Evaluation` | Rubric-scored assessment |
| `schemas/v1/matrix.schema.json` | `ComparisonMatrix` | Pairwise/grid scores with labels |
| `schemas/v1/report.schema.json` | `Report` | Human-facing narrative report |
| `schemas/v1/note.schema.json` | _(no Pydantic model yet)_ | Lightweight wiki note (Phase 1) |
| `schemas/v1/browser_evidence.schema.json` | `BrowserEvidence` (`browser.models`) | Navigation + console (+ optional DOM ref) for browser runs |
| `schemas/v1/benchmark_definition.schema.json` | _(YAML; Pydantic `BenchmarkDefinitionV1`)_ | Benchmark suite: rubric, prompts (inline `text` xor `prompt_ref`), variants |
| `schemas/v1/prompt_registry.schema.json` | `PromptRegistryDocument` | `prompts/registry.yaml`: ids, paths to prompt bodies, document `version` |
| `schemas/v1/benchmark_request.schema.json` | `BenchmarkRequestRecord` | Per-cell provider request; includes `prompt_source`, optional `prompt_registry_id`, `registry_document_version`, `prompt_source_relpath` |
| `schemas/v1/benchmark_response.schema.json` | `BenchmarkResponse` | Same prompt provenance fields as request for traceability |

## Validation

- `agent_llm_wiki_matrix.artifacts.parse_artifact(kind, data)` runs JSON Schema validation then Pydantic parsing.
- CLI: `alwm validate <path> <kind>` — includes `browser_evidence` and benchmark/matrix kinds (see `list_artifact_kinds()`).

## Templates

Markdown templates for each entity live under `templates/` (placeholders for Phase 5 reporting).
