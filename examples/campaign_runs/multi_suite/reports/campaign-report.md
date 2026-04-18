# Campaign comparative report: `campaign.examples.multi_suite.v1`

**Succeeded** member runs only. **`FT-*`:** `docs/workflows/longitudinal-reporting.md`. Same longitudinal pass as `campaign-analysis.json`.

## Executive summary

At-a-glance; **sections below** repeat and expand each topic (including failure atlas).

- **Varied sweep axes:** `suite_ref`.
- _Note:_ `suite_ref` and `benchmark_id` sweep together — member scores by benchmark are the same grouping as by suite.

### Mean member score — best / worst by axis

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
| 1 | `fixtures/benchmarks/offline.v1.yaml` | -1.000000 | 0 | 0 | — | — |
| 2 | `fixtures/benchmarks/campaign_micro.v1.yaml` | -1.000000 | 0 | 0 | — | — |

### Provider axis

| # | Axis | Instability | Low-conf. | Repeat cells | mean_range | max_range |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `(default)` | -1.000000 | 0 | 0 | — | — |

### Execution modes

| # | Axis | Instability | Low-conf. | Repeat cells | mean_range | max_range |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `repo_governed` | -1.000000 | 0 | 0 | — | — |
| 2 | `cli` | -1.000000 | 0 | 0 | — | — |
| 3 | `browser_mock` | -1.000000 | 0 | 0 | — | — |


---

## Which dimensions varied

| Axis | Distinct values | Varied |
| --- | ---: | --- |
| `browser_config_applied` | 1 (False) | no |
| `eval_scoring_label` | 1 (suite_default) | no |
| `execution_modes_filter` | 1 (—) | no |
| `provider_config_ref` | 1 (null (harness default)) | no |
| `suite_ref (paired with benchmark_id)` | 2 (fixtures/benchmarks/campaign_micro.v1.yaml, fixtures/benchmarks/offline.v1.yaml) | yes |

## Member-run mean score by sweep value

Each row is the mean of **mean_total_weighted_score** for member runs at that sweep value (equal weight per run). Only axes with **more than one** distinct value are shown.

### `suite_ref`

| Value | Runs | Mean member score |
| --- | ---: | ---: |
| `fixtures/benchmarks/campaign_micro.v1.yaml` | 1 | 0.667276 |
| `fixtures/benchmarks/offline.v1.yaml` | 1 | 0.367251 |

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

**Evidence is limited on** `provider_config_fingerprint`, `execution_mode`, `browser_config_fingerprint` (small cell counts and/or thin buckets) — treat all labels below as **triage only**, not confirmation. **Likely configuration / path (heuristic):** `provider_config_fingerprint`, `execution_mode`, `browser_config_fingerprint` show the clearest **mean separation** with **low** judge-instability signal in aggregate — consistent with **stable** config/path differences, still **not** proven causation.

#### Per-axis attribution (heuristic)

| Axis | Kind | Pattern | Evidence | Conf. | Cells (min bucket) |
| --- | --- | --- | --- | --- | ---: |
| `provider_config_fingerprint` | `config_fingerprint` | **Config-driven** (heuristic) | weak | low | 1 |
| `execution_mode` | `execution_mode` | **Config-driven** (heuristic) | weak | low | 1 |
| `browser_config_fingerprint` | `config_fingerprint` | **Config-driven** (heuristic) | weak | low | 1 |

**Rationale & sample limits (per axis):**

- **`provider_config_fingerprint`:** **Likely configuration / path-driven:** meaningful pooled mean spread across manifest fingerprint slices (resolved provider/scoring/registry/browser config) with **no** judge-instability rows in these buckets — gaps are **plausibly stable** vs config/path at this granularity (still not causal).
  - _Limit:_ Smallest bucket has only 1 cell(s) — **high variance** in that bucket mean.
  - _Limit:_ Only two buckets and modest cell totals — treat spread as **directional**, not firm.
  - _Limit:_ Confidence downgraded to **low** because aggregate evidence strength is **weak**.
- **`execution_mode`:** **Likely configuration / path-driven:** meaningful pooled mean spread across execution mode slices (harness/tooling path) with **no** judge-instability rows in these buckets — gaps are **plausibly stable** vs config/path at this granularity (still not causal).
  - _Limit:_ Smallest bucket has only 1 cell(s) — **high variance** in that bucket mean.
  - _Limit:_ Only two buckets and modest cell totals — treat spread as **directional**, not firm.
  - _Limit:_ Confidence downgraded to **low** because aggregate evidence strength is **weak**.
- **`browser_config_fingerprint`:** **Likely configuration / path-driven:** meaningful pooled mean spread across manifest fingerprint slices (resolved provider/scoring/registry/browser config) with **no** judge-instability rows in these buckets — gaps are **plausibly stable** vs config/path at this granularity (still not causal).
  - _Limit:_ Smallest bucket has only 1 cell(s) — **high variance** in that bucket mean.
  - _Limit:_ Only two buckets and modest cell totals — treat spread as **directional**, not firm.
  - _Limit:_ Confidence downgraded to **low** because aggregate evidence strength is **weak**.

#### Score spread (ranked by pooled mean gap across buckets)

| Rank | Axis | Spread | Lowest mean (bucket) | Highest mean (bucket) |
| ---: | --- | ---: | --- | --- |
| 1 | `provider_config_fingerprint` | 0.300025 | `sha256:c26e5aa1062dd8044ff0…` | `sha256:4fbcb71d4546d6de7a19…` |
| 2 | `execution_mode` | 0.300025 | `(mixed)` | `cli` |
| 3 | `browser_config_fingerprint` | 0.300025 | `sha256:ed3546eca3742a5cf3c4…` | `sha256:0801b86094b64df0a6e4…` |

#### Instability hotspots (judge instability vs bucket size)

| Axis | Most events (bucket) | Events | Cells | Rate | Highest rate (bucket) | Rate |
| --- | --- | ---: | ---: | ---: | --- | ---: |
| `provider_config_fingerprint` | `sha256:4fbcb71d4546d6de7a19…` | 0 | 1 | 0.000000 | `sha256:4fbcb71d4546d6de7a19…` | 0.000000 |
| `execution_mode` | `(mixed)` | 0 | 6 | 0.000000 | `(mixed)` | 0.000000 |
| `browser_config_fingerprint` | `sha256:0801b86094b64df0a6e4…` | 0 | 1 | 0.000000 | `sha256:0801b86094b64df0a6e4…` | 0.000000 |

#### Raw signals (secondary checks)

_Cross-checks beyond the attribution table — grouped by **signal_class** (configuration vs instability vs mixed). Still heuristic._

##### Configuration / spread structure

- **`config_fingerprint_axis_in_top_score_spread`** (`provider_config_fingerprint`, _note_): This experiment-config fingerprint axis is among the top score-spread drivers — compare manifest comparison_fingerprints and member manifests.
- **`config_fingerprint_axis_in_top_score_spread`** (`browser_config_fingerprint`, _note_): This experiment-config fingerprint axis is among the top score-spread drivers — compare manifest comparison_fingerprints and member manifests.

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

## Browser evidence (member runs)

**mock** traces from `fixtures/browser_evidence/v1/`; optional **Playwright** (`[browser]`). See `docs/architecture/browser.md`.

| Member cell | Evidence | Runner | Signals | DOM snap | Extension digest |
| --- | --- | --- | --- | --- | --- |
| `campaign.examples.multi_suite.v1__0001 / v-browser__p-one` | `mock-evidence-v-browser__p-one` (Mock browser evidence (v-browser__p-one)) | `mock` | nav×2 · console×1 · dom×1 · shot×1 | — | net 0 req/ok · a11y 0v · trace 94de29738ca1 |
| `campaign.examples.multi_suite.v1__0001 / v-browser__p-two` | `mock-evidence-v-browser__p-two` (Mock browser evidence (v-browser__p-two)) | `mock` | nav×2 · console×1 · dom×1 · shot×1 | — | net 0 req/ok · a11y 0v · trace 692a9af2e692 |

### Per-cell traces

#### `campaign.examples.multi_suite.v1__0001` · `v-browser__p-one`

- **suite:** `fixtures/benchmarks/offline.v1.yaml`
- **runner:** `mock` (deterministic fixture)
- **evidence:** `mock-evidence-v-browser__p-one` — Mock browser evidence (v-browser__p-one)
- **signals:** nav×2 · console×1 · dom×1 · shot×1
- **extensions (digest):** net 0 req/ok · a11y 0v · trace 94de29738ca1

**Navigation**

- `https://example.test/` “Start” [navigate]
- `https://example.test/step-2` “Mock step (94de29738ca1)” [navigate]

**Console**

- `[log]` mock_trace=94de29738ca1

**DOM excerpts**

| # | Label | Selector | Role | a11y name | Order | Visible text |
| ---: | --- | --- | --- | --- | ---: | --- |
| 1 | mock primary surface | `[data-mock-id='94de29738ca1']` | `button` | Mock action v-browser__p-one | 0 | Deterministic mock excerpt for v-browser__p-one |

**Screenshots**

| Seq | Scope | Target | Viewport | DPR | SHA-256 (short) | MIME | Caption |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 0 | `viewport` | — | 1280×720 | 1 | `000000000000…` | image/png | Mock screenshot metadata only (no binary). |

**Extensions (structured)**

| Extension block | Summary |
| --- | --- |
| `structured_capture_version` | 1 |
| `runner` | `mock` (deterministic fixture) |
| `trace_digest` | `94de29738ca1` |
| **network** | req 0, fail 0, last `—` → — |
| **accessibility** | rules_checked=0, violations_count=0 |

_Notes:_ MockBrowserRunner: deterministic; no real browser.

#### `campaign.examples.multi_suite.v1__0001` · `v-browser__p-two`

- **suite:** `fixtures/benchmarks/offline.v1.yaml`
- **runner:** `mock` (deterministic fixture)
- **evidence:** `mock-evidence-v-browser__p-two` — Mock browser evidence (v-browser__p-two)
- **signals:** nav×2 · console×1 · dom×1 · shot×1
- **extensions (digest):** net 0 req/ok · a11y 0v · trace 692a9af2e692

**Navigation**

- `https://example.test/` “Start” [navigate]
- `https://example.test/step-2` “Mock step (692a9af2e692)” [navigate]

**Console**

- `[log]` mock_trace=692a9af2e692

**DOM excerpts**

| # | Label | Selector | Role | a11y name | Order | Visible text |
| ---: | --- | --- | --- | --- | ---: | --- |
| 1 | mock primary surface | `[data-mock-id='692a9af2e692']` | `button` | Mock action v-browser__p-two | 0 | Deterministic mock excerpt for v-browser__p-two |

**Screenshots**

| Seq | Scope | Target | Viewport | DPR | SHA-256 (short) | MIME | Caption |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 0 | `viewport` | — | 1280×720 | 1 | `000000000000…` | image/png | Mock screenshot metadata only (no binary). |

**Extensions (structured)**

| Extension block | Summary |
| --- | --- |
| `structured_capture_version` | 1 |
| `runner` | `mock` (deterministic fixture) |
| `trace_digest` | `692a9af2e692` |
| **network** | req 0, fail 0, last `—` → — |
| **accessibility** | rules_checked=0, violations_count=0 |

_Notes:_ MockBrowserRunner: deterministic; no real browser.

## Provider / backend performance (mean cell score)

Mean **total_weighted_score** per **backend_kind** (higher is better).

| Rank | backend_kind | Mean score | Cells |
| ---: | --- | ---: | ---: |
| 1 | `mock` | 0.410112 | 7 |

## Scoring backends with semantic / hybrid instability

Unstable **cell** events by **scoring_backend** (longitudinal thresholds).

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

Signal counts per **FT-*** code (`docs/workflows/longitudinal-reporting.md`).

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
