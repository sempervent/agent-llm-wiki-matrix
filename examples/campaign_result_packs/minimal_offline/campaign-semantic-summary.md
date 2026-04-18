# Semantic & hybrid scoring — `campaign.examples.minimal_offline.v1`

- **title:** Minimal offline campaign (single suite, deterministic)
- **created_at:** `1970-01-01T00:00:00Z`

## Judge confidence & disagreement (campaign snapshot)

Use this section first: it surfaces **`judge_low_confidence`**, **repeat-judge disagreement** (`max_range_across_criteria`, per-criterion **score_range**), and **threshold flags** from **`repeat_aggregation`** before the full rollups below.

| Signal | Count |
| --- | ---: |
| Low-confidence cells (merged) | 0 |
| Cells with `Evaluation.judge_low_confidence` | 0 |
| Cells with repeat `confidence.low_confidence` | 0 |
| Cells with repeat judge (N>1) | 0 |
| Semantic / hybrid cells | 0 |
| Deterministic cells | 1 |

### Unstable suites (ranked)

| Rank | Axis | Instab. | Cells | Sem | Rep | LC | m_rng | x_rng | σ_tot |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | `fixtures/benchmarks/campaign_micro.v1.yaml` | -1.000000 | 1 | 0 | 0 | 0 | — | — | — |

### Unstable provider axis (ranked)

| Rank | Axis | Instab. | Cells | Sem | Rep | LC | m_rng | x_rng | σ_tot |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | `(default)` | -1.000000 | 1 | 0 | 0 | 0 | — | — | — |

### Unstable execution modes (ranked)

| Rank | Axis | Instab. | Cells | Sem | Rep | LC | m_rng | x_rng | σ_tot |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | `cli` | -1.000000 | 1 | 0 | 0 | 0 | — | — | — |

## Totals

| Metric | Value |
| --- | ---: |
| Runs scanned | 1 |
| Cells total | 1 |
| Deterministic cells | 1 |
| Semantic / hybrid cells | 0 |
| Cells with repeat judge (N>1) | 0 |
| Low-confidence cells (merged) | 0 |
| Max range across campaign | — |
| Mean range (repeat cells) | — |
| Mean σ total weighted (repeat cells) | — |

## Instability hotspots (ranked)

Slices with the **highest** judge disagreement (`mean_range_across_cells` or `max_range_observed` on repeat cells). Use these to prioritize reviews.

_No semantic / hybrid cells — hotspots apply when `eval_scoring.backend` is semantic or hybrid with repeat judges._

## Detailed rollups — by suite

| Suite | Cells | Semantic | Repeat judge | Low conf. | Max range | Mean range | Mean σ_tot |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `fixtures/benchmarks/campaign_micro.v1.yaml` | 1 | 0 | 0 | 0 | — | — | — |

## Detailed rollups — by provider config (campaign axis)

| Provider ref | Cells | Semantic | Repeat judge | Low conf. | Max range | Mean range | Mean σ_tot |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `(default)` | 1 | 0 | 0 | 0 | — | — | — |

## Detailed rollups — by execution mode

| Mode | Cells | Semantic | Repeat judge | Low conf. | Max range | Mean range | Mean σ_tot |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `cli` | 1 | 0 | 0 | 0 | — | — | — |

## Low confidence & high disagreement (cells)

| Run | Cell | Scoring | N | j_lc | r_cf | merged | flags | max_r | σ_tot |
| --- | --- | --- | ---: | --- | --- | --- | --- | ---: | ---: |
