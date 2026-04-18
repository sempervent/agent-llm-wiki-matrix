# Example longitudinal reports

This directory holds **sample outputs** from `alwm benchmark longitudinal` so reviewers can see the Markdown shape without running the tool.

- **`sample-output/`** — `weekly.md`, `longitudinal.md`, `regression.md`, `provider-comparison.md` (includes **`comparison_fingerprints`** from each run manifest), `failure-atlas.md`, `failure-taxonomy.md`, and `summary.json` (includes **`comparison_fingerprints_by_run`**) produced from `fixtures/longitudinal/paired/*/manifest.json`.

Regenerate (from repo root):

```bash
alwm benchmark longitudinal \
  --runs-glob 'fixtures/longitudinal/paired/*/manifest.json' \
  --out-dir examples/reports/longitudinal/sample-output
```

See `docs/workflows/longitudinal-reporting.md` for options and taxonomy details.
