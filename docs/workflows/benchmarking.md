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

For **`cli`** and **`repo_governed`**, the same resolved prompt text is sent to the provider (with execution-mode tagging on the normalized response). For **`browser_mock`**, the harness runs a **browser evidence phase** first (`MockBrowserRunner` by default, or **`browser.runner`**: `file`, `playwright`, `mcp`), writes **`cells/.../browser_evidence.json`** (navigation, console, optional **`dom_excerpts`**, **`screenshots`** metadata, **`extensions`** JSON), and **appends** a markdown evidence block to the prompt before calling the provider. Request/response records store the **effective** prompt (including browser context). Browser-focused scoring may use **`examples/dataset/rubrics/browser_realism.v1.json`** (grounding / hallucination resistance / source fidelity). **`mcp`** here is still **fixture-backed** unless remote MCP tools are implemented; see **`docs/architecture/browser.md`**.

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
| `success_criteria` | Human-readable pass conditions for comparing external agent systems (metadata; copied to **`manifest.json`**). |
| `failure_taxonomy_hints` | Suggested failure-class labels for cross-system or longitudinal reports (metadata). |

**Determinism classification** is **`taxonomy.determinism`** (`deterministic_fixture`, `deterministic_scoring`, `stochastic_live`). The **agentic benchmark pack** (`examples/benchmark_suites/v1/agentic/`) documents cross-system use: **`docs/workflows/agentic-benchmark-pack.md`**.

### Eval scoring backends (optional)

| Field | Meaning |
| --- | --- |
| `eval_scoring.backend` | `deterministic` (default): byte-hash rubric scores. `semantic_judge`: LLM returns JSON scores per criterion. `hybrid`: per-criterion blend of deterministic + semantic. |
| `eval_scoring.hybrid` | When `backend` is `hybrid`: `deterministic_weight` and `semantic_weight` (must sum to 1.0). |
| `eval_scoring.judge_provider_ref` | Optional repo-relative providers YAML for the judge; otherwise **`--provider-config`** on `alwm benchmark run`. |
| `eval_scoring.judge_repeats` | Number of semantic judge calls per cell (default **1**). When **>1**, per-criterion scores are aggregated (see below) and **`evaluation_judge_provenance.json`** includes **`repeat_aggregation`** (per-run raw text, disagreement metrics, optional low-confidence flags). |
| `eval_scoring.semantic_aggregation` | **`mean`** (default), **`median`**, or **`trimmed_mean`** (combines scores across `judge_repeats`). |
| `eval_scoring.trim_fraction` | For **`trimmed_mean`**: fraction removed from each tail before averaging (default **0.1**). |
| `eval_scoring.judge_max_*` | Optional thresholds (`judge_max_criterion_range`, `judge_max_criterion_stdev`, `judge_max_mean_criterion_stdev`, `judge_max_total_weighted_stdev`) that set **`judge_low_confidence`** on **`evaluation.json`** when repeated-run disagreement exceeds them. |

Each successful **`alwm benchmark run`** writes **`comparison_fingerprints`** on **`manifest.json`**: six **`sha256:`** axes (suite definition, prompt set, per-variant provider configs, scoring config, browser config, **prompt registry state**) so runs can be grouped and compared longitudinally without re-reading YAML.

CLI: **`--eval-scoring-backend`**, **`--judge-provider-config`**. With **`ALWM_FIXTURE_MODE=1`**, the judge uses a **mock** provider with deterministic pseudo-semantic scores (CI-safe). Opt-in live judge: set **`ALWM_JUDGE_LIVE=1`** (and configure Ollama / OpenAI-compatible env vars). Semantic or hybrid runs write **`cells/.../evaluation_judge_provenance.json`** (full judge prompt, provider, raw response(s), aggregated parsed scores, hybrid aggregation when applicable, **`repeat_aggregation`** when **`judge_repeats` > 1**) and reference it from **`evaluation.json`**.

**`alwm evaluate`** (non-deterministic backends): **`--judge-repeats`**, **`--semantic-aggregation`**, **`--trim-fraction`**, and the same **`--judge-max-...`** threshold flags.

These copy into **`manifest.json`** when set. Example suites: `examples/benchmark_suites/v1/suite.taxonomy.*.v1.yaml`; example runs with taxonomy: `examples/benchmark_runs/taxonomy-repo-governance/`, `taxonomy-runtime-config/`.

**Task families:** `repo_governance`, `runtime_config`, `documentation`, `browser_evidence`, `matrix_reasoning`, `multi_agent_coordination`, `campaign`, `scaffolding`, `integration`, `other`. Example browser suites: **`suite.taxonomy.browser_evidence.v1`**, **`suite.taxonomy.browser_checkout.v1`**, **`suite.taxonomy.browser_form.v1`**, **`suite.agentic.browser_interpretation.v1`**, **`suite.agentic.browser_checkout.v1`** (all use deterministic **`file`** or default **`mock`** runners unless you opt into Playwright). **Difficulty:** `trivial` … `stress`. **Determinism:** `deterministic_fixture`, `deterministic_scoring`, `stochastic_live`. **Tool requirements (hints):** `none`, `cli`, `registry`, `browser_mock`, `repo_context`, `live_llm`, `playwright`, `compose`, `multi_variant`.

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
- `reports/report.json`, `reports/report.md` — **report** JSON + generated Markdown (when **`browser_mock`** cells ran, **`report.md`** includes **Browser evidence (fixture summary)** — evidence ids, runner, excerpt/screenshot counts, extension keys — before optional **Runtime observability**).
- `manifest.json` — run summary with **cells[]** path index; may include **`definition_source_relpath`** and **`prompt_registry_effective_ref`** for reproducibility when the definition path and registry-backed prompts are known. Validate with **`alwm validate <path> benchmark_manifest`** (JSON Schema `schemas/v1/manifest.schema.json` + Pydantic `BenchmarkRunManifest`). The harness writes manifests that pass this check; older committed runs may omit optional provenance keys entirely (still valid).

### Runtime observability (optional fields)

Newer runs add **wall-clock metadata** (still backward compatible when omitted):

| Field | Meaning |
| --- | --- |
| **`runtime_summary`** | `started_at_utc`, `finished_at_utc`, **`duration_seconds`**, and phase sums: **`browser_phase_seconds`**, **`provider_completion_seconds`**, **`evaluation_phase_seconds`**, **`judge_phase_seconds`**. |
| **`retry_summary`** | Echoes **`retry_policy.max_attempts`** when present; **`total_judge_invocations`** (sum of configured semantic judge repeats across cells); **`cells_with_judge_parse_fallback`** (cells where a semantic parse fell back to deterministic mock scores). |
| **`cells[].runtime`** | Per-cell breakdown of the same phases where applicable. |

**`reports/report.md`** appends a **Runtime observability** section with the same tables. **Campaign** roots add **`aggregated_runtime`** (sums over successful member manifests) and a section in **`campaign-summary.md`**. Harness retries on provider/judge are not implemented yet; **`retry_policy`** remains metadata except for the manifest summary above.

For a **full-application smoke** gate (pytest + host CLI + Docker offline benchmark + failure recovery analysis), see [smoke.md](smoke.md).

## Docker Compose

| Recipe | Profile | Notes |
| --- | --- | --- |
| `just benchmark-offline` | `benchmark-offline` | Mock-only; `ALWM_FIXTURE_MODE=1`; writes `out/benchmark-offline`. |
| `just benchmark-ollama` | `benchmark-ollama` | Full Compose benchmark using **`benchmarks/v1/ollama.v1.yaml`** ( **`gpt-oss:20b`** ). Run **`just ollama-gptoss-setup`** first so the model is pulled and verified. |
| `just ollama-gptoss-setup` | `benchmark-ollama` | Start Ollama, pull **`gpt-oss:20b`**, **`alwm benchmark probe`** from the host. Models live under **`OLLAMA_MODELS_DIR`** (default **`./.ollama-models`**). |
| `just smoke-ollama-live` | (host) | Opt-in minimal live benchmark (`benchmarks/v1/ollama.v1.yaml`); requires reachable Ollama with the model pulled. Not part of **`just ci`**. |
| `just benchmark-probe` | `benchmark-probe` | Runs `alwm benchmark probe` with `OLLAMA_HOST=http://ollama:11434` and host `OPENAI_BASE_URL` for llama.cpp — no full benchmark, only API reachability. |
| `just benchmark-llamacpp` | `benchmark-llamacpp` | Points `OPENAI_BASE_URL` at `LLAMACPP_OPENAI_BASE_URL` (default `http://host.docker.internal:8080/v1`); start `llama-server` on the host first. |

### Live API checks (CLI)

```bash
alwm benchmark probe
# With explicit hosts:
OLLAMA_HOST=http://127.0.0.1:11434 OPENAI_BASE_URL=http://127.0.0.1:8080/v1 alwm benchmark probe
```

### Ollama (gpt-oss:20b) local workflow

The repo standardizes on **OpenAI gpt-oss** at the **`gpt-oss:20b`** tag in Ollama (see [Ollama library](https://ollama.com/library/gpt-oss)). Benchmark definitions and provider defaults use that tag so **`benchmarks/v1/ollama.v1.yaml`**, **`config/providers.example.yaml`**, and **`OLLAMA_MODEL`** stay aligned.

1. **One-shot setup (recommended):** `just ollama-gptoss-setup` — starts the Compose **`ollama`** service, waits for the CLI, pulls **`gpt-oss:20b`** into the bind-mounted store (default **`./.ollama-models`**), then runs **`alwm benchmark probe`** against **`http://127.0.0.1:11434`** to confirm the API and model list.
2. **Full Compose benchmark:** `just benchmark-ollama` (after setup; writes **`out/benchmark-ollama`**).
3. **Host-only minimal live smoke:** `just smoke-ollama-live` — probes, then **`alwm benchmark run --definition benchmarks/v1/ollama.v1.yaml`** with **`--no-fixture-mock`** (output default **`$TMPDIR/alwm-smoke-ollama`**, override with **`ALWM_SMOKE_OLLAMA_OUT`**).

Environment overrides: **`OLLAMA_PULL_MODEL`**, **`OLLAMA_PROBE_HOST`** (for **`ollama-gptoss-setup.sh`**), **`OLLAMA_HOST`**, **`OLLAMA_MODEL`** (defaults **`gpt-oss:20b`** in **`config/providers.example.yaml`** and the **`alwm benchmark probe`** CLI default).

#### Migrating from the old named Docker volume to `./.ollama-models`

Earlier Compose used a **named volume** (`ollama_models`) for `/root/.ollama`. The stack now **bind-mounts** **`OLLAMA_MODELS_DIR`** (default **`./.ollama-models`**) so blobs are visible on the host and easy to back up.

1. Stop containers: `docker compose --profile benchmark-ollama down` (adjust profile if needed).
2. Find the old volume: `docker volume ls | grep ollama` (often `*_ollama_models` depending on project name).
3. Copy data into the bind mount (example; replace `VOLUME_NAME`):

   ```bash
   mkdir -p .ollama-models
   docker run --rm -v VOLUME_NAME:/from -v "$PWD/.ollama-models:/to" alpine \
     sh -c 'cp -a /from/. /to/'
   ```

4. Remove the old volume only after verifying pulls work: `docker volume rm VOLUME_NAME` (destructive).

5. Bring Ollama back: `just ollama-gptoss-setup` or `docker compose --profile benchmark-ollama up -d ollama`.

If you skip migration, Ollama simply downloads models again into **`./.ollama-models`**.

## Integration tests (opt-in)

Default **`just test`** / **`just ci`** run **`pytest tests/ --ignore=tests/integration`** so CI never requires Ollama or llama.cpp.

To verify end-to-end benchmark cells against **live** backends:

1. Start services (or use Compose profiles above).
2. Export **one or both** flags:
   - `ALWM_LIVE_BENCHMARK_OLLAMA=1` — uses `OLLAMA_HOST` (default `http://127.0.0.1:11434`) and `OLLAMA_MODEL` (default **`gpt-oss:20b`**).
   - `ALWM_LIVE_BENCHMARK_LLAMACPP=1` — uses `OPENAI_BASE_URL` and `OPENAI_MODEL` (default `gpt-oss` to match `benchmarks/v1/llamacpp.v1.yaml`).
3. Run:

```bash
just test-integration
# or: pytest tests/integration/ -v -m integration
```

Tests **skip** (fixture-safe) when the flag is unset, when the HTTP probe fails (connection error), or when Ollama has no matching model pulled. The OpenAI-compatible probe treats any HTTP response on ``GET …/v1/models`` with a non-server-error status as reachable (some llama.cpp builds return 404 for that route while chat still works).

## Campaign sweeps (multi-run)

Orchestrate many benchmark runs from one definition (suites × providers × eval scoring × browser overrides): **`docs/workflows/benchmark-campaigns.md`**, CLI **`alwm benchmark campaign run`** (execute) and **`alwm benchmark campaign run --dry-run`** (plan only: **`campaign-dry-run.json`**, no member **`runs/`**). Each member run is a standard benchmark directory with **`benchmark_manifest`** and **six-axis** **`comparison_fingerprints`**; the campaign root **`manifest.json`** is **`campaign_manifest`** with **`campaign_definition_fingerprint`** and **`campaign_experiment_fingerprints`** (six campaign axes), plus **`campaign-summary.*`**. **Walkthrough:** **`docs/workflows/campaign-walkthrough.md`**. Wiki: **`docs/wiki/campaign-orchestration.md`** (concept) and **`docs/wiki/benchmark-campaigns.md`** (index); ADR: **`docs/adr/0001-campaign-orchestration.md`** or **`docs/architecture/adr/0001-benchmark-campaign-orchestration.md`**; tracking: **`docs/tracking/campaign-orchestration.md`**. Longitudinal: glob **`runs/*/manifest.json`** under the campaign output dir.

## Determinism

- CI uses `fixtures/benchmarks/offline.v1.yaml` with mock backends only.
- Use a fixed `--created-at` for byte-stable JSON when comparing runs.
- Live runs should record model ids and provider hostnames in your own experiment notes (future: automatic metadata block in manifest).

## Current state

- End-to-end harness is implemented (`alwm benchmark run`).
- Live verification: `alwm benchmark probe`, Compose **`benchmark-probe`** profile, and **opt-in** integration tests under `tests/integration/`.
