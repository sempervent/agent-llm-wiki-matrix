# Campaign summary: `campaign.examples.browser_evidence_compare.v1`

- **title:** Example — browser evidence contrast (checkout vs form fixtures)
- **created_at:** `1970-01-01T00:00:00Z`
- **definition:** `examples/campaigns/v1/browser_evidence_compare.v1.yaml`
- **definition_fingerprint:** `sha256:781642c343722637e819c84c11296d4fab2cd91be75102df3f1f743211ae6b76`

## Experiment fingerprints (axes)

Stable per-axis hashes for longitudinal grouping and comparability checks.

- **campaign_definition:** `sha256:781642c343722637e819c84c11296d4fab2cd91be75102df3f1f743211ae6b76`
- **suite_definitions:** `sha256:3516abc8cd145dfb87d0d3bf89f2e1a6b02bbdab7a091b80fcb808a1953faffc`
- **provider_configs:** `sha256:69c4ef3c9876f8d46bd609d755baa1bb850cd8d9fdcbdee0748b6e10c36cf5f1`
- **scoring_configs:** `sha256:2c7f1b6d79305cde67076936152d80992802d413157de43143bac86c13c21fc8`
- **browser_configs:** `sha256:591cbc3aa572200862e2f336261f05849fe93c17d226a939565815d0cb075961`
- **prompt_registry_state:** `sha256:d409ed75b3cb355ac6727f09877d7ef98c40adce16e3e8284c6dcfe9c5c3db21`
- **fixture_mode_force_mock:** `True`
- **dry_run:** `False`
- **runs:** 2
- **succeeded / failed:** 2 / 0
- **git_commit:** `148517589c625e7fc468c35311d0bcd6939462bd`
- **git_describe:** `v0.2.2-dirty`

## Aggregated runtime (member manifests)

Sums of per-run `runtime_summary` fields for successful member runs that recorded timing.

| Metric | Value |
| --- | --- |
| member_runs_timed | 2 |
| total_browser_phase_seconds | 0.012477 |
| total_provider_completion_seconds | 0.000040 |
| total_evaluation_phase_seconds | 0.004552 |
| total_judge_phase_seconds | 0.000000 |
| total_judge_invocations | 0 |
| cells_with_judge_parse_fallback | 0 |


## At a glance

Mean-score spreads, backends, semantic instability, mode gaps, and **FT-*** tags. Details: **`reports/campaign-report.md`**; judge variance: **`campaign-semantic-summary.md`**.

### Mean score — best / worst by sweep axis

- **`browser_config_applied`:** Single distinct value on this axis — no best/worst spread.
- **`eval_scoring_label`:** Single distinct value on this axis — no best/worst spread.
- **`execution_modes_filter`:** Single distinct value on this axis — no best/worst spread.
- **`provider_config_ref`:** Single distinct value on this axis — no best/worst spread.
- **`suite_ref`:** best `fixtures/benchmarks/browser_checkout.v1.yaml` (0.571024), worst `fixtures/benchmarks/browser_form.v1.yaml` (0.361310), spread **0.209714**
_`benchmark_id` tracks `suite_ref` here (same grouping); see comparative report for the full dimension table._

### Provider / backend (mean cell score)

- **Best:** `mock` (0.466167 over 2 cells)
- **Weakest:** _single backend kind in this campaign._

### Semantic instability hotspots (longitudinal)

_No cells flagged as semantically unstable at configured thresholds._

### Execution mode gaps (within-run)

_No mode-gap rows above threshold, or modes not comparable in member runs._

### Top recurring failure tags (FT-*)

- `FT-ABS-LOW`×1

### Judge confidence & repeat disagreement (rollup)

- **Low-confidence (merged):** 0 — judge 0, repeat 0
- **Repeat-judge cells (N>1):** 0; **max range:** —


### Semantic / hybrid judge — axis hotspots (rollup)

_All cells used deterministic scoring — no judge variance rollups._
---
| # | run_id | suite | benchmark_id | eval axis | modes filter | status | mean score | cells |
| ---: | --- | --- | --- | --- | --- | --- | ---: | ---: |
| 0 | `campaign.examples.browser_evidence_compare.v1__0000` | `fixtures/benchmarks/browser_checkout.v1.yaml` | `bench.fixtures.browser.checkout.v1` | suite_default | — | succeeded | 0.571024 | 1 |
| 1 | `campaign.examples.browser_evidence_compare.v1__0001` | `fixtures/benchmarks/browser_form.v1.yaml` | `bench.fixtures.browser.form.v1` | suite_default | — | succeeded | 0.361310 | 1 |

## Comparative reports

- **Markdown:** `reports/campaign-report.md` (dimensions, backends, scoring instability, mode gaps, failure tags)
- **JSON:** `reports/campaign-analysis.json` (machine-readable mirror)

### Semantic / hybrid judge rollup

- **Markdown:** `campaign-semantic-summary.md` (repeat-judge disagreement, low-confidence cells; variance by suite / provider / mode)
- **JSON:** `campaign-semantic-summary.json` (structured aggregates)

## Longitudinal analysis

Each successful row is a standard benchmark run directory. Point longitudinal tooling at ``runs/*/manifest.json`` under this campaign root (see ``docs/workflows/longitudinal-reporting.md``).
