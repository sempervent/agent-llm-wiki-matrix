# Evaluation pipeline

_Target design; Phase 1 implements only schema validation scaffolding._

## Intended stages

1. **Ingest:** Parse raw markdown notes into structured records (thought/event/experiment) with provenance.
2. **Extract:** Pull structured claims or checklist items suitable for scoring (deterministic parsers + optional LLM assist behind adapters).
3. **Evaluate:** Score against YAML/JSON **rubrics** with explicit weights; persist `Evaluation` artifacts.
4. **Compare:** Build **pairwise comparison matrices** and aggregate **weighted scores** across dimensions (agent stack, model, backend, prompt, browser behavior).
5. **Summarize:** Emit Markdown reports (weekly, model/provider, agent-stack, browser evidence) from templates.

## Determinism

- Prefer fixtures and frozen inputs for CI.
- When LLMs are used, record provider id, model id, prompt version, and seed/settings in evaluation metadata.

## Current state

- Rubrics under `schemas/` / `fixtures/` to be added in Phase 2+.
- No automated ingest or scoring yet; `alwm` CLI provides operational hooks only.
