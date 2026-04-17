# Data model

_Phase 1: introductory note schema only. Phase 2 will add full entities._

## Principles

- **Git-native**: artifacts are plain files (Markdown, JSON, YAML) suitable for diff and review.
- **Validation**: JSON Schema (Draft 2020-12) for machine-readable records; Markdown for human narrative.
- **Identifiers**: stable string IDs (slugs or UUIDs) as required fields.

## Implemented (Phase 1)

### `WikiNote` (`schemas/v1/note.schema.json`)

Minimal structured note for wiki-style content: `id`, `kind`, `title`, `body_markdown`, `created_at`, optional `tags` and `links`.

## Planned (Phase 2+)

| Entity | Role |
| --- | --- |
| Thought | Atomic idea or hypothesis |
| Event | Timestamped occurrence (run, incident, observation) |
| Experiment | Protocol, parameters, outcomes |
| Evaluation | Rubric-scored assessment of an artifact or run |
| Matrix | Pairwise or multi-dimensional comparison payload |
| Report | Aggregated narrative + tables for humans |

Relationships and cross-links will use explicit ID references and/or repo-relative paths, documented when schemas land.
