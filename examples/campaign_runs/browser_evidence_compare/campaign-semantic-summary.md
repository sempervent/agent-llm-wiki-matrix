# Campaign semantic summary

- **Campaign:** `campaign.examples.browser_evidence_compare.v1`
- **Title:** Example — browser evidence contrast (checkout vs form fixtures)
- **Created:** `1970-01-01T00:00:00Z`

Rolls up **semantic** and **hybrid** scoring cells: repeat-judge disagreement, low-confidence flags, per-criterion instability, and per-axis hotspots. **Deterministic** cells are counted but do not contribute judge spread. Use with **`campaign-summary.md`** (run index) and **`reports/campaign-report.md`** (full comparative narrative).

## Executive snapshot

Counts below combine judge metadata from member-run **evaluation** artifacts.

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

Axes with the largest judge disagreement on repeat-judge cells (**`mean_range_across_cells`** / **`max_range_observed`**).

_No semantic / hybrid cells — hotspots apply when `eval_scoring.backend` is semantic or hybrid with repeat judges._

## Detailed rollups by suite

| Suite | Cells | Semantic | Repeat judge | Low conf. | Max range | Mean range | Mean σ_tot |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `fixtures/benchmarks/browser_checkout.v1.yaml` | 1 | 0 | 0 | 0 | — | — | — |
| `fixtures/benchmarks/browser_form.v1.yaml` | 1 | 0 | 0 | 0 | — | — | — |

## Detailed rollups by provider config

| Provider ref | Cells | Semantic | Repeat judge | Low conf. | Max range | Mean range | Mean σ_tot |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `(default)` | 2 | 0 | 0 | 0 | — | — | — |

## Detailed rollups by execution mode

| Mode | Cells | Semantic | Repeat judge | Low conf. | Max range | Mean range | Mean σ_tot |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `browser_mock` | 2 | 0 | 0 | 0 | — | — | — |

## Low confidence & high disagreement (cells)

| Run | Cell | Scoring | N | j_lc | r_cf | merged | flags | max_r | σ_tot |
| --- | --- | --- | ---: | --- | --- | --- | --- | ---: | ---: |
