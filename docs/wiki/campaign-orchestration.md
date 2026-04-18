# Wiki: Campaign orchestration

**Campaign orchestration** is a first-class workflow for running **many benchmark harness executions** from one versioned **campaign definition** (YAML/JSON). It exists so sweeps across suites, providers, scoring backends, execution modes, and browser configs are **git-reviewable**, **schema-validated**, and **longitudinal-compatible**—not one-off shell loops.

## Purpose

| Goal | How campaigns help |
| --- | --- |
| **Reproducibility** | Definition + campaign manifest + per-run `manifest.json` pin inputs and outputs. |
| **Comparability** | Each member run is a normal `alwm benchmark run` tree; six-axis **`comparison_fingerprints`** propagate into campaign rows. |
| **Governance** | `campaign_definition_fingerprint`, **`campaign_experiment_fingerprints`** (six per-axis hashes), `inputs_snapshot`, optional git SHA/describe, and `run_status_summary` support audits and dashboards. |
| **Cost control** | **`alwm benchmark campaign run --dry-run`** plans the sweep (writes `campaign-dry-run.json`) without executing suites. |

## Data model (conceptual)

```text
CampaignDefinition (YAML)
    └── expands to N × (suite × provider × scoring × browser axis)
            └── each cell → run_benchmark(...) → runs/runNNNN/  (benchmark_manifest)
    └── campaign root → manifest.json (campaign_manifest)
                     → campaign-summary.json (campaign_summary)
                     → campaign-summary.md
```

- **Definition** (`BenchmarkCampaignDefinitionV1` / `campaign_definition`): what to sweep and metadata (owner, budgets, tags).
- **Campaign manifest** (`BenchmarkCampaignManifest` / `campaign_manifest`): aggregate index, timing, failures, fingerprints, pointers to member runs.
- **Campaign summary** (`CampaignSummaryV1` / `campaign_summary`): rollup JSON aligned with the manifest for tooling.

## Execution flow

1. **Load** the campaign definition; validate against JSON Schema + Pydantic.
2. **Compute** `campaign_definition_fingerprint` and **`campaign_experiment_fingerprints`** (canonical campaign identity plus per-axis hashes for suites, provider YAMLs, scoring and browser axes, and campaign registry override).
3. **Expand** the Cartesian product (skipping redundant browser axes when the suite has no `browser_mock` variants).
4. For each cell, **call** `run_benchmark` (no duplicated scoring/matrix logic); record duration, status, and failure message on error.
5. **Write** campaign manifest, summary JSON/Markdown, and optional `campaign-dry-run.json` when `--dry-run` (dry-run JSON includes the same fingerprint fields as a full run’s top-level manifest).

## CLI (exact)

```bash
# Full sweep (offline)
export ALWM_FIXTURE_MODE=1
uv run alwm benchmark campaign run \
  --definition examples/campaigns/v1/minimal_offline.v1.yaml \
  --output-dir examples/campaign_runs/minimal_offline

# Plan only
uv run alwm benchmark campaign run --dry-run \
  --definition examples/campaigns/v1/minimal_offline.v1.yaml \
  --output-dir /tmp/plan
```

## Failure modes

| Symptom | Likely cause | Mitigation |
| --- | --- | --- |
| `No variants left after execution_modes filter` | `execution_modes` too strict for a suite | Widen the list or drop suites that lack those modes. |
| `provider_config_ref not found` | Path not relative to repo root | Fix YAML path or symlink. |
| Member run `status: failed` | Harness exception (provider, browser, schema) | Read `runs/runNNNN/campaign_run_error.json` and the benchmark cell logs. |
| Huge disk use | Large Cartesian product | Use `--dry-run` first; reduce `suite_refs` or axes. |

## Canonical references

| Topic | Location |
| --- | --- |
| Step-by-step walkthrough (committed `examples/`) | [docs/workflows/campaign-walkthrough.md](../workflows/campaign-walkthrough.md) |
| Workflow & command table | [docs/workflows/benchmark-campaigns.md](../workflows/benchmark-campaigns.md) |
| Tracking & exit criteria | [docs/tracking/campaign-orchestration.md](../tracking/campaign-orchestration.md) |
| ADR (decision) | [docs/adr/0001-campaign-orchestration.md](../adr/0001-campaign-orchestration.md) |
| Architecture ADR (alternate path) | [docs/architecture/adr/0001-benchmark-campaign-orchestration.md](../architecture/adr/0001-benchmark-campaign-orchestration.md) |
| Benchmark workflow parent | [docs/workflows/benchmarking.md](../workflows/benchmarking.md) |

## Relationship to longitudinal reporting

Member runs expose **`benchmark_manifest`** under `runs/runNNNN/` (with **six-axis** **`comparison_fingerprints`**). Point **`alwm benchmark longitudinal`** at `runs/*/manifest.json` (see [longitudinal-reporting.md](../workflows/longitudinal-reporting.md)). The **campaign** manifest’s **`campaign_experiment_fingerprints`** group the sweep for audits; longitudinal series grouping also keys off fingerprint fields documented in that workflow.
