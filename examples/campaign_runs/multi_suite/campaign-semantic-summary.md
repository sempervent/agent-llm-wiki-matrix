# Semantic & hybrid scoring — `campaign.examples.multi_suite.v1`

- **title:** Example — multi-suite sweep (two fixtures)
- **created_at:** `1970-01-01T00:00:00Z`

## Totals

| Metric | Value |
| --- | ---: |
| Runs scanned | 2 |
| Cells total | 7 |
| Deterministic cells | 7 |
| Semantic / hybrid cells | 0 |
| Cells with repeat judge (N>1) | 0 |
| Low-confidence cells | 0 |
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
| `fixtures/benchmarks/offline.v1.yaml` | 6 | 0 | 0 | 0 | — | — | — |

## Detailed rollups — by provider config (campaign axis)

| Provider ref | Cells | Semantic | Repeat judge | Low conf. | Max range | Mean range | Mean σ_tot |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `(default)` | 7 | 0 | 0 | 0 | — | — | — |

## Detailed rollups — by execution mode

| Mode | Cells | Semantic | Repeat judge | Low conf. | Max range | Mean range | Mean σ_tot |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `browser_mock` | 2 | 0 | 0 | 0 | — | — | — |
| `cli` | 3 | 0 | 0 | 0 | — | — | — |
| `repo_governed` | 2 | 0 | 0 | 0 | — | — | — |

## Low confidence & high disagreement (cells)

| Run | Cell | Scoring | N | Low conf. | max_range | σ_tot |
| --- | --- | --- | ---: | --- | ---: | ---: |
