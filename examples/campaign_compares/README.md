# Campaign comparisons (directory vs directory)

This example sits in the broader **publication workflow** — **[docs/workflows/campaign-result-pack-publication.md](../../docs/workflows/campaign-result-pack-publication.md)** (§5b) — alongside **pack** assembly and **`compare-packs`**.

Use **`alwm benchmark campaign compare`** to diff two **completed campaign output directories** (each has **`manifest.json`** at the root plus optional **`reports/campaign-analysis.json`**, **`campaign-semantic-summary.json`**, etc.). The command writes:

- **`campaign-compare.json`** — artifact kind **`campaign_compare`** (`schemas/v1/campaign_compare.schema.json`); includes optional **`reader_interpretation`** (non-causal summary for humans)
- **`campaign-compare-report.md`** — Markdown summary (**At a glance** first, then member overlap, manifest tables, **Analysis deltas**)

This is complementary to **`alwm benchmark campaign compare-packs`**, which compares **result packs** (`pack-compare.json`). Compare **raw campaigns** when you have two harness output trees and want a report without assembling packs.

Example (from the repo root, deterministic timestamp for reproducible JSON):

```bash
uv run alwm benchmark campaign compare \
  examples/campaign_runs/minimal_offline \
  examples/campaign_runs/multi_suite \
  -o examples/campaign_compares/minimal_offline_vs_multi_suite \
  --repo-root . \
  --created-at 1970-01-01T00:00:00Z
```

Validate:

```bash
uv run alwm validate examples/campaign_compares/minimal_offline_vs_multi_suite/campaign-compare.json campaign_compare
```

Full reference: **`docs/workflows/benchmark-campaigns.md`**. Tests: **`tests/test_campaign_directory_compare.py`**.
