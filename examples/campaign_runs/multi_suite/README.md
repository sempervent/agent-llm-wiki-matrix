# Example: multi-suite campaign output

Generated with:

```bash
export ALWM_FIXTURE_MODE=1
uv run alwm benchmark campaign run \
  --definition examples/campaigns/v1/multi_suite.v1.yaml \
  --output-dir examples/campaign_runs/multi_suite \
  --created-at 1970-01-01T00:00:00Z
```

**Read first**

- `campaign-summary.md` — **Snapshot digest** (mean-score spreads, backends, instability, mode gaps, FT-* tags) plus **Member run index**.
- `reports/campaign-report.md` — comparative narrative with **Executive summary** at the top, member mean tables, fingerprint axes, and full failure atlas.
- `reports/campaign-analysis.json` — machine-readable mirror (`mean_score_extremes_by_sweep_axis`, thresholds, fingerprint blocks).
- `campaign-semantic-summary.{md,json}` — judge-variance rollups (deterministic-only runs show totals with empty hotspots).

This tree exists to document **multi-run** campaign reporting (two distinct `suite_ref` values). See `docs/workflows/benchmark-campaigns.md`.
