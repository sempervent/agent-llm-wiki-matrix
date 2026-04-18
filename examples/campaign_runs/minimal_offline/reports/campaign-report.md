# Campaign comparative report: `campaign.examples.minimal_offline.v1`

Aggregates **succeeded** member runs under this campaign directory. Regression-style **`FT-*`** signals use the same taxonomy as longitudinal analysis (adjacent run order in the campaign manifest when the same benchmark cell appears in multiple runs). Within-run mode gaps and judge instability apply per snapshot.

## Which dimensions varied

| Axis | Distinct values | Varied |
| --- | ---: | --- |
| `benchmark_id` | 1 (bench.fixtures.campaign.micro.v1) | no |
| `browser_config_applied` | 1 (False) | no |
| `eval_scoring_label` | 1 (suite_default) | no |
| `execution_modes_filter` | 1 (—) | no |
| `provider_config_ref` | 1 (null (harness default)) | no |
| `suite_ref` | 1 (fixtures/benchmarks/campaign_micro.v1.yaml) | no |

## Provider / backend performance (mean cell score)

Higher is better (simple mean of **total_weighted_score** over all cells using that **backend_kind** across member runs).

| Rank | backend_kind | Mean score | Cells |
| ---: | --- | ---: | ---: |
| 1 | `mock` | 0.667276 | 1 |

## Scoring backends with semantic / hybrid instability

Counts **cells** flagged in longitudinal semantic stability analysis (low confidence or repeat-variance thresholds), grouped by **scoring_backend** on the evaluation artifact.

| scoring_backend | Unstable cell events |
| --- | ---: |
| *(no unstable cells)* | 0 |

## Execution mode divergence (within-run)

Largest spreads across **execution_mode** for the same **prompt_id** inside one member run (threshold ≥ 0.12; top 1 rows).

| run_id | benchmark | prompt | spread | modes (score) |
| --- | --- | --- | ---: | --- |
| — | — | — | — | _No mode-gap signals at threshold._ |

## Top recurring failure taxonomy tags

Signal counts (unique FT-* entries per code). See `docs/workflows/longitudinal-reporting.md` or `FAILURE_TAXONOMY` in `pipelines/longitudinal.py`.

| Rank | Code | Signals | Description |
| ---: | --- | ---: | --- |
| — | — | 0 | _No FT-* signals in this pass._ |

## Failure atlas (full taxonomy)

Grouped signals from the analyzed benchmark runs. Paths are relative to the repository root.

## FT-ABS-LOW

Cell total score below the configured low-score threshold.

_No signals in this pass._

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

_No signals in this pass._

## FT-PROV-SPLIT

Within a single run, multiple backend kinds present — compare mock vs live paths explicitly when interpreting scores.

_No signals in this pass._

## FT-JUDGE-UNSTABLE

Semantic or hybrid judge flagged low confidence, or repeat-run stdev/range exceeded the configured semantic threshold for that cell.

_No signals in this pass._

## FT-SERIES-SWING

High variance of total score across three or more snapshots for the same benchmark cell (oscillation / instability over time).

_No signals in this pass._
