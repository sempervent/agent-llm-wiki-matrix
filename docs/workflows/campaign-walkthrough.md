# Campaign walkthrough (committed examples only)

This walkthrough uses **only paths that exist in the repository**. You can validate artifacts and read fingerprints without regenerating anything. To reproduce a full sweep locally, use the same commands with a fresh `--output-dir` (see [benchmark-campaigns.md](benchmark-campaigns.md)).

## What you get from a campaign

| Output | Role |
| --- | --- |
| **Campaign manifest** (`manifest.json` at the campaign root) | Artifact kinds **`campaign_manifest`** or **`benchmark_campaign_manifest`**. Indexes all member runs, records **`campaign_definition_fingerprint`**, **`campaign_experiment_fingerprints`** (six campaign-level axes), timing, git fields, **`run_status_summary`**, **`inputs_snapshot`**, and per-row status plus **copied** **`comparison_fingerprints`** from each child run. |
| **Campaign summary** (`campaign-summary.json`, `campaign-summary.md`) | Kind **`campaign_summary`**. Rollup aligned with the manifest for dashboards; repeats **`campaign_experiment_fingerprints`** for quick audits. |
| **Member runs** (`runs/runNNNN/`) | Same layout as **`alwm benchmark run`**. Each **`manifest.json`** is a **`benchmark_manifest`** with **six-axis** **`comparison_fingerprints`** (`suite_definition`, `prompt_set`, `provider_config`, `scoring_config`, `browser_config`, `prompt_registry_state`). |

**Longitudinal compatibility:** downstream tools consume **`runs/*/manifest.json`**. The campaign root manifest is for **orchestration and experiment identity**, not a substitute for per-run benchmark manifests.

## Fingerprint axes (two levels)

**Benchmark run** (`comparison_fingerprints` on each `runs/runNNNN/manifest.json`):

- `suite_definition` — canonical suite YAML (title excluded)
- `prompt_set` — resolved prompts and text digests
- `provider_config` — per-variant provider blocks
- `scoring_config` — effective eval scoring + judge settings
- `browser_config` — per-variant browser blocks
- `prompt_registry_state` — effective registry YAML hash when `prompt_ref` is used (or a sentinel for inline-only)

**Campaign** (`campaign_experiment_fingerprints` on the campaign **`manifest.json`** and **`campaign-summary.json`**):

- `campaign_definition` — same digest as **`campaign_definition_fingerprint`** (identity of the sweep definition)
- `suite_definitions` — stacked suite definitions in the campaign
- `provider_configs` — provider YAML paths / nulls used in the sweep
- `scoring_configs` — eval scoring options axis
- `browser_configs` — browser override axis
- `prompt_registry_state` — campaign-level registry override (or effective registry state)

Use these to **group or filter** time series and to confirm two runs are comparable before interpreting score deltas (see [longitudinal-reporting.md](longitudinal-reporting.md)).

## Step 1 — Read the definition

Open the minimal offline campaign definition:

- `examples/campaigns/v1/minimal_offline.v1.yaml`

It points at one suite: `fixtures/benchmarks/campaign_micro.v1.yaml`. Larger committed definitions for multi-axis sweeps live beside it (`sweep_modes.v1.yaml`, `multi_suite.v1.yaml`).

## Step 2 — Inspect the committed output tree

The repo includes a full campaign output (not a dry-run):

- `examples/campaign_runs/minimal_offline/`

Layout:

```text
examples/campaign_runs/minimal_offline/
  manifest.json              # campaign manifest
  campaign-summary.json
  campaign-summary.md
  runs/run0000/
    manifest.json            # benchmark_manifest for member run 0
    cells/ … matrices/ …
```

## Step 3 — Validate artifacts

From the repository root:

```bash
uv run alwm validate examples/campaign_runs/minimal_offline/manifest.json campaign_manifest
uv run alwm validate examples/campaign_runs/minimal_offline/manifest.json benchmark_campaign_manifest
uv run alwm validate examples/campaign_runs/minimal_offline/campaign-summary.json campaign_summary
uv run alwm validate examples/campaign_runs/minimal_offline/runs/run0000/manifest.json benchmark_manifest
```

Both **`campaign_manifest`** and **`benchmark_campaign_manifest`** validate the same campaign **`manifest.json`** (registered aliases).

## Step 4 — Confirm fingerprints in JSON

Open **`examples/campaign_runs/minimal_offline/manifest.json`** and locate:

- **`campaign_definition_fingerprint`** — single canonical hash for the definition
- **`campaign_experiment_fingerprints`** — six keys listed above
- **`runs[0].comparison_fingerprints`** — six benchmark-level keys (member run)

Open **`examples/campaign_runs/minimal_offline/runs/run0000/manifest.json`** for the same member’s full **`comparison_fingerprints`** as written by the harness.

## Step 5 — Longitudinal analysis (glob on committed paths)

```bash
uv run alwm benchmark longitudinal \
  --runs-glob 'examples/campaign_runs/minimal_offline/runs/*/manifest.json' \
  --out-dir /tmp/campaign-longitudinal-from-repo
```

This uses the **member** benchmark manifests only; the campaign root manifest is optional context for your own notes or dashboards.

## Step 6 — Publish a result pack (optional)

To bundle a completed campaign into a **git-friendly** directory with **`INDEX.md`**, **`campaign-result-pack.json`**, and the same layout as a normal campaign tree (for sharing or archiving), use **`alwm benchmark campaign pack`**. See [benchmark-campaigns.md](benchmark-campaigns.md) (Result pack section) and the committed example **`examples/campaign_result_packs/minimal_offline/`**.

```bash
uv run alwm benchmark campaign pack examples/campaign_runs/minimal_offline \
  -o /tmp/my-pack \
  --pack-id minimal-offline \
  --source-label examples/campaign_runs/minimal_offline \
  --created-at 1970-01-01T00:00:00Z
```

## Optional — Re-run offline (writes new output)

To regenerate the same shape of tree in a temporary directory (does not modify committed examples):

```bash
export ALWM_FIXTURE_MODE=1
uv run alwm benchmark campaign run \
  --definition examples/campaigns/v1/minimal_offline.v1.yaml \
  --output-dir /tmp/minimal-campaign-rerun \
  --created-at 1970-01-01T00:00:00Z
```

Plan the sweep size without executing suites:

```bash
uv run alwm benchmark campaign run --dry-run \
  --definition examples/campaigns/v1/minimal_offline.v1.yaml \
  --output-dir /tmp/minimal-campaign-dry-run
```

Dry-run writes **`campaign-dry-run.json`** plus top-level manifest and summaries; it does **not** create **`runs/runNNNN/`**.

## See also

- [benchmark-campaigns.md](benchmark-campaigns.md) — full field reference, CLI table, and **result packs**
- [../wiki/campaign-orchestration.md](../wiki/campaign-orchestration.md) — concept, failure modes
- [../tracking/campaign-orchestration.md](../tracking/campaign-orchestration.md) — exit criteria and verification
- [../roadmap/v0.2.0.md](../roadmap/v0.2.0.md) — milestone context for fingerprints and campaigns
