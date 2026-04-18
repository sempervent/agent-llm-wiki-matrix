# Example benchmark campaigns

Campaign definitions describe **sweeps** over:

- One or more **benchmark suite** files (`suite_refs`)
- **Provider** YAML paths (`provider_config_refs`; empty means one run with harness defaults)
- **Eval scoring** options (`eval_scoring_options`; `null` entries keep each suite’s `eval_scoring`)
- Optional **execution mode** filters (`execution_modes`)
- Optional **browser** configs merged into `browser_mock` variants (`browser_configs`)

Run offline (default fixture mocks):

```bash
alwm benchmark campaign run \
  --definition examples/campaigns/v1/minimal_offline.v1.yaml \
  --output-dir examples/campaign_runs/minimal_offline
```

Plan only (no `runs/`; useful before large sweeps):

```bash
uv run alwm benchmark campaign run --dry-run \
  --definition examples/campaigns/v1/minimal_offline.v1.yaml \
  --output-dir /tmp/minimal_campaign_plan
```

Outputs (git-friendly, longitudinal-ready):

- `manifest.json` — campaign manifest (index of runs)
- `runs/runNNNN/manifest.json` — standard per-run benchmark manifests (omitted for `--dry-run`)
- `campaign-summary.json` / `campaign-summary.md` — aggregate table
- `campaign-semantic-summary.json` / `.md` — semantic/hybrid judge rollups (zero semantic cells when scoring is deterministic-only)
- `reports/campaign-report.md` / `campaign-analysis.json` — comparative report (dimensions, backends, instability, mode gaps, failure tags)
- `campaign-semantic-summary.json` / `campaign-semantic-summary.md` — semantic / hybrid repeat-judge variance by suite, provider, and execution mode (`alwm validate … campaign_semantic_summary`)
- `campaign-dry-run.json` — only for `--dry-run`: planned run count + `campaign_definition_fingerprint` + `campaign_experiment_fingerprints` (no `runs/` trees)

See `docs/workflows/benchmark-campaigns.md`, **`docs/workflows/campaign-walkthrough.md`** (committed `examples/campaign_runs/minimal_offline/`), `docs/wiki/campaign-orchestration.md`, `docs/wiki/benchmark-campaigns.md`, and `docs/tracking/campaign-orchestration.md`.
