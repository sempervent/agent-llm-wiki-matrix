# Example: browser evidence contrast (campaign output)

Generated with:

```bash
export ALWM_FIXTURE_MODE=1
uv run alwm benchmark campaign run \
  --definition examples/campaigns/v1/browser_evidence_compare.v1.yaml \
  --output-dir examples/campaign_runs/browser_evidence_compare \
  --created-at 1970-01-01T00:00:00Z
```

**Read first**

- `reports/campaign-report.md` — **Browser evidence (member runs)** includes **Cross-run contrast (deterministic fixtures)** comparing checkout (network + performance extensions) vs form validation (accessibility-focused) traces, then per-cell **signals** / **extension digest** tables.
- Member `reports/report.md` files — **Browser traces** sections use compact extension summaries (Playwright optional; MCP stdio is local-only per architecture docs).

This tree complements **`fixtures/benchmarks/browser_traces_compare.v1.yaml`** (single-run, two cells) by showing the same kind of contrast **across campaign members**.
