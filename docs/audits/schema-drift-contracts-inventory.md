# Audit: committed artifact drift risk (examples / fixtures / emitted campaign outputs)

**Date:** 2026-04-18  
**Method:** Deterministic **`load_artifact_file`** — each file is validated with **JSON Schema** then **Pydantic** (`src/agent_llm_wiki_matrix/artifacts.py`).

## Canonical verification

See **[docs/workflows/verification.md](../workflows/verification.md)** for how **`just validate-artifacts`** relates to **`just ci`** and **`uv run`** fallbacks.

```bash
uv run just validate-artifacts
```

Equivalent (no `just`):

```bash
uv run pytest tests/test_schema_drift_contracts.py -v
```

**Full CI** still runs the default suite (**`uv run just ci`**), which includes this module as part of **`pytest tests/ --ignore=tests/integration`**.

## Sweep coverage (by filename / path)

| Artifact / surface | `alwm` kind(s) | Drift risk if unchecked |
| --- | --- | --- |
| **`manifest.json`** (classified) | `benchmark_manifest` or `benchmark_campaign_manifest` | Run vs campaign manifests diverge from **`manifest.schema.json`** / **`benchmark_campaign_manifest.schema.json`**; **fingerprints**, **runtime**, **cells** shape drift. |
| **`campaign-summary.json`** | `campaign_summary` | Campaign rollup fields vs **`campaign_summary.schema.json`**. |
| **`campaign-semantic-summary.json`** | `campaign_semantic_summary` | Semantic rollups, **criterion_instability**, **instability_highlights** vs schema. |
| **`campaign-result-pack.json`** | `campaign_result_pack` | Pack metadata and **artifacts** paths vs **`campaign_result_pack.schema.json`**. |
| **`browser_evidence.json`** | `browser_evidence` | DOM / screenshot / extensions vs **`browser_evidence.schema.json`**. |
| **`evaluation.json`** | `evaluation` | Scoring backend, judge provenance refs vs **`evaluation.schema.json`**. |
| **`benchmark_response.json`** | `benchmark_response` | Provider output contract vs **`benchmark_response.schema.json`**. |
| **`benchmark_request.json`** | `benchmark_request` | Request record vs **`benchmark_request.schema.json`**. |
| **`evaluation_judge_provenance.json`** | `evaluation_judge_provenance` | Repeat-judge payloads vs **`evaluation_judge_provenance.schema.json`**. |
| **`reports/report.json`** | `report` | Report JSON vs **`report.schema.json`**. |
| **`matrices/pairwise.json`**, **`matrices/grid.json`** | `matrix` | Matrix shape vs **`matrix.schema.json`**. |
| **`matrices/*.row_inputs.json`** | `matrix_grid_inputs` / `matrix_pairwise_inputs` | Row-input bundles vs respective schemas. |
| **`examples/dataset/rubrics/*.json`** | `rubric` | Rubric docs vs **`rubric.schema.json`**. |

## Not covered by this sweep (by design)

| Path / JSON | Reason |
| --- | --- |
| **`reports/campaign-analysis.json`** | Machine-readable comparative bundle; **not** a registered **`alwm validate`** kind (schema versioned object in-repo). Validate via targeted tests / future kind. |
| **`summary.json`** (e.g. longitudinal sample output) | Longitudinal bundle summary; **not** mapped to a single **`artifacts.py`** kind today. |
| **Ephemeral `out/`**, local Compose outputs | Not committed; regenerate or delete stale trees. |
| **`benchmark_run_context`** | No committed **`benchmark_run_context.json`** files in **`examples/`** / **`fixtures/`** yet; add a glob when fixtures exist. |

## Classification rule (`manifest.json`)

- **`benchmark_campaign_manifest`**: `schema_version == 1`, **`campaign_id`** + **`runs`**, no top-level **`benchmark_id`**.
- **`benchmark_manifest`**: `schema_version == 1`, **`benchmark_id`** + **`cells`**.

Unclassified manifests under **`examples/`** / **`fixtures/`** fail the test (forces explicit handling).

## See also

- **[v0.2.4-publication-workflow-audit.md](v0.2.4-publication-workflow-audit.md)** — end-to-end publication readiness; prioritizes **`campaign-analysis.json`** contract options vs this inventory.
- **[schema-runtime-hardening-2026-04-18.md](schema-runtime-hardening-2026-04-18.md)** — earlier hardening notes.
- **`docs/implementation-log.md`** — changelog of contract tests.
