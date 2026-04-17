# Benchmarking workflow

_Target workflow; harness implementation lands in Phases 3–6._

## Goals

- Compare **agent stacks**, **models**, **backends**, **prompts**, and **orchestration patterns** with reproducible inputs.
- Emit **pairwise matrices** and **weighted scores** as structured JSON + human-readable Markdown.

## Planned usage (stub)

1. Fix provider configuration (`.env` / YAML) — Ollama or OpenAI-compatible HTTP, or `mock` for CI.
2. Run benchmark profile via Compose or local CLI (commands to be added).
3. Store outputs under a gitignored or committed-results path (policy TBD per team).

## Determinism

- Use `ALWM_FIXTURE_MODE=1` when implemented to avoid network calls.
- Record prompt registry IDs and schema versions in every benchmark output.

## Current state

- Compose `benchmark` profile exists as a **hook** for future services.
- No benchmark CLI subcommands yet; see `docs/implementation-log.md`.
