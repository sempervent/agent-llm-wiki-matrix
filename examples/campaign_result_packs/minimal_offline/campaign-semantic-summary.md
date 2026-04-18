# Campaign semantic summary

- **Campaign:** `campaign.examples.minimal_offline.v1`
- **Title:** Minimal offline campaign (single suite, deterministic)
- **Created:** `1970-01-01T00:00:00Z`

Semantic / hybrid judge rollups from member **evaluation** artifacts (deterministic cells counted, no spread). Cross-link: **`campaign-summary.md`**, **`reports/campaign-report.md`**.

## Executive snapshot

| Signal | Count |
| --- | ---: |
| Runs scanned | 1 |
| Cells total | 1 |
| Low-confidence (merged) | 0 |
| `judge_low_confidence` | 0 |
| repeat `confidence.low_confidence` | 0 |
| Repeat-judge cells (N>1) | 0 |
| Semantic / hybrid cells | 0 |
| Deterministic cells | 1 |
| Max range (campaign) | — |
| Mean range (repeat cells) | — |
| Mean σ total (repeat cells) | — |

## Instability hotspots

Ranked by **`mean_range_across_cells`** and **`max_range_observed`** (repeat-judge cells).

_No semantic / hybrid cells — hotspots apply when `eval_scoring.backend` is semantic or hybrid with repeat judges._

## Detailed rollups by suite

| Suite | Cells | Semantic | Repeat judge | Low conf. | Max range | Mean range | Mean σ_tot |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `fixtures/benchmarks/campaign_micro.v1.yaml` | 1 | 0 | 0 | 0 | — | — | — |

## Detailed rollups by provider config

| Provider ref | Cells | Semantic | Repeat judge | Low conf. | Max range | Mean range | Mean σ_tot |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `(default)` | 1 | 0 | 0 | 0 | — | — | — |

## Detailed rollups by execution mode

| Mode | Cells | Semantic | Repeat judge | Low conf. | Max range | Mean range | Mean σ_tot |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `cli` | 1 | 0 | 0 | 0 | — | — | — |

## Low confidence & high disagreement (cells)

| Run | Cell | Scoring | N | j_lc | r_cf | merged | flags | max_r | σ_tot |
| --- | --- | --- | ---: | --- | --- | --- | --- | ---: | ---: |
