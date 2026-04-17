# Benchmarking workflow

## Goals

- Compare **agent stacks**, **models**, **backends**, **prompts**, and **orchestration patterns** with reproducible inputs.
- Emit **pairwise or grid matrices** and **weighted scores** as structured JSON plus human-readable Markdown.

## Configuration

1. Copy `.env.example` to `.env` and set `ALWM_PROVIDER` to `mock` (CI), `ollama`, or `openai_compatible` (llama.cpp-style HTTP servers exposing `/v1/chat/completions`).
2. Optionally add `config/providers.yaml` (see `config/providers.example.yaml`); override with `OLLAMA_*` or `OPENAI_*` environment variables.
3. Record **prompt registry** IDs and **schema versions** in benchmark outputs when publishing results.

## Running comparisons (offline matrix)

Deterministic scoring (no LLM calls) is the default for `alwm evaluate`. It uses **SHA-256–derived** per-criterion scores in `[0, 1]` so the same subject text always produces the same evaluation JSON.

1. Ingest Markdown pages to Thought JSON (optional if you already have subjects):

   ```bash
   alwm ingest examples/dataset/pages examples/dataset/thoughts --created-at 1970-01-01T00:00:00Z
   ```

2. Evaluate each subject against a rubric:

   ```bash
   alwm evaluate --subject examples/dataset/pages/retrieval-basics.md \
     --rubric examples/v1/rubric.json \
     --out examples/dataset/evals/retrieval-basics.eval.json
   ```

3. Compare evaluations into a matrix (optional Markdown sidecar):

   ```bash
   alwm compare eval-a.json eval-b.json \
     --out matrix.json --out-md matrix.md \
     --id bench-matrix --title "Bench run"
   ```

4. Render a report artifact + Markdown:

   ```bash
   alwm report --matrix matrix.json \
     --out-json report.json --out-md report.md \
     --id bench-report-001
   ```

## Docker Compose

- **benchmark** profile runs `alwm info` against the mounted repository as a quick smoke (replace `command` in `docker-compose.yml` for custom harnesses).

```bash
docker compose --profile benchmark run --rm benchmark
```

## Determinism

- Set `ALWM_FIXTURE_MODE=1` in `.env` as a convention when runs must avoid live endpoints (providers still read config; pipelines themselves do not call the network).
- Use fixed `--created-at` / `--evaluated-at` timestamps when you need byte-stable JSON across machines.

## Current state

- Provider adapters are available for **Ollama** (`/api/chat`) and **OpenAI-compatible** servers (`/v1/chat/completions`).
- LLM-assisted rubric scoring can be layered on later; today’s `evaluate` command is **pipeline-only** for reproducibility.
