# Audit: schema ↔ runtime drift (benchmark & campaign artifacts)

**Date:** 2026-04-18 (updated 2026-04-18 — expanded drift sweep)  
**Method:** Deterministic validation only — `load_artifact_file` / `parse_artifact` for registered kinds against JSON Schema + Pydantic (`src/agent_llm_wiki_matrix/artifacts.py`).

## Scope

| Area | JSON Schema | Notes |
| --- | --- | --- |
| Benchmark run index | `schemas/v1/manifest.schema.json` | **`runtime_summary`** (`benchmarkRunTimingSummary`), **`retry_summary`** (`benchmarkRetrySummary`), **`cells[].runtime`** (`benchmarkCellRuntime`), **`comparison_fingerprints`** (six axes including **`prompt_registry_state`**) |
| Campaign index | `schemas/v1/benchmark_campaign_manifest.schema.json` | **`generated_report_paths`** (includes **`campaign_semantic_summary_*`**, comparative report paths), **`aggregated_runtime`** |
| Campaign semantic rollup | `schemas/v1/campaign_semantic_summary.schema.json` | Written when campaigns complete; deterministic-only runs may show **zero** semantic cells |
| Campaign result pack | `schemas/v1/campaign_result_pack.schema.json` | **`examples/campaign_result_packs/**`** |
| Browser evidence | `schemas/v1/browser_evidence.schema.json` | Optional **`dom_excerpts`**, **`screenshots`**, **`extensions`** |
| Cell I/O | `benchmark_request`, `benchmark_response`, `evaluation`, `evaluation_judge_provenance` | Committed under benchmark/campaign run trees |
| Reports & matrices | `report`, `matrix`, `matrix_grid_inputs`, `matrix_pairwise_inputs` | **`reports/report.json`**, **`matrices/*.json`** under run outputs |
| Rubrics | `rubric` | **`examples/dataset/rubrics/*.json`** |

Full filename → kind inventory and explicit non-goals: **[schema-drift-contracts-inventory.md](schema-drift-contracts-inventory.md)**.

## Evidence

1. **Repository trees:** **`tests/test_schema_drift_contracts.py`** sweeps **`examples/`** and **`fixtures/`** for the filenames in the inventory (including emitted campaign outputs under **`examples/campaign_runs/`** and **`examples/campaign_result_packs/`**).
2. **Local build outputs:** Ephemeral directories such as **`out/`** (e.g. Compose **`benchmark-offline`**) may contain **older** `manifest.json` files (e.g. five-axis **`comparison_fingerprints`**). Those are **not** committed; re-run the benchmark or delete **`out/`** to regenerate. **Do not** treat uncommitted trees as contract sources.
3. **Focused regression tests:** Example campaign member manifest parses **`runtime_summary`**, **`retry_summary`**, and **`cells[].runtime`**; campaign root manifest parses **`generated_report_paths`** and **`campaign-semantic-summary.json`**.

## Conclusion

Committed **examples/** and **fixtures/** stay aligned with current schemas; CI fails on drift. Use **`just validate-artifacts`** for a fast, contract-only run.

## Verification commands

```bash
just validate-artifacts
```

```bash
uv run pytest tests/test_schema_drift_contracts.py -v
```

Full pipeline:

```bash
uv run just ci
```
