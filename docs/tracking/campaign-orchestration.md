# Tracking: Campaign orchestration

**Status summary (2026-04-17):** **Complete** for default CI — schema-backed definitions and manifests, CLI `alwm benchmark campaign run` + `--dry-run`, artifact kinds `campaign_definition`, `campaign_manifest`, `campaign_summary`, tests (`tests/test_benchmark_campaign.py`), example tree `examples/campaign_runs/minimal_offline/`. **Partial:** automatic retry of failed cells per `retry_policy` (metadata only today). **Non-goals:** replacing `alwm benchmark run` internals; remote campaign execution without a checkout.

## Objective

Deliver **benchmark campaign orchestration** as a first-class, documented, schema-backed workflow so users can sweep suites × providers × scoring × browser configs with one **campaign manifest** and **summary** artifacts, while reusing **`run_benchmark`** for each member run.

## Scope

- `BenchmarkCampaignDefinitionV1` + `schemas/v1/benchmark_campaign.schema.json`
- `BenchmarkCampaignManifest` + `schemas/v1/benchmark_campaign_manifest.schema.json` (`campaign_definition_fingerprint`, `campaign_experiment_fingerprints`, timing, git provenance, run status, failures; member rows copy six-axis `comparison_fingerprints`)
- `CampaignSummaryV1` + `schemas/v1/campaign_summary.schema.json`
- `run_benchmark_campaign` in `benchmark/campaign_runner.py`; CLI `alwm benchmark campaign run` and `--dry-run`
- Artifact registration: `benchmark_campaign_*` and aliases `campaign_definition`, `campaign_manifest`, `campaign_summary`
- Longitudinal compatibility: `runs/*/manifest.json` glob

## Non-goals

- Replacing Docker/Compose for provider isolation
- Implicit network calls in default CI (offline fixture mode remains default)
- A separate `campaign plan` subcommand (use `run --dry-run`)

## Dependencies

- Benchmark harness (`run_benchmark`, benchmarks, matrices, reports)
- JSON Schema + Pydantic alignment (`artifacts.py`)
- `docs/workflows/benchmark-campaigns.md`, `docs/workflows/campaign-walkthrough.md`, `docs/wiki/campaign-orchestration.md`, ADR `docs/adr/0001-campaign-orchestration.md`

## Exit criteria

| Criterion | Evidence |
| --- | --- |
| Schema + models | `schemas/v1/benchmark_campaign*.json`, `campaign_summary.schema.json`; Pydantic models in `models.py` |
| CLI | `uv run alwm benchmark campaign run --help`; dry-run writes `campaign-dry-run.json` |
| Validation | `alwm validate … campaign_manifest` / `campaign_summary` on sample output |
| Tests | `tests/test_benchmark_campaign.py` passes; `uv run just ci` |
| Docs | README, AGENTS, workflows, wiki, ADR, CHANGELOG, implementation-log |

## Verification commands

```bash
uv run just ci
uv run alwm validate examples/campaign_runs/minimal_offline/manifest.json campaign_manifest
uv run alwm validate examples/campaign_runs/minimal_offline/campaign-summary.json campaign_summary
ALWM_FIXTURE_MODE=1 uv run alwm benchmark campaign run --dry-run \
  --definition examples/campaigns/v1/minimal_offline.v1.yaml --output-dir /tmp/campaign-dry
```

## Open questions

- Should `retry_policy` eventually drive automatic re-execution of failed cells? (Currently metadata.)

## Follow-up work

- Optional: Compose recipe for large sweeps on CI builders
- Optional: `--fail-fast` to stop after first member failure

## See also

- Older tracking filename: [benchmark-campaign-orchestration.md](benchmark-campaign-orchestration.md) (if present) — prefer this file as canonical.
