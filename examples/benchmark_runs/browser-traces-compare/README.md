# Example run: `bench.fixtures.browser.traces_compare.v1`

Offline benchmark with **two** `browser_mock` variants (checkout vs form-validation fixtures). Use it to inspect **browser evidence** sections in `reports/report.md` (summary table + legible DOM / screenshot / extension blocks).

Regenerate (from repo root):

```bash
uv run alwm benchmark run \
  --definition fixtures/benchmarks/browser_traces_compare.v1.yaml \
  --output-dir examples/benchmark_runs/browser-traces-compare/run
```

Then open `reports/report.md` under that output directory. No Playwright or MCP required; fixtures are under `fixtures/browser_evidence/v1/`.
