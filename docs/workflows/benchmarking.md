# Benchmarking workflow

## Goals

- Compare **agent stacks**, **models**, **backends**, **prompts**, and **execution modes** with reproducible inputs.
- Emit **grid** and **pairwise** matrices plus **weighted rubric scores** as structured JSON and Markdown.

## Definitions

Versioned files live in `benchmarks/v1/` (see `benchmarks/v1/README.md`). Each file includes:

| Field | Meaning |
| --- | --- |
| `prompts[]` | Stable prompt ids and text (the shared prompt set). |
| `variants[]` | **agent_stack** (label), **execution_mode** (`cli` \| `browser_mock` \| `repo_governed`), **backend** (`kind` + `model`). |

The same prompt text is executed for every variant; execution mode prefixes model output deterministically so rubric hashes differ by mode without a real browser.

## Running locally (offline)

```bash
export ALWM_FIXTURE_MODE=1
alwm benchmark run \
  --definition fixtures/benchmarks/offline.v1.yaml \
  --output-dir out/benchmark-offline \
  --created-at 1970-01-01T00:00:00Z \
  --run-id local
```

Artifacts (under `--output-dir`; lexicographic cell order in `manifest.json`):

- `cells/{variant}__{prompt}/request.json` — persisted **benchmark_request** (prompt + model + ids).
- `cells/.../response.raw.txt` — provider output **before** execution-mode tagging.
- `cells/.../response.normalized.txt` — text after tagging (what the rubric scores).
- `cells/.../benchmark_response.json` — aggregate **benchmark_response** record.
- `cells/.../evaluation.json` — **evaluation** result for that cell.
- `matrices/grid.json`, `matrices/pairwise.json` — **matrix** artifacts.
- `matrices/grid.row_inputs.json`, `matrices/pairwise.row_inputs.json` — **matrix_grid_inputs** / **matrix_pairwise_inputs** (row inputs and evaluation refs).
- `markdown/matrix.grid.md`, `markdown/matrix.pairwise.md` — rendered matrix tables.
- `reports/report.json`, `reports/report.md` — **report** JSON + generated Markdown.
- `manifest.json` — run summary with **cells[]** path index.

## Docker Compose

| Recipe | Profile | Notes |
| --- | --- | --- |
| `just benchmark-offline` | `benchmark-offline` | Mock-only; `ALWM_FIXTURE_MODE=1`; writes `out/benchmark-offline`. |
| `just benchmark-ollama` | `benchmark-ollama` | Starts `ollama/ollama`; run `docker compose exec ollama ollama pull llama3.2` (or your model) before benchmarking. |
| `just benchmark-llamacpp` | `benchmark-llamacpp` | Points `OPENAI_BASE_URL` at `LLAMACPP_OPENAI_BASE_URL` (default `http://host.docker.internal:8080/v1`); start `llama-server` on the host first. |

## Determinism

- CI uses `fixtures/benchmarks/offline.v1.yaml` with mock backends only.
- Use a fixed `--created-at` for byte-stable JSON when comparing runs.
- Live runs should record model ids and provider hostnames in your own experiment notes (future: automatic metadata block in manifest).

## Current state

- End-to-end harness is implemented (`alwm benchmark run`).
- Ollama and OpenAI-compatible paths require running services and models; offline tests stay on **mock** only.
