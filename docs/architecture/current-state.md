# Current architecture

_Last updated: 2026-04-17 (Phase 2)._

## Summary

The repository is a **docs-first** workspace for an LLM wiki and comparison matrix, with a Python orchestration package and Docker-based build/run tooling. Phase 2 added **domain models** and **JSON Schemas** for core entities, **fixtures**, **examples**, **markdown templates**, and a **`validate`** CLI command.

## Components

| Component | Status | Notes |
| --- | --- | --- |
| CLI (`alwm`) | Implemented | `version`, `info`, `validate` |
| JSON Schema + Pydantic | Implemented | Thought, Event, Experiment, Evaluation, Matrix, Report |
| Wiki `WikiNote` schema | Implemented | `note.schema.json`; examples still JSON-only |
| Prompt registry | Skeleton | `prompts/registry.yaml` |
| Markdown templates | Skeleton | `templates/*.md` plus weekly report stub |
| Provider layer | Not implemented | Phase 3 |
| Pipelines (ingest/evaluate) | Not implemented | Phases 4–5 |
| Browser evidence layer | Not implemented | Planned: mock + fixtures |

## Runtime

- **Local:** Python 3.11+ (`pyproject.toml`); `make ci` for lint, typecheck, tests.
- **Container:** `Dockerfile` produces non-root `alwm` image; Compose mounts repo at `/workspace` for dev/test/benchmark profiles.
- **Build:** `docker buildx bake` defaults to `linux/amd64` and `linux/arm64`; `orchestrator-amd64` / `orchestrator-arm64` for single-arch builds.

## Data flow (today)

```mermaid
flowchart LR
  subgraph repo [Git repository]
    SCH[JSON Schemas]
    FIX[fixtures/v1 JSON]
    EX[examples/v1 JSON]
  end
  VAL[jsonschema + Pydantic]
  CLI[alwm validate]
  SCH --> VAL
  FIX --> VAL
  EX --> CLI
  CLI --> VAL
```

## Testing

- Pytest covers smoke tests, all v1 fixtures, matrix dimension validation, and CLI `validate`.
- No live network tests by default.
