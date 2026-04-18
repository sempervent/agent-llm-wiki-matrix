# Campaign summary: `campaign.examples.minimal_offline.v1`

- **title:** Minimal offline campaign (single suite, deterministic)
- **created_at:** `1970-01-01T00:00:00Z`
- **definition:** `examples/campaigns/v1/minimal_offline.v1.yaml`
- **definition_fingerprint:** `sha256:340780556158635e0b33298b726f530cbc86f7dcfdd8923934bbb14a0734e47b`

## Experiment fingerprints (axes)

Stable per-axis hashes for longitudinal grouping and comparability checks.

- **campaign_definition:** `sha256:340780556158635e0b33298b726f530cbc86f7dcfdd8923934bbb14a0734e47b`
- **suite_definitions:** `sha256:89fed34c06b5afbe00f18b22f21c268389fdf928f73f446796d8c19666514348`
- **provider_configs:** `sha256:69c4ef3c9876f8d46bd609d755baa1bb850cd8d9fdcbdee0748b6e10c36cf5f1`
- **scoring_configs:** `sha256:2c7f1b6d79305cde67076936152d80992802d413157de43143bac86c13c21fc8`
- **browser_configs:** `sha256:591cbc3aa572200862e2f336261f05849fe93c17d226a939565815d0cb075961`
- **prompt_registry_state:** `sha256:d409ed75b3cb355ac6727f09877d7ef98c40adce16e3e8284c6dcfe9c5c3db21`
- **fixture_mode_force_mock:** `True`
- **dry_run:** `False`
- **runs:** 1
- **succeeded / failed:** 1 / 0
- **git_commit:** `148517589c625e7fc468c35311d0bcd6939462bd`
- **git_describe:** `v0.2.2-dirty`

## Aggregated runtime (member manifests)

Sums of per-run `runtime_summary` fields for successful member runs that recorded timing.

| Metric | Value |
| --- | --- |
| member_runs_timed | 1 |
| total_browser_phase_seconds | 0.000000 |
| total_provider_completion_seconds | 0.000031 |
| total_evaluation_phase_seconds | 0.002095 |
| total_judge_phase_seconds | 0.000000 |
| total_judge_invocations | 0 |
| cells_with_judge_parse_fallback | 0 |


## At a glance

Quick read on **mean-score spreads** across sweep axes, **backend** leaders, **semantic instability** (when longitudinal analysis ran), **execution-mode gaps**, and **failure taxonomy** signals. See **`reports/campaign-report.md`** for the full comparative narrative and **`campaign-semantic-summary.md`** for judge-variance rollups.

### Mean score — best / worst by sweep axis

- Need at least two succeeded member runs with mean scores to compare axes.

### Provider / backend (mean cell score)

- **Best:** `mock` (0.667276 over 1 cells)
- **Weakest:** _single backend kind in this campaign._

### Semantic instability hotspots (longitudinal)

_No cells flagged as semantically unstable at configured thresholds._

### Execution mode gaps (within-run)

_No mode-gap rows above threshold, or modes not comparable in member runs._

### Top recurring failure tags (FT-*)

_No FT-* signals in this pass._

### Judge confidence & repeat disagreement (rollup)

- **Low-confidence cells (merged):** 0 (`Evaluation.judge_low_confidence`: 0, repeat `confidence.low_confidence`: 0)
- **Repeat judge cells (N>1):** 0
- **Max range (campaign):** —


### Semantic / hybrid judge — axis hotspots (rollup)

_All cells used deterministic scoring — no judge variance rollups._
---
| # | run_id | suite | benchmark_id | eval axis | modes filter | status | mean score | cells |
| ---: | --- | --- | --- | --- | --- | --- | ---: | ---: |
| 0 | `campaign.examples.minimal_offline.v1__0000` | `fixtures/benchmarks/campaign_micro.v1.yaml` | `bench.fixtures.campaign.micro.v1` | suite_default | — | succeeded | 0.667276 | 1 |

## Comparative reports

- **Markdown:** `reports/campaign-report.md` (dimensions, backends, scoring instability, mode gaps, failure tags)
- **JSON:** `reports/campaign-analysis.json` (machine-readable mirror)

### Semantic / hybrid judge rollup

- **Markdown:** `campaign-semantic-summary.md` (repeat-judge disagreement, low-confidence cells; variance by suite / provider / mode)
- **JSON:** `campaign-semantic-summary.json` (structured aggregates)

## Longitudinal analysis

Each successful row is a standard benchmark run directory. Point longitudinal tooling at ``runs/*/manifest.json`` under this campaign root (see ``docs/workflows/longitudinal-reporting.md``).
