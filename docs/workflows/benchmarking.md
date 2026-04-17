# Benchmarking workflow

For **offline vs live** modes and Compose profiles, see [live-verification.md](live-verification.md).

## Goals

- Compare **agent stacks**, **models**, **backends**, **prompts**, and **execution modes** with reproducible inputs.
- Emit **grid** and **pairwise** matrices plus **weighted rubric scores** as structured JSON and Markdown.

## Definitions

Versioned files live in `benchmarks/v1/` (see `benchmarks/v1/README.md`). Each file includes:

| Field | Meaning |
| --- | --- |
| `prompts[]` | Stable prompt ids and text (the shared prompt set). |
| `variants[]` | **agent_stack** (label), **execution_mode** (`cli` \| `browser_mock` \| `repo_governed`), **backend** (`kind` + `model`), optional **`browser`** (only with `browser_mock`). |

For **`cli`** and **`repo_governed`**, the same resolved prompt text is sent to the provider (with execution-mode tagging on the normalized response). For **`browser_mock`**, the harness runs a **browser evidence phase** first (`MockBrowserRunner` by default, or **`browser.runner`**: `file`, `playwright`, `mcp`), writes **`cells/.../browser_evidence.json`**, and **appends** a markdown evidence block to the prompt before calling the provider. Request/response records store the **effective** prompt (including browser context).

| `browser.runner` | When to use | CI / notes |
| --- | --- | --- |
| `mock` (default) | Synthetic trace from `MockBrowserRunner` | Deterministic; default tests |
| `file` | Load JSON from `scenario_id` or `fixture_relpath` | Deterministic; no network |
| `mcp` | Same file loading as `file`, labeled runner `mcp` (fixture bridge) | Remote MCP tools **not** implemented |
| `playwright` | Live navigation; requires `start_url` | Set **`ALWM_BENCHMARK_PLAYWRIGHT=1`**, install **`[browser]`** + `playwright install …`; not part of default `just ci` |

### Taxonomy and optional metadata (v1)

Example and production definitions may add **optional** fields (older suites omit them; still valid):

| Field | Meaning |
| --- | --- |
| `taxonomy` | `taxonomy_version: 1`, **task_family**, **difficulty**, **determinism**, optional **tool_requirements[]**. Schema: `schemas/v1/benchmark_taxonomy.schema.json`. |
| `time_budget_seconds` | Wall-clock hint for agent runners (not enforced by the harness). |
| `token_budget` | Token budget hint (not enforced). |
| `retry_policy` | `{ max_attempts, backoff_seconds }` for agent implementations (harness does not loop yet). |
| `tags` | Free-form labels for filters and dashboards. |
| `expected_artifact_kinds` | Registered `alwm validate` kinds expected when reviewing cells. |

These copy into **`manifest.json`** when set. Example suites: `examples/benchmark_suites/v1/suite.taxonomy.*.v1.yaml`; example runs with taxonomy: `examples/benchmark_runs/taxonomy-repo-governance/`, `taxonomy-runtime-config/`.

**Task families:** `repo_governance`, `runtime_config`, `documentation`, `browser_evidence`, `matrix_reasoning`, `multi_agent_coordination`, `campaign`, `scaffolding`, `integration`, `other`. **Difficulty:** `trivial` … `stress`. **Determinism:** `deterministic_fixture`, `deterministic_scoring`, `stochastic_live`. **Tool requirements (hints):** `none`, `cli`, `registry`, `browser_mock`, `repo_context`, `live_llm`, `playwright`, `compose`, `multi_variant`.

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

- `cells/{variant}__{prompt}/request.json` — persisted **benchmark_request** (effective prompt + model + ids; may include optional **`browser_runner`** / **`browser_evidence_relpath`**).
- `cells/.../browser_evidence.json` — **browser_evidence** for `browser_mock` variants (omitted for `cli` / `repo_governed`).
- `cells/.../response.raw.txt` — provider output **before** execution-mode tagging.
- `cells/.../response.normalized.txt` — text after tagging (what the rubric scores).
- `cells/.../benchmark_response.json` — aggregate **benchmark_response** record.
- `cells/.../evaluation.json` — **evaluation** result for that cell.
- `matrices/grid.json`, `matrices/pairwise.json` — **matrix** artifacts.
- `matrices/grid.row_inputs.json`, `matrices/pairwise.row_inputs.json` — **matrix_grid_inputs** / **matrix_pairwise_inputs** (row inputs and evaluation refs).
- `markdown/matrix.grid.md`, `markdown/matrix.pairwise.md` — rendered matrix tables.
- `reports/report.json`, `reports/report.md` — **report** JSON + generated Markdown.
- `manifest.json` — run summary with **cells[]** path index; may include **`definition_source_relpath`** and **`prompt_registry_effective_ref`** for reproducibility when the definition path and registry-backed prompts are known. Validate with **`alwm validate <path> benchmark_manifest`** (JSON Schema `schemas/v1/manifest.schema.json` + Pydantic `BenchmarkRunManifest`). The harness writes manifests that pass this check; older committed runs may omit optional provenance keys entirely (still valid).

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
