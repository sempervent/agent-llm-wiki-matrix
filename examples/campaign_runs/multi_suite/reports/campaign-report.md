# Campaign comparative report: `campaign.examples.multi_suite.v1`

Aggregates **succeeded** member runs under this campaign directory. Regression-style **`FT-*`** signals use the same taxonomy as longitudinal analysis (adjacent run order in the campaign manifest when the same benchmark cell appears in multiple runs). Within-run mode gaps and judge instability apply per snapshot.

## At a glance

- **Varied sweep axes:** `benchmark_id`, `suite_ref`.

### Mean member score — best / worst by axis

- **`benchmark_id`:** best `bench.fixtures.campaign.micro.v1` (0.667276, n=1), worst `bench.offline.v1` (0.367251, n=1), spread **0.300025**
- **`browser_config_applied`:** _not comparable_ — Single distinct value on this axis — no best/worst spread.
- **`eval_scoring_label`:** _not comparable_ — Single distinct value on this axis — no best/worst spread.
- **`execution_modes_filter`:** _not comparable_ — Single distinct value on this axis — no best/worst spread.
- **`provider_config_ref`:** _not comparable_ — Single distinct value on this axis — no best/worst spread.
- **`suite_ref`:** best `fixtures/benchmarks/campaign_micro.v1.yaml` (0.667276, n=1), worst `fixtures/benchmarks/offline.v1.yaml` (0.367251, n=1), spread **0.300025**

### Backend (mean cell score across the campaign)

- **Best:** `mock` (0.410112 over 7 cells)
- **Weakest:** _only one backend kind present._

### Semantic / hybrid instability (longitudinal)

_No cells flagged as semantically unstable at configured thresholds._

### Execution mode gaps (within-run)

- **Signals:** 2 row(s) at threshold ≥ 0.12.
- **Largest spread:** **0.7782** on `campaign.examples.multi_suite.v1__0001` / `p-one` (browser_mock=0.3062, cli=0.8439, repo_governed=0.0657).

### Top recurring failure tags (FT-*)

- `FT-ABS-LOW`×4, `FT-MODE-GAP`×2

## Which dimensions varied

| Axis | Distinct values | Varied |
| --- | ---: | --- |
| `benchmark_id` | 2 (bench.fixtures.campaign.micro.v1, bench.offline.v1) | yes |
| `browser_config_applied` | 1 (False) | no |
| `eval_scoring_label` | 1 (suite_default) | no |
| `execution_modes_filter` | 1 (—) | no |
| `provider_config_ref` | 1 (null (harness default)) | no |
| `suite_ref` | 2 (fixtures/benchmarks/campaign_micro.v1.yaml, fixtures/benchmarks/offline.v1.yaml) | yes |

## Member-run mean score by sweep value

Each row is the mean of **mean_total_weighted_score** for member runs at that sweep value (equal weight per run). Only axes with **more than one** distinct value are shown.

### `benchmark_id`

| Value | Runs | Mean member score |
| --- | ---: | ---: |
| `bench.fixtures.campaign.micro.v1` | 1 | 0.667276 |
| `bench.offline.v1` | 1 | 0.367251 |

### `suite_ref`

| Value | Runs | Mean member score |
| --- | ---: | ---: |
| `fixtures/benchmarks/campaign_micro.v1.yaml` | 1 | 0.667276 |
| `fixtures/benchmarks/offline.v1.yaml` | 1 | 0.367251 |

## Fingerprint axes (longitudinal grouping keys)

Each **succeeded** member run is grouped using the same keys as ``group_snapshots_by`` in ``pipelines/longitudinal`` (``provider_config_fingerprint``, ``scoring_config_fingerprint``, ``execution_mode``, ``prompt_registry_state_fingerprint``, ``browser_config_fingerprint``). **Pooled mean** is the mean of all cell **total_weighted_score** values in that group. **Unstable** counts longitudinal **FT-JUDGE-UNSTABLE**-class rows for runs in the group. **Regressions→** counts **to_run** edges (score dropped vs the prior run for the same benchmark cell) whose destination run lies in this group.

### Provider config (`provider_config_fingerprint`)

| Group (short) | run_ids | Pooled mean | Cells | Unstable | Regressions→ | Mode gaps |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `sha256:4fbcb71d4546d6de7a19…` | `campaign.examples.multi_suite.v1__0000` | 0.667276 | 1 | 0 | 0 | 0 |
| `sha256:c26e5aa1062dd8044ff0…` | `campaign.examples.multi_suite.v1__0001` | 0.367251 | 6 | 0 | 0 | 2 |

### Scoring config (`scoring_config_fingerprint`)

| Group (short) | run_ids | Pooled mean | Cells | Unstable | Regressions→ | Mode gaps |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `sha256:f958bcbda76ceda7438c…` | `campaign.examples.multi_suite.v1__0000`, `campaign.examples.multi_suite.v1__0001` | 0.410112 | 7 | 0 | 0 | 2 |

### Execution mode (`execution_mode`)

| Group (short) | run_ids | Pooled mean | Cells | Unstable | Regressions→ | Mode gaps |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `(mixed)` | `campaign.examples.multi_suite.v1__0001` | 0.367251 | 6 | 0 | 0 | 2 |
| `cli` | `campaign.examples.multi_suite.v1__0000` | 0.667276 | 1 | 0 | 0 | 0 |

### Prompt registry state (`prompt_registry_state_fingerprint`)

| Group (short) | run_ids | Pooled mean | Cells | Unstable | Regressions→ | Mode gaps |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `sha256:9604a174787655177b3c…` | `campaign.examples.multi_suite.v1__0000`, `campaign.examples.multi_suite.v1__0001` | 0.410112 | 7 | 0 | 0 | 2 |

### Browser config (`browser_config_fingerprint`)

| Group (short) | run_ids | Pooled mean | Cells | Unstable | Regressions→ | Mode gaps |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `sha256:0801b86094b64df0a6e4…` | `campaign.examples.multi_suite.v1__0000` | 0.667276 | 1 | 0 | 0 | 0 |
| `sha256:ed3546eca3742a5cf3c4…` | `campaign.examples.multi_suite.v1__0001` | 0.367251 | 6 | 0 | 0 | 2 |

### Correlation-style notes (score vs instability)

- **Provider config:** spread **0.300025** on pooled mean; pooled mean score spread 0.300025 (lowest `sha256:c26e5aa1062dd8044ff0…` 0.367251 vs highest `sha256:4fbcb71d4546d6de7a19…` 0.667276).
- **Scoring config:** Single group on this axis — no cross-group spread.
- **Execution mode:** spread **0.300025** on pooled mean; pooled mean score spread 0.300025 (lowest `(mixed)` 0.367251 vs highest `cli` 0.667276).
- **Prompt registry state:** Single group on this axis — no cross-group spread.
- **Browser config:** spread **0.300025** on pooled mean; pooled mean score spread 0.300025 (lowest `sha256:ed3546eca3742a5cf3c4…` 0.367251 vs highest `sha256:0801b86094b64df0a6e4…` 0.667276).

## Provider / backend performance (mean cell score)

Higher is better (simple mean of **total_weighted_score** over all cells using that **backend_kind** across member runs).

| Rank | backend_kind | Mean score | Cells |
| ---: | --- | ---: | ---: |
| 1 | `mock` | 0.410112 | 7 |

## Scoring backends with semantic / hybrid instability

Counts **cells** flagged in longitudinal semantic stability analysis (low confidence or repeat-variance thresholds), grouped by **scoring_backend** on the evaluation artifact.

| scoring_backend | Unstable cell events |
| --- | ---: |
| *(no unstable cells)* | 0 |

## Execution mode divergence (within-run)

Largest spreads across **execution_mode** for the same **prompt_id** inside one member run (threshold ≥ 0.12; top 2 rows).

| run_id | benchmark | prompt | spread | modes (score) |
| --- | --- | --- | ---: | --- |
| `campaign.examples.multi_suite.v1__0001` | `bench.offline.v1` | `p-one` | 0.778220 | browser_mock=0.3062, cli=0.8439, repo_governed=0.0657 |
| `campaign.examples.multi_suite.v1__0001` | `bench.offline.v1` | `p-two` | 0.545823 | browser_mock=0.6521, cli=0.1063, repo_governed=0.2295 |

## Top recurring failure taxonomy tags

Signal counts (unique FT-* entries per code). See `docs/workflows/longitudinal-reporting.md` or `FAILURE_TAXONOMY` in `pipelines/longitudinal.py`.

| Rank | Code | Signals | Description |
| ---: | --- | ---: | --- |
| 1 | `FT-ABS-LOW` | 4 | Cell total score below the configured low-score threshold. |
| 2 | `FT-MODE-GAP` | 2 | Within a single run, spread of cell means across execution modes for the same prompt exceeds the mode-gap threshold. |

## Failure atlas (full taxonomy)

Grouped signals from the analyzed benchmark runs. Paths are relative to the repository root.

## FT-ABS-LOW

Cell total score below the configured low-score threshold.

- `bench.offline.v1::v-browser__p-one`
- `bench.offline.v1::v-cli__p-two`
- `bench.offline.v1::v-repo__p-one`
- `bench.offline.v1::v-repo__p-two`

## FT-RUN-REG

Run-over-run regression: total score dropped more than the regression delta vs the previous snapshot for the same benchmark + cell.

_No signals in this pass._

## FT-CRIT-DROP

At least one rubric criterion dropped vs the previous run for that cell.

_No signals in this pass._

## FT-RECUR-LOW

Cell scored below the low threshold in at least `min_recurring` distinct runs.

_No signals in this pass._

## FT-MODE-GAP

Within a single run, spread of cell means across execution modes for the same prompt exceeds the mode-gap threshold.

- `bench.offline.v1::p-one`
- `bench.offline.v1::p-two`

## FT-PROV-SPLIT

Within a single run, multiple backend kinds present — compare mock vs live paths explicitly when interpreting scores.

_No signals in this pass._

## FT-JUDGE-UNSTABLE

Semantic or hybrid judge flagged low confidence, or repeat-run stdev/range exceeded the configured semantic threshold for that cell.

_No signals in this pass._

## FT-SERIES-SWING

High variance of total score across three or more snapshots for the same benchmark cell (oscillation / instability over time).

_No signals in this pass._
