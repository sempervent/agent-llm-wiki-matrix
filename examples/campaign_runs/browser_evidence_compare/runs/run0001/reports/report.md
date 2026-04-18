# Report: `Report: Browser file-runner benchmark (form validation fixture) (per-prompt scores)`

- **id:** `campaign.examples.browser_evidence_compare.v1__0001-report`
- **kind:** `model_comparison`
- **period:** `1970-01-01` → `1970-01-01`

## Body

`## Browser file-runner benchmark (form validation fixture) (per-prompt scores)

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
| `v-form__p-one` | `evidence.form_validation.v1` (Abstract trace: signup form with validation errors) | `file` | nav×1 · console×1 · dom×2 · shot×1 | — | form_validation.v1 · a11y 2v |

### Browser traces (DOM, screenshots, extensions)

#### Cell `v-form__p-one`

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

## Runtime observability

| Field | Value |
| --- | --- |
| started_at_utc | `2026-04-18T01:11:09Z` |
| finished_at_utc | `2026-04-18T01:11:09Z` |
| duration_seconds | 0.013046 |
| browser_phase_seconds | 0.001869 |
| provider_completion_seconds | 0.000016 |
| evaluation_phase_seconds | 0.002902 |
| judge_phase_seconds | 0.000000 |

### Retry and judge summary

| Field | Value |
| --- | --- |
| retry_policy_max_attempts | None |
| total_judge_invocations | 0 |
| cells_with_judge_parse_fallback | 0 |
