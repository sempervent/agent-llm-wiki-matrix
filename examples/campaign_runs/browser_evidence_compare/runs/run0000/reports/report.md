# Report: `Report: Browser file-runner benchmark (checkout fixture) (per-prompt scores)`

- **id:** `campaign.examples.browser_evidence_compare.v1__0000-report`
- **kind:** `model_comparison`
- **period:** `1970-01-01` → `1970-01-01`

## Body

`## Browser file-runner benchmark (checkout fixture) (per-prompt scores)

- **metric:** `total_weighted_rubric_score`
- **shape:** 1×1 (grid)

### Highlights

- See the companion matrix Markdown for the full score grid.
`

## Sources

`- `matrices/grid.json`
- `markdown/matrix.grid.md``

## Browser evidence (fixture summary)

Per-cell **browser_mock** traces (`cells/.../browser_evidence.json`). **Playwright** is optional (live capture). **MCP** stdio is a **local** JSON bridge to a subprocess — not IDE-hosted or remote automation (`docs/architecture/browser.md`).

| Cell | Evidence | Runner | Signals | DOM snap | Extension digest |
| --- | --- | --- | --- | --- | --- |
| `v-checkout__p-one` | `evidence.checkout_flow.v1` (Abstract trace: Cart → Checkout → Confirm) | `file` | nav×3 · console×2 · dom×2 · shot×2 · snap | yes | checkout_flow.v1 · net 14 req/1 fail · a11y 1v · LCP 890ms |

### Browser traces (DOM, screenshots, extensions)

#### Cell `v-checkout__p-one`

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

## Runtime observability

| Field | Value |
| --- | --- |
| started_at_utc | `2026-04-18T01:41:39Z` |
| finished_at_utc | `2026-04-18T01:41:39Z` |
| duration_seconds | 0.004050 |
| browser_phase_seconds | 0.001263 |
| provider_completion_seconds | 0.000015 |
| evaluation_phase_seconds | 0.000475 |
| judge_phase_seconds | 0.000000 |

### Retry and judge summary

| Field | Value |
| --- | --- |
| retry_policy_max_attempts | None |
| total_judge_invocations | 0 |
| cells_with_judge_parse_fallback | 0 |
