# End-to-end walkthrough (v0.1.0, committed examples only)

This walkthrough runs entirely from the **repository checkout**. Inputs are under **`examples/`** and **`fixtures/`**; generated files go to a **temporary directory** so the working tree stays clean.

**Prerequisites:** Python **3.11+**, [just](https://github.com/casey/just), repo root as current working directory.

## 1. Environment and sanity checks

```bash
python3.11 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

alwm version    # expect: 0.1.0
alwm info
just ci
```

## 2. Validate example artifacts

```bash
alwm validate examples/v1/thought.json thought
alwm validate examples/v1/rubric.json rubric
alwm validate examples/browser_evidence/v1/export_flow.json browser_evidence
```

## 3. Prompt registry

```bash
alwm prompts check
alwm prompts list
alwm prompts show scaffold.echo.v1
```

## 4. Pipeline: ingest → evaluate → compare → report

Use committed dataset pages and rubric; write **only** under `$OUT` (replace with your temp dir).

```bash
OUT=$(mktemp -d)
export OUT

alwm ingest examples/dataset/pages "$OUT/thoughts" --created-at 1970-01-01T00:00:00Z

alwm evaluate \
  --subject examples/dataset/pages/retrieval-basics.md \
  --rubric examples/v1/rubric.json \
  --out "$OUT/retrieval-basics.eval.json" \
  --id eval-retrieval-basics

alwm compare \
  examples/dataset/evals/retrieval-basics.eval.json \
  examples/dataset/evals/chunking-strategies.eval.json \
  --out "$OUT/wiki_matrix.json" \
  --out-md "$OUT/wiki_matrix.md" \
  --id wiki-matrix-walkthrough \
  --title "Walkthrough matrix"

alwm report \
  --matrix "$OUT/wiki_matrix.json" \
  --out-json "$OUT/wiki_report.json" \
  --out-md "$OUT/wiki_report.md" \
  --id wiki-report-walkthrough

alwm validate "$OUT/wiki_matrix.json" matrix
alwm validate "$OUT/wiki_report.json" report

rm -rf "$OUT"
unset OUT
```

## 5. Benchmark run (offline / fixture mode)

```bash
BENCH=$(mktemp -d)
ALWM_FIXTURE_MODE=1 alwm benchmark run \
  --definition fixtures/benchmarks/offline.v1.yaml \
  --output-dir "$BENCH" \
  --created-at 1970-01-01T00:00:00Z \
  --run-id walkthrough-offline

alwm validate "$BENCH/manifest.json" benchmark_manifest
alwm validate "$BENCH/cells/v-cli__p-one/benchmark_response.json" benchmark_response

rm -rf "$BENCH"
```

## 6. Benchmark manifest (committed example)

```bash
alwm validate examples/v1/manifest.json benchmark_manifest
```

## 7. Optional: integration checks (not part of default CI)

Only when your machine has the right services or extras:

```bash
# Live Ollama / OpenAI-compatible benchmarks (skips if env/services missing)
just verify-live-providers

# Playwright: requires pip install -e ".[browser]" && playwright install chromium
just verify-playwright-local
```

---

**Done.** You have exercised validation, the prompt registry, the full scoring pipeline, an offline benchmark run, and manifest validation using only paths shipped in the repo.
