# Campaign comparative report: `campaign.examples.minimal_offline.v1`

**Succeeded** member runs only. **`FT-*`:** `docs/workflows/longitudinal-reporting.md`. Same longitudinal pass as `campaign-analysis.json`.

## Executive summary

At-a-glance; **sections below** repeat and expand each topic (including failure atlas).

- **Varied sweep axes:** _none — single configuration path in this campaign._

### Mean member score — best / worst by axis

- _Need at least two succeeded member runs with mean scores to compare axes._

### Backend (mean cell score across the campaign)

- **Best:** `mock` (0.667276 over 1 cells)
- **Weakest:** _only one backend kind present._

### Semantic / hybrid instability (longitudinal)

_No cells flagged as semantically unstable at configured thresholds._

### Execution mode gaps (within-run)

_No mode-gap rows above threshold (or modes not comparable in member runs)._

### Top recurring failure tags (FT-*)

_No FT-* signals in this pass._

## Judge variance (abbreviated)

_Full tables: `campaign-semantic-summary.md`._

| Signal | Count |
| --- | ---: |
| Low-confidence (merged) | 0 |
| `judge_low_confidence` | 0 |
| repeat `confidence.low_confidence` | 0 |
| Repeat-judge cells (N>1) | 0 |
| Max range (campaign) | — |

### Suites

| # | Axis | Instability | Low-conf. | Repeat cells | mean_range | max_range |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `fixtures/benchmarks/campaign_micro.v1.yaml` | -1.000000 | 0 | 0 | — | — |

### Provider axis

| # | Axis | Instability | Low-conf. | Repeat cells | mean_range | max_range |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `(default)` | -1.000000 | 0 | 0 | — | — |

### Execution modes

| # | Axis | Instability | Low-conf. | Repeat cells | mean_range | max_range |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `cli` | -1.000000 | 0 | 0 | — | — |


---

## Which dimensions varied

| Axis | Distinct values | Varied |
| --- | ---: | --- |
| `benchmark_id` | 1 (bench.fixtures.campaign.micro.v1) | no |
| `browser_config_applied` | 1 (False) | no |
| `eval_scoring_label` | 1 (suite_default) | no |
| `execution_modes_filter` | 1 (—) | no |
| `provider_config_ref` | 1 (null (harness default)) | no |
| `suite_ref` | 1 (fixtures/benchmarks/campaign_micro.v1.yaml) | no |

## Member-run mean score by sweep value

Each row is the mean of **mean_total_weighted_score** for member runs at that sweep value (equal weight per run). Only axes with **more than one** distinct value are shown.

_No axis had more than one distinct value among runs with scores._

## Fingerprint axes (longitudinal grouping keys)

Each **succeeded** member run is grouped using the same keys as ``group_snapshots_by`` in ``pipelines/longitudinal`` (``provider_config_fingerprint``, ``scoring_config_fingerprint``, ``execution_mode``, ``prompt_registry_state_fingerprint``, ``browser_config_fingerprint``). **Pooled mean** is the mean of all cell **total_weighted_score** values in that group. **Unstable** counts longitudinal **FT-JUDGE-UNSTABLE**-class rows for runs in the group. **Regressions→** counts **to_run** edges (score dropped vs the prior run for the same benchmark cell) whose destination run lies in this group.

_Axis interpretation below states **evidence strength** (aggregate cell counts) and **uncertainty** explicitly — small buckets or few cells mean labels are **tentative**._

### Axis interpretation (why buckets differ)

These rows summarize **aggregate** differences across fingerprint buckets (same keys as ``group_snapshots_by``). Labels distinguish **likely configuration-driven** vs **likely instability-driven** vs **mixed** vs **inconclusive** patterns — they are **not** causal claims and can be wrong when cell counts are small.

**Reading the categories:** **configuration-dominant** = spread with little instability signal; **instability-dominant** = instability without strong mean separation; **mixed** = spread and instability overlap; **inconclusive** = weak/borderline evidence.

> **Uncertainty & limits:**
> - Attribution labels describe **aggregate bucket patterns**, not proven causation.
> - Confidence and **evidence_strength** are heuristics from cell/run counts — **not** statistical significance.
> - Confidence is **low** when few member runs, few cells per bucket, or **evidence_strength** is **weak**.
> - Compare `comparison_fingerprints` on each member `manifest.json` before trusting cross-run score deltas.
> - **inconclusive** / **mixed** are expected when sample sizes are small or instability co-occurs with spread.

#### Summary

No fingerprint axis had more than one bucket in this pass, so there is no cross-bucket spread to attribute.

_No multi-bucket axes — nothing to rank._

#### Instability hotspots by axis

_No varied fingerprint axes._

#### Raw signals (secondary checks)

_Cross-checks beyond the attribution table — grouped by **signal_class** (configuration vs instability vs mixed). Still heuristic._

_No secondary hints for this dataset._

### Provider config (`provider_config_fingerprint`)

| Group (short) | run_ids | Pooled mean | Cells | Unstable | Regressions→ | Mode gaps |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `sha256:4fbcb71d4546d6de7a19…` | `campaign.examples.minimal_offline.v1__0000` | 0.667276 | 1 | 0 | 0 | 0 |

### Scoring config (`scoring_config_fingerprint`)

| Group (short) | run_ids | Pooled mean | Cells | Unstable | Regressions→ | Mode gaps |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `sha256:f958bcbda76ceda7438c…` | `campaign.examples.minimal_offline.v1__0000` | 0.667276 | 1 | 0 | 0 | 0 |

### Execution mode (`execution_mode`)

| Group (short) | run_ids | Pooled mean | Cells | Unstable | Regressions→ | Mode gaps |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `cli` | `campaign.examples.minimal_offline.v1__0000` | 0.667276 | 1 | 0 | 0 | 0 |

### Prompt registry state (`prompt_registry_state_fingerprint`)

| Group (short) | run_ids | Pooled mean | Cells | Unstable | Regressions→ | Mode gaps |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `sha256:9604a174787655177b3c…` | `campaign.examples.minimal_offline.v1__0000` | 0.667276 | 1 | 0 | 0 | 0 |

### Browser config (`browser_config_fingerprint`)

| Group (short) | run_ids | Pooled mean | Cells | Unstable | Regressions→ | Mode gaps |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `sha256:0801b86094b64df0a6e4…` | `campaign.examples.minimal_offline.v1__0000` | 0.667276 | 1 | 0 | 0 | 0 |

### Correlation-style notes (score vs instability)

- **Provider config:** Single group on this axis — no cross-group spread.
- **Scoring config:** Single group on this axis — no cross-group spread.
- **Execution mode:** Single group on this axis — no cross-group spread.
- **Prompt registry state:** Single group on this axis — no cross-group spread.
- **Browser config:** Single group on this axis — no cross-group spread.

## Provider / backend performance (mean cell score)

Mean **total_weighted_score** per **backend_kind** (higher is better).

| Rank | backend_kind | Mean score | Cells |
| ---: | --- | ---: | ---: |
| 1 | `mock` | 0.667276 | 1 |

## Scoring backends with semantic / hybrid instability

Unstable **cell** events by **scoring_backend** (longitudinal thresholds).

| scoring_backend | Unstable cell events |
| --- | ---: |
| *(no unstable cells)* | 0 |

## Execution mode divergence (within-run)

Largest spreads across **execution_mode** for the same **prompt_id** inside one member run (threshold ≥ 0.12; top 1 rows).

| run_id | benchmark | prompt | spread | modes (score) |
| --- | --- | --- | ---: | --- |
| — | — | — | — | _No mode-gap signals at threshold._ |

## Top recurring failure taxonomy tags

Signal counts per **FT-*** code (`docs/workflows/longitudinal-reporting.md`).

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
