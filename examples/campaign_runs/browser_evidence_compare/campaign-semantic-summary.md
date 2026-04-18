# Judge variance — `campaign.examples.browser_evidence_compare.v1`

- **title:** Example — browser evidence contrast (checkout vs form fixtures)
- **created_at:** `1970-01-01T00:00:00Z`

## Snapshot

Low-confidence flags, repeat-judge spread, and per-criterion disagreement.

| Signal | Count |
| --- | ---: |
| Runs scanned | 2 |
| Cells total | 2 |
| Low-confidence (merged) | 0 |
| `judge_low_confidence` | 0 |
| repeat `confidence.low_confidence` | 0 |
| Repeat-judge cells (N>1) | 0 |
| Semantic / hybrid cells | 0 |
| Deterministic cells | 2 |
| Max range (campaign) | — |
| Mean range (repeat cells) | — |
| Mean σ total (repeat cells) | — |

### Suites

| Rank | Axis | Instab. | Cells | Sem | Rep | LC | m_rng | x_rng | σ_tot |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | `fixtures/benchmarks/browser_form.v1.yaml` | -1.000000 | 1 | 0 | 0 | 0 | — | — | — |
| 2 | `fixtures/benchmarks/browser_checkout.v1.yaml` | -1.000000 | 1 | 0 | 0 | 0 | — | — | — |

### Provider axis

| Rank | Axis | Instab. | Cells | Sem | Rep | LC | m_rng | x_rng | σ_tot |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | `(default)` | -1.000000 | 2 | 0 | 0 | 0 | — | — | — |

### Execution modes

| Rank | Axis | Instab. | Cells | Sem | Rep | LC | m_rng | x_rng | σ_tot |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | `browser_mock` | -1.000000 | 2 | 0 | 0 | 0 | — | — | — |

## Instability hotspots

Highest disagreement on repeat-judge cells (`mean_range_across_cells` / `max_range_observed`).

_No semantic / hybrid cells — hotspots apply when `eval_scoring.backend` is semantic or hybrid with repeat judges._

## Detailed rollups — by suite

| Suite | Cells | Semantic | Repeat judge | Low conf. | Max range | Mean range | Mean σ_tot |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `fixtures/benchmarks/browser_checkout.v1.yaml` | 1 | 0 | 0 | 0 | — | — | — |
| `fixtures/benchmarks/browser_form.v1.yaml` | 1 | 0 | 0 | 0 | — | — | — |

## Detailed rollups — by provider config (campaign axis)

| Provider ref | Cells | Semantic | Repeat judge | Low conf. | Max range | Mean range | Mean σ_tot |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `(default)` | 2 | 0 | 0 | 0 | — | — | — |

## Detailed rollups — by execution mode

| Mode | Cells | Semantic | Repeat judge | Low conf. | Max range | Mean range | Mean σ_tot |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `browser_mock` | 2 | 0 | 0 | 0 | — | — | — |

## Low confidence & high disagreement (cells)

| Run | Cell | Scoring | N | j_lc | r_cf | merged | flags | max_r | σ_tot |
| --- | --- | --- | ---: | --- | --- | --- | --- | ---: | ---: |
