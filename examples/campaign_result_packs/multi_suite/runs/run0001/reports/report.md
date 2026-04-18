# Report: `Report: Offline benchmark harness (mock backends) (per-prompt scores)`

- **id:** `campaign.examples.multi_suite.v1__0001-report`
- **kind:** `model_comparison`
- **period:** `1970-01-01` → `1970-01-01`

## Body

`## Offline benchmark harness (mock backends) (per-prompt scores)

- **metric:** `total_weighted_rubric_score`
- **shape:** 3×2 (grid)

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
| `v-browser__p-one` | `mock-evidence-v-browser__p-one` (Mock browser evidence (v-browser__p-one)) | `mock` | nav×2 · console×1 · dom×1 · shot×1 | — | net 0 req/ok · a11y 0v · trace 94de29738ca1 |
| `v-browser__p-two` | `mock-evidence-v-browser__p-two` (Mock browser evidence (v-browser__p-two)) | `mock` | nav×2 · console×1 · dom×1 · shot×1 | — | net 0 req/ok · a11y 0v · trace 692a9af2e692 |

### Browser traces (DOM, screenshots, extensions)

#### Cell `v-browser__p-one`

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

#### Cell `v-browser__p-two`

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

## Runtime observability

| Field | Value |
| --- | --- |
| started_at_utc | `2026-04-18T01:58:47Z` |
| finished_at_utc | `2026-04-18T01:58:47Z` |
| duration_seconds | 0.006387 |
| browser_phase_seconds | 0.000175 |
| provider_completion_seconds | 0.000021 |
| evaluation_phase_seconds | 0.001011 |
| judge_phase_seconds | 0.000000 |

### Retry and judge summary

| Field | Value |
| --- | --- |
| retry_policy_max_attempts | None |
| total_judge_invocations | 0 |
| cells_with_judge_parse_fallback | 0 |
