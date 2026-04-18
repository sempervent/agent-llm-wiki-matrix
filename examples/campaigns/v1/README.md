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

**Multi-suite sweep** (two fixture definitions; shows **suite_ref** variance in comparative **At a glance** and member-score tables):

```bash
uv run alwm benchmark campaign run \
  --definition examples/campaigns/v1/multi_suite.v1.yaml \
  --output-dir examples/campaign_runs/multi_suite
```

**Browser evidence contrast** (two browser-heavy suites — checkout vs form fixtures; **Cross-run contrast** + signal digests in `reports/campaign-report.md`):

```bash
export ALWM_FIXTURE_MODE=1
uv run alwm benchmark campaign run \
  --definition examples/campaigns/v1/browser_evidence_compare.v1.yaml \
  --output-dir examples/campaign_runs/browser_evidence_compare \
  --created-at 1970-01-01T00:00:00Z
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
- `reports/campaign-report.md` / `campaign-analysis.json` — comparative report (**At a glance**, dimensions, member-run mean scores by axis, fingerprint comparison when applicable, backends, instability, mode gaps, failure tags)
- `campaign-semantic-summary.json` / `campaign-semantic-summary.md` — semantic / hybrid repeat-judge variance by suite, provider, and execution mode (`alwm validate … campaign_semantic_summary`)
- `campaign-dry-run.json` — only for `--dry-run`: planned run count + `campaign_definition_fingerprint` + `campaign_experiment_fingerprints` (no `runs/` trees)

See `docs/workflows/benchmark-campaigns.md`, **`docs/workflows/campaign-walkthrough.md`** (committed `examples/campaign_runs/minimal_offline/`), `docs/wiki/campaign-orchestration.md`, `docs/wiki/benchmark-campaigns.md`, and `docs/tracking/campaign-orchestration.md`.

For **fingerprint-axis** comparative tables (`reports/campaign-report.md`), see `fingerprint_axes_probe.v1.yaml` (two runs that differ on **scoring_config** fingerprints).
