# Wiki: Benchmark campaign orchestration

**Campaigns** coordinate many benchmark harness runs from one **campaign definition** (YAML/JSON). Each member run is a normal benchmark output tree; the campaign root adds a **campaign manifest**, rollups, and optional **`alwm benchmark campaign run --dry-run`** planning without executing suites.

**Concept + workflow page:** [campaign-orchestration.md](campaign-orchestration.md).

## Canonical references

| Topic | Location |
| --- | --- |
| Concept + failure modes | [docs/wiki/campaign-orchestration.md](campaign-orchestration.md) |
| Workflow (CLI, fields, outputs, validation) | [docs/workflows/benchmark-campaigns.md](../workflows/benchmark-campaigns.md) |
| Architecture decision | [docs/adr/0001-campaign-orchestration.md](../adr/0001-campaign-orchestration.md) or [docs/architecture/adr/0001-benchmark-campaign-orchestration.md](../architecture/adr/0001-benchmark-campaign-orchestration.md) |
| Contract + tracking checklist | [docs/tracking/campaign-orchestration.md](../tracking/campaign-orchestration.md) |
| Example definitions | `examples/campaigns/v1/` |
| Sample output tree | `examples/campaign_runs/minimal_offline/` |

## Relationship to longitudinal reporting

Member runs are **`benchmark_manifest`** artifacts under `runs/runNNNN/`. Point **`alwm benchmark longitudinal`** at `runs/*/manifest.json` for cross-run analysis (see [longitudinal-reporting.md](../workflows/longitudinal-reporting.md)).
