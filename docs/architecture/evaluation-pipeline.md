# Evaluation pipeline

## Stages

1. **Ingest:** Parse Markdown wiki pages into `Thought` JSON (`alwm ingest`).
2. **Extract:** (Incremental) Pull structured claims or checklist items suitable for scoring—deterministic parsers first; optional LLM assist behind provider adapters.
3. **Evaluate:** Score subjects against JSON **rubrics** with explicit weights; persist `Evaluation` artifacts (`alwm evaluate`). The default implementation uses **deterministic byte-hash scores** per criterion (no network).
4. **Compare:** Build **grid matrices** over evaluations and emit `ComparisonMatrix` JSON plus optional Markdown (`alwm compare`).
5. **Summarize:** Emit Markdown reports from `templates/report.md` plus structured `Report` JSON (`alwm report`).

## Determinism

- Prefer fixtures and frozen inputs for CI.
- When LLMs are used, record provider id, model id, prompt version, and seed/settings in evaluation metadata.

## Current state

- **Rubric** schema and fixtures/examples are checked in (`schemas/v1/rubric.schema.json`).
- **Ingest / evaluate / compare / report** CLI commands run offline in tests; provider adapters exist for live backends when you wire them to future scoring modes.
