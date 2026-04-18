# Campaign comparative report: `campaign.examples.browser_evidence_compare.v1`

Succeeded member runs only. **`FT-*`** taxonomy matches longitudinal analysis (manifest run order). Mode gaps and judge instability are per snapshot.

## At a glance

- **Varied sweep axes:** `suite_ref`.
- _Note:_ `suite_ref` and `benchmark_id` sweep together — member scores by benchmark are the same grouping as by suite.

### Mean member score — best / worst by axis

- **`browser_config_applied`:** _not comparable_ — Single distinct value on this axis — no best/worst spread.
- **`eval_scoring_label`:** _not comparable_ — Single distinct value on this axis — no best/worst spread.
- **`execution_modes_filter`:** _not comparable_ — Single distinct value on this axis — no best/worst spread.
- **`provider_config_ref`:** _not comparable_ — Single distinct value on this axis — no best/worst spread.
- **`suite_ref`:** best `fixtures/benchmarks/browser_checkout.v1.yaml` (0.571024, n=1), worst `fixtures/benchmarks/browser_form.v1.yaml` (0.361310, n=1), spread **0.209714**

### Backend (mean cell score across the campaign)

- **Best:** `mock` (0.466167 over 2 cells)
- **Weakest:** _only one backend kind present._

### Semantic / hybrid instability (longitudinal)

_No cells flagged as semantically unstable at configured thresholds._

### Execution mode gaps (within-run)

_No mode-gap rows above threshold (or modes not comparable in member runs)._

### Top recurring failure tags (FT-*)

- `FT-ABS-LOW`×1

## Judge variance (semantic / hybrid)

From **evaluation.json**, **evaluation_judge_provenance.json**, and **repeat_aggregation** when N>1. Deterministic cells have no judge spread.

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
| 1 | `fixtures/benchmarks/browser_form.v1.yaml` | -1.000000 | 0 | 0 | — | — |
| 2 | `fixtures/benchmarks/browser_checkout.v1.yaml` | -1.000000 | 0 | 0 | — | — |

### Provider axis

| # | Axis | Instability | Low-conf. | Repeat cells | mean_range | max_range |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `(default)` | -1.000000 | 0 | 0 | — | — |

### Execution modes

| # | Axis | Instability | Low-conf. | Repeat cells | mean_range | max_range |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `browser_mock` | -1.000000 | 0 | 0 | — | — |

_Full tables: `campaign-semantic-summary.md` in this directory._

## Which dimensions varied

| Axis | Distinct values | Varied |
| --- | ---: | --- |
| `browser_config_applied` | 1 (False) | no |
| `eval_scoring_label` | 1 (suite_default) | no |
| `execution_modes_filter` | 1 (—) | no |
| `provider_config_ref` | 1 (null (harness default)) | no |
| `suite_ref (paired with benchmark_id)` | 2 (fixtures/benchmarks/browser_checkout.v1.yaml, fixtures/benchmarks/browser_form.v1.yaml) | yes |

## Member-run mean score by sweep value

Each row is the mean of **mean_total_weighted_score** for member runs at that sweep value (equal weight per run). Only axes with **more than one** distinct value are shown.

### `suite_ref`

| Value | Runs | Mean member score |
| --- | ---: | ---: |
| `fixtures/benchmarks/browser_checkout.v1.yaml` | 1 | 0.571024 |
| `fixtures/benchmarks/browser_form.v1.yaml` | 1 | 0.361310 |

## Fingerprint axes (longitudinal grouping keys)

Each **succeeded** member run is grouped using the same keys as ``group_snapshots_by`` in ``pipelines/longitudinal`` (``provider_config_fingerprint``, ``scoring_config_fingerprint``, ``execution_mode``, ``prompt_registry_state_fingerprint``, ``browser_config_fingerprint``). **Pooled mean** is the mean of all cell **total_weighted_score** values in that group. **Unstable** counts longitudinal **FT-JUDGE-UNSTABLE**-class rows for runs in the group. **Regressions→** counts **to_run** edges (score dropped vs the prior run for the same benchmark cell) whose destination run lies in this group.

### Axis interpretation (why buckets differ)

These rows summarize **aggregate** differences across fingerprint buckets (same keys as ``group_snapshots_by``). They help triage **configuration / path** effects vs **judge-instability** effects — they are **not** causal claims.

> **Uncertainty & limits:**
> - Attribution labels describe **aggregate bucket patterns**, not proven causation.
> - Confidence is **low** when few member runs or few cells fall in each bucket.
> - Compare `comparison_fingerprints` on each member `manifest.json` before trusting cross-run score deltas.

#### Summary

**Configuration / path:** aggregate patterns on `provider_config_fingerprint`, `browser_config_fingerprint` are consistent with **stable** score gaps between fingerprint buckets (weak judge-instability signal). This remains a **heuristic** — confirm with manifests and per-cell evaluations.

#### Per-axis attribution (heuristic)

| Axis | Slice | Attribution | Confidence |
| --- | --- | --- | --- |
| `provider_config_fingerprint` | `config_fingerprint` | Likely **configuration / path** | low |
| `browser_config_fingerprint` | `config_fingerprint` | Likely **configuration / path** | low |

**Rationale (per axis):**

- `provider_config_fingerprint`: Meaningful pooled mean spread across manifest fingerprint slices (resolved provider/scoring/registry/browser config) with no judge-instability rows in those member runs — differences are plausibly **stable** and configuration/path-related rather than judge noise at this granularity.
- `browser_config_fingerprint`: Meaningful pooled mean spread across manifest fingerprint slices (resolved provider/scoring/registry/browser config) with no judge-instability rows in those member runs — differences are plausibly **stable** and configuration/path-related rather than judge noise at this granularity.

#### Score spread (ranked by pooled mean gap across buckets)

| Rank | Axis | Spread | Lowest mean (bucket) | Highest mean (bucket) |
| ---: | --- | ---: | --- | --- |
| 1 | `provider_config_fingerprint` | 0.209714 | `sha256:b5f7c632636d4760febd…` | `sha256:a21f9f3dfa8d97e31e7f…` |
| 2 | `browser_config_fingerprint` | 0.209714 | `sha256:bc42b4965253463647d7…` | `sha256:dda4aeabb9afaebafd87…` |

#### Instability hotspots (judge instability vs bucket size)

| Axis | Most events (bucket) | Events | Cells | Rate | Highest rate (bucket) | Rate |
| --- | --- | ---: | ---: | ---: | --- | ---: |
| `provider_config_fingerprint` | `sha256:a21f9f3dfa8d97e31e7f…` | 0 | 1 | 0.000000 | `sha256:a21f9f3dfa8d97e31e7f…` | 0.000000 |
| `browser_config_fingerprint` | `sha256:bc42b4965253463647d7…` | 0 | 1 | 0.000000 | `sha256:bc42b4965253463647d7…` | 0.000000 |

#### Raw signals (secondary checks)

_Cross-checks beyond the attribution table — grouped by **signal_class** (configuration vs instability vs mixed). Still heuristic._

##### Configuration / spread structure

- **`config_fingerprint_axis_in_top_score_spread`** (`provider_config_fingerprint`, _note_): This experiment-config fingerprint axis is among the top score-spread drivers — compare manifest comparison_fingerprints and member manifests.
- **`config_fingerprint_axis_in_top_score_spread`** (`browser_config_fingerprint`, _note_): This experiment-config fingerprint axis is among the top score-spread drivers — compare manifest comparison_fingerprints and member manifests.

### Provider config (`provider_config_fingerprint`)

| Group (short) | run_ids | Pooled mean | Cells | Unstable | Regressions→ | Mode gaps |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `sha256:a21f9f3dfa8d97e31e7f…` | `campaign.examples.browser_evidence_compare.v1__0000` | 0.571024 | 1 | 0 | 0 | 0 |
| `sha256:b5f7c632636d4760febd…` | `campaign.examples.browser_evidence_compare.v1__0001` | 0.361310 | 1 | 0 | 0 | 0 |

### Scoring config (`scoring_config_fingerprint`)

| Group (short) | run_ids | Pooled mean | Cells | Unstable | Regressions→ | Mode gaps |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `sha256:f958bcbda76ceda7438c…` | `campaign.examples.browser_evidence_compare.v1__0000`, `campaign.examples.browser_evidence_compare.v1__0001` | 0.466167 | 2 | 0 | 0 | 0 |

### Execution mode (`execution_mode`)

| Group (short) | run_ids | Pooled mean | Cells | Unstable | Regressions→ | Mode gaps |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `browser_mock` | `campaign.examples.browser_evidence_compare.v1__0000`, `campaign.examples.browser_evidence_compare.v1__0001` | 0.466167 | 2 | 0 | 0 | 0 |

### Prompt registry state (`prompt_registry_state_fingerprint`)

| Group (short) | run_ids | Pooled mean | Cells | Unstable | Regressions→ | Mode gaps |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `sha256:9604a174787655177b3c…` | `campaign.examples.browser_evidence_compare.v1__0000`, `campaign.examples.browser_evidence_compare.v1__0001` | 0.466167 | 2 | 0 | 0 | 0 |

### Browser config (`browser_config_fingerprint`)

| Group (short) | run_ids | Pooled mean | Cells | Unstable | Regressions→ | Mode gaps |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `sha256:bc42b4965253463647d7…` | `campaign.examples.browser_evidence_compare.v1__0001` | 0.361310 | 1 | 0 | 0 | 0 |
| `sha256:dda4aeabb9afaebafd87…` | `campaign.examples.browser_evidence_compare.v1__0000` | 0.571024 | 1 | 0 | 0 | 0 |

### Correlation-style notes (score vs instability)

- **Provider config:** spread **0.209714** on pooled mean; pooled mean score spread 0.209714 (lowest `sha256:b5f7c632636d4760febd…` 0.361310 vs highest `sha256:a21f9f3dfa8d97e31e7f…` 0.571024).
- **Scoring config:** Single group on this axis — no cross-group spread.
- **Execution mode:** Single group on this axis — no cross-group spread.
- **Prompt registry state:** Single group on this axis — no cross-group spread.
- **Browser config:** spread **0.209714** on pooled mean; pooled mean score spread 0.209714 (lowest `sha256:bc42b4965253463647d7…` 0.361310 vs highest `sha256:dda4aeabb9afaebafd87…` 0.571024).

## Browser evidence (member runs)

**browser_mock** file-backed traces (`fixtures/browser_evidence/v1/`). **Playwright** is optional (`[browser]` + env). **MCP** stdio is a **local** JSON bridge to a subprocess — not IDE-hosted or remote capture (`docs/architecture/browser.md`).

### Cross-run contrast (deterministic fixtures)

Compare **signals** (navigation / console / DOM / screenshots) and **extension digests** across members. Multi-step flows often show **network** + **performance** bars; single-page traces may emphasize **accessibility** without network churn. **Playwright** remains optional; **MCP stdio** is a **local** subprocess bridge when used without `fixture_relpath` (see `docs/architecture/browser.md`).

| run_id | suite_ref | Signals | Extension digest |
| --- | --- | --- | --- |
| `campaign.examples.browser_evidence_compare.v1__0000` | `fixtures/benchmarks/browser_checkout.v1.yaml` | nav×3 · console×2 · dom×2 · shot×2 · snap | checkout_flow.v1 · net 14 req/1 fail · a11y 1v · LCP 890ms |
| `campaign.examples.browser_evidence_compare.v1__0001` | `fixtures/benchmarks/browser_form.v1.yaml` | nav×1 · console×1 · dom×2 · shot×1 | form_validation.v1 · a11y 2v |

| Member cell | Evidence | Runner | Signals | DOM snap | Extension digest |
| --- | --- | --- | --- | --- | --- |
| `campaign.examples.browser_evidence_compare.v1__0000 / v-checkout__p-one` | `evidence.checkout_flow.v1` (Abstract trace: Cart → Checkout → Confirm) | `file` | nav×3 · console×2 · dom×2 · shot×2 · snap | yes | checkout_flow.v1 · net 14 req/1 fail · a11y 1v · LCP 890ms |
| `campaign.examples.browser_evidence_compare.v1__0001 / v-form__p-one` | `evidence.form_validation.v1` (Abstract trace: signup form with validation errors) | `file` | nav×1 · console×1 · dom×2 · shot×1 | — | form_validation.v1 · a11y 2v |

### Per-cell traces

#### `campaign.examples.browser_evidence_compare.v1__0000` · `v-checkout__p-one`

- **suite:** `fixtures/benchmarks/browser_checkout.v1.yaml`
- **runner:** `file` (deterministic fixture)
- **evidence:** `evidence.checkout_flow.v1` — Abstract trace: Cart → Checkout → Confirm
- **signals:** nav×3 · console×2 · dom×2 · shot×2 · snap
- **extensions (digest):** checkout_flow.v1 · net 14 req/1 fail · a11y 1v · LCP 890ms
- **dom_snapshot_ref:** `snapshot.checkout.v1`

**Navigation**

- `https://example.test/cart` “Cart” [navigate]
- `https://example.test/checkout` “Checkout” [navigate]
- `https://example.test/checkout/confirm` “Order confirmed” [submit]

**Console**

- `[log]` payment tokenization: ok
- `[warn]` third-party analytics blocked in fixture profile

**DOM excerpts**

| # | Label | Selector | Role | a11y name | Order | Visible text |
| ---: | --- | --- | --- | --- | ---: | --- |
| 1 | Pay now | `button#pay` | `button` | Pay now | 0 | Pay now |
| 2 | Order total | `[data-testid='order-total']` | `statictext` | Order total | 1 | $42.00 |

**HTML snippets** (truncated for Markdown)

_Pay now_ (`button#pay`)

```html
<button type="submit" id="pay">Pay now</button>
```

**Screenshots**

| Seq | Scope | Target | Viewport | DPR | SHA-256 (short) | MIME | Caption |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 0 | `viewport` | — | 390×844 | 2 | `aaaaaaaaaaaa…` | image/png | Fixture: mobile viewport before submit. |
| 1 | `element` | `button#pay` | 390×844 | — | `bbbbbbbbbbbb…` | image/png | Fixture: focused element capture (metadata only). |

**Extensions (structured)**

| Extension block | Summary |
| --- | --- |
| `fixture_profile` | 'checkout_flow.v1' |
| `structured_capture_version` | 1 |
| **network** | req 14, fail 1, last `https://example.test/checkout/confirm` → 200 |
| **accessibility** | notes='One color-contrast issue on secondary link (fixture).', rules_checked=24, violations_count=1 |
| **performance** | dom_content_loaded_ms=420.5, largest_contentful_paint_ms=890.0 |

_Notes:_ Deterministic checkout narrative for browser benchmark realism (no PII, no binaries).

#### `campaign.examples.browser_evidence_compare.v1__0001` · `v-form__p-one`

- **suite:** `fixtures/benchmarks/browser_form.v1.yaml`
- **runner:** `file` (deterministic fixture)
- **evidence:** `evidence.form_validation.v1` — Abstract trace: signup form with validation errors
- **signals:** nav×1 · console×1 · dom×2 · shot×1
- **extensions (digest):** form_validation.v1 · a11y 2v

**Navigation**

- `https://example.test/signup` “Sign up” [navigate]

**Console**

- `[error]` validation failed: email

**DOM excerpts**

| # | Label | Selector | Role | a11y name | Order | Visible text |
| ---: | --- | --- | --- | --- | ---: | --- |
| 1 | Email error | `#email-error` | `alert` | Email format invalid | 0 | Enter a valid email address. |
| 2 | Submit | `button[type=submit]` | `button` | Create account | 1 | Create account |

**Screenshots**

| Seq | Scope | Target | Viewport | DPR | SHA-256 (short) | MIME | Caption |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 0 | `viewport` | — | 1280×720 | — | `cccccccccccc…` | image/png | Fixture: form state after failed submit. |

**Extensions (structured)**

| Extension block | Summary |
| --- | --- |
| `fixture_profile` | 'form_validation.v1' |
| `structured_capture_version` | 1 |
| **accessibility** | notes='Focus order vs DOM order mismatch (fixture).', rules_checked=8, violations_count=2 |

_Notes:_ Stress a11y roles + console errors without navigation churn.

## Provider / backend performance (mean cell score)

Higher is better (simple mean of **total_weighted_score** over all cells using that **backend_kind** across member runs).

| Rank | backend_kind | Mean score | Cells |
| ---: | --- | ---: | ---: |
| 1 | `mock` | 0.466167 | 2 |

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
| 1 | `FT-ABS-LOW` | 1 | Cell total score below the configured low-score threshold. |

## Failure atlas (full taxonomy)

Grouped signals from the analyzed benchmark runs. Paths are relative to the repository root.

## FT-ABS-LOW

Cell total score below the configured low-score threshold.

- `bench.fixtures.browser.form.v1::v-form__p-one`

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
