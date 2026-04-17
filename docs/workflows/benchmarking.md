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
| `just benchmark-ollama` | `benchmark-ollama` | Ollama service has a **healthcheck** (`ollama list`); `benchmark-ollama` waits for **healthy**. Pull a model first, e.g. `docker compose --profile benchmark-ollama exec ollama ollama pull llama3.2`. |
| `just benchmark-probe` | `benchmark-probe` | Runs `alwm benchmark probe` with `OLLAMA_HOST=http://ollama:11434` and host `OPENAI_BASE_URL` for llama.cpp — no full benchmark, only API reachability. |
| `just benchmark-llamacpp` | `benchmark-llamacpp` | Points `OPENAI_BASE_URL` at `LLAMACPP_OPENAI_BASE_URL` (default `http://host.docker.internal:8080/v1`); start `llama-server` on the host first. |

### Live API checks (CLI)

```bash
alwm benchmark probe
# With explicit hosts:
OLLAMA_HOST=http://127.0.0.1:11434 OPENAI_BASE_URL=http://127.0.0.1:8080/v1 alwm benchmark probe
```

## Integration tests (opt-in)

Default **`just test`** / **`just ci`** run **`pytest tests/ --ignore=tests/integration`** so CI never requires Ollama or llama.cpp.

To verify end-to-end benchmark cells against **live** backends:

1. Start services (or use Compose profiles above).
2. Export **one or both** flags:
   - `ALWM_LIVE_BENCHMARK_OLLAMA=1` — uses `OLLAMA_HOST` (default `http://127.0.0.1:11434`) and `OLLAMA_MODEL` (default `llama3.2`).
   - `ALWM_LIVE_BENCHMARK_LLAMACPP=1` — uses `OPENAI_BASE_URL` and `OPENAI_MODEL` (default `gpt-oss` to match `benchmarks/v1/llamacpp.v1.yaml`).
3. Run:

```bash
just test-integration
# or: pytest tests/integration/ -v -m integration
```

Tests **skip** (fixture-safe) when the flag is unset, when the HTTP probe fails (connection error), or when Ollama has no matching model pulled. The OpenAI-compatible probe treats any HTTP response on ``GET …/v1/models`` with a non-server-error status as reachable (some llama.cpp builds return 404 for that route while chat still works).

## Determinism

- CI uses `fixtures/benchmarks/offline.v1.yaml` with mock backends only.
- Use a fixed `--created-at` for byte-stable JSON when comparing runs.
- Live runs should record model ids and provider hostnames in your own experiment notes (future: automatic metadata block in manifest).

## Current state

- End-to-end harness is implemented (`alwm benchmark run`).
- Live verification: `alwm benchmark probe`, Compose **`benchmark-probe`** profile, and **opt-in** integration tests under `tests/integration/`.
