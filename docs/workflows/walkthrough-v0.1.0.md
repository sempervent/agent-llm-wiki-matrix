# End-to-end walkthrough (v0.1.0, committed examples only)

This walkthrough runs entirely from the **repository checkout**. Inputs are under **`examples/`** and **`fixtures/`**; generated files go to a **temporary directory** so the working tree stays clean.

**Prerequisites:** [uv](https://docs.astral.sh/uv/) (required), Python **3.11+** (via `uv venv`), [just](https://github.com/casey/just), repo root as current working directory. Commands below use **`uv run`** so you do not need to activate `.venv` (see **`AGENTS.md`**).

## 1. Environment and sanity checks

```bash
uv venv --python 3.11
uv pip install -e ".[dev]"

uv run alwm version    # expect: 0.1.0
uv run alwm info
uv run just ci
```

## 2. Validate example artifacts

```bash
uv run alwm validate examples/v1/thought.json thought
uv run alwm validate examples/v1/rubric.json rubric
uv run alwm validate examples/browser_evidence/v1/export_flow.json browser_evidence
```

## 3. Prompt registry

```bash
uv run alwm prompts check
uv run alwm prompts list
uv run alwm prompts show scaffold.echo.v1
```

## 4. Pipeline: ingest → evaluate → compare → report

Use committed dataset pages and rubric; write **only** under `$OUT` (replace with your temp dir).

```bash
OUT=$(mktemp -d)
export OUT

uv run alwm ingest examples/dataset/pages "$OUT/thoughts" --created-at 1970-01-01T00:00:00Z

uv run alwm evaluate \
  --subject examples/dataset/pages/retrieval-basics.md \
  --rubric examples/v1/rubric.json \
  --out "$OUT/retrieval-basics.eval.json" \
  --id eval-retrieval-basics

uv run alwm compare \
  examples/dataset/evals/retrieval-basics.eval.json \
  examples/dataset/evals/chunking-strategies.eval.json \
  --out "$OUT/wiki_matrix.json" \
  --out-md "$OUT/wiki_matrix.md" \
  --id wiki-matrix-walkthrough \
  --title "Walkthrough matrix"

uv run alwm report \
  --matrix "$OUT/wiki_matrix.json" \
  --out-json "$OUT/wiki_report.json" \
  --out-md "$OUT/wiki_report.md" \
  --id wiki-report-walkthrough

uv run alwm validate "$OUT/wiki_matrix.json" matrix
uv run alwm validate "$OUT/wiki_report.json" report

rm -rf "$OUT"
unset OUT
```

## 5. Benchmark run (offline / fixture mode)

```bash
BENCH=$(mktemp -d)
ALWM_FIXTURE_MODE=1 uv run alwm benchmark run \
  --definition fixtures/benchmarks/offline.v1.yaml \
  --output-dir "$BENCH" \
  --created-at 1970-01-01T00:00:00Z \
  --run-id walkthrough-offline

uv run alwm validate "$BENCH/manifest.json" benchmark_manifest
uv run alwm validate "$BENCH/cells/v-cli__p-one/benchmark_response.json" benchmark_response

rm -rf "$BENCH"
```

## 6. Benchmark manifest (committed example)

```bash
uv run alwm validate examples/v1/manifest.json benchmark_manifest
```

## 7. Optional: integration checks (not part of default CI)

Only when your machine has the right services or extras:

```bash
# Live Ollama / OpenAI-compatible benchmarks (skips if env/services missing)
uv run just verify-live-providers

# Playwright: requires uv pip install -e ".[browser]" && uv run playwright install chromium
uv run just verify-playwright-local
```

---

**Done.** You have exercised validation, the prompt registry, the full scoring pipeline, an offline benchmark run, and manifest validation using only paths shipped in the repo.
