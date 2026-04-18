# Campaign summary: `campaign.examples.multi_suite.v1`

- **title:** Example — multi-suite sweep (two fixtures)
- **created_at:** `1970-01-01T00:00:00Z`
- **definition:** `examples/campaigns/v1/multi_suite.v1.yaml`
- **definition_fingerprint:** `sha256:98d0b9852fa277dc5b164fe14a3711b50be2a72ea5f5fca5ed0dd09fe8072566`

## Experiment fingerprints (axes)

Stable per-axis hashes for longitudinal grouping and comparability checks.

- **campaign_definition:** `sha256:98d0b9852fa277dc5b164fe14a3711b50be2a72ea5f5fca5ed0dd09fe8072566`
- **suite_definitions:** `sha256:d2b3773206bf3494af78922b52603f56a48e60aea74a7f40998fc98adbafbeca`
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
| total_browser_phase_seconds | 0.000523 |
| total_provider_completion_seconds | 0.000418 |
| total_evaluation_phase_seconds | 0.195920 |
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
- **`suite_ref`:** best `fixtures/benchmarks/campaign_micro.v1.yaml` (0.667276), worst `fixtures/benchmarks/offline.v1.yaml` (0.367251), spread **0.300025**
_`benchmark_id` tracks `suite_ref` here (same grouping); see comparative report for the full dimension table._

### Provider / backend (mean cell score)

- **Best:** `mock` (0.410112 over 7 cells)
- **Weakest:** _single backend kind in this campaign._

### Semantic instability hotspots (longitudinal)

_No cells flagged as semantically unstable at configured thresholds._

### Execution mode gaps (within-run)

- **`campaign.examples.multi_suite.v1__0001`** / `p-one` — spread **0.7782** (browser_mock=0.3062, cli=0.8439, repo_governed=0.0657)
- **`campaign.examples.multi_suite.v1__0001`** / `p-two` — spread **0.5458** (browser_mock=0.6521, cli=0.1063, repo_governed=0.2295)

### Top recurring failure tags (FT-*)

- `FT-ABS-LOW`×4, `FT-MODE-GAP`×2

### Judge confidence & repeat disagreement (rollup)

- **Low-confidence (merged):** 0 — judge 0, repeat 0
- **Repeat-judge cells (N>1):** 0; **max range:** —


### Semantic / hybrid judge — axis hotspots (rollup)

_All cells used deterministic scoring — no judge variance rollups._
---
| # | run_id | suite | benchmark_id | eval axis | modes filter | status | mean score | cells |
| ---: | --- | --- | --- | --- | --- | --- | ---: | ---: |
| 0 | `campaign.examples.multi_suite.v1__0000` | `fixtures/benchmarks/campaign_micro.v1.yaml` | `bench.fixtures.campaign.micro.v1` | suite_default | — | succeeded | 0.667276 | 1 |
| 1 | `campaign.examples.multi_suite.v1__0001` | `fixtures/benchmarks/offline.v1.yaml` | `bench.offline.v1` | suite_default | — | succeeded | 0.367251 | 6 |

## Comparative reports

- **Markdown:** `reports/campaign-report.md` (dimensions, backends, scoring instability, mode gaps, failure tags)
- **JSON:** `reports/campaign-analysis.json` (machine-readable mirror)

### Semantic / hybrid judge rollup

- **Markdown:** `campaign-semantic-summary.md` (repeat-judge disagreement, low-confidence cells; variance by suite / provider / mode)
- **JSON:** `campaign-semantic-summary.json` (structured aggregates)

## Longitudinal analysis

Each successful row is a standard benchmark run directory. Point longitudinal tooling at ``runs/*/manifest.json`` under this campaign root (see ``docs/workflows/longitudinal-reporting.md``).
