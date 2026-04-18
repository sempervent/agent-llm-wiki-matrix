# Tracking: Benchmark campaign orchestration

**Canonical tracking file:** [campaign-orchestration.md](campaign-orchestration.md) — prefer that document for objective, exit criteria, and verification commands.

**Purpose:** Track contract surface, CLI, and documentation for **first-class** benchmark campaign orchestration (definitions, manifests, summaries, validation).

**Status:** **Active** — aligned with `docs/architecture/adr/0001-benchmark-campaign-orchestration.md` and `docs/adr/0001-campaign-orchestration.md`.

## Contracts

| Artifact | JSON Schema | Pydantic | `alwm validate` kind(s) |
| --- | --- | --- | --- |
| Campaign definition | `schemas/v1/benchmark_campaign.schema.json` | `BenchmarkCampaignDefinitionV1` | `benchmark_campaign_definition`, `campaign_definition` (load via `load_benchmark_campaign_definition` for YAML) |
| Campaign manifest (output) | `schemas/v1/benchmark_campaign_manifest.schema.json` | `BenchmarkCampaignManifest` | `benchmark_campaign_manifest`, `campaign_manifest` (includes `campaign_experiment_fingerprints` + member `comparison_fingerprints`) |
| Campaign summary (output) | `schemas/v1/campaign_summary.schema.json` | `CampaignSummaryV1` | `campaign_summary` |

Registration: `src/agent_llm_wiki_matrix/artifacts.py`.

## CLI

| Command | Role |
| --- | --- |
| `alwm benchmark campaign run` | Execute sweep; write `manifest.json`, `runs/runNNNN/`, `campaign-summary.json`, `campaign-summary.md` |
| `alwm benchmark campaign run --dry-run` | Plan sweep only: same top-level artifacts except **no** member `runs/`; writes `campaign-dry-run.json` with planned count |

## Tests (default suite)

- `tests/test_benchmark_campaign.py` — definition load, full run tree, dry-run plan path

## Docs map

| Doc | Role |
| --- | --- |
| [docs/workflows/benchmark-campaigns.md](../workflows/benchmark-campaigns.md) | How-to |
| [docs/wiki/benchmark-campaigns.md](../wiki/benchmark-campaigns.md) | Wiki index |
| [README.md](../../README.md) | Quick reference |
| [AGENTS.md](../../AGENTS.md) | Contribution expectations for campaign changes |

## Change checklist

When changing campaign behavior or contracts:

1. Schema + Pydantic + `artifacts.py` (if kinds change)
2. `tests/test_benchmark_campaign.py` (or new tests)
3. `docs/workflows/benchmark-campaigns.md`, wiki, this file if scope shifts
4. `CHANGELOG.md`, `docs/implementation-log.md`
5. ADR if the decision changes materially
