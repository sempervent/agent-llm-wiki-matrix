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

Per-cell structured traces written during **browser_mock** execution (see `cells/.../browser_evidence.json`).

| Cell | Evidence | Runner | Excerpts | Screens | DOM snapshot ref | Extension keys |
| --- | --- | --- | ---: | ---: | --- | --- |
| `v-browser__p-one` | `mock-evidence-v-browser__p-one` (Mock browser evidence (v-browser__p-one)) | `mock` | 1 | 1 | — | accessibility, network, runner, structured_capture_version, trace_digest |
| `v-browser__p-two` | `mock-evidence-v-browser__p-two` (Mock browser evidence (v-browser__p-two)) | `mock` | 1 | 1 | — | accessibility, network, runner, structured_capture_version, trace_digest |

## Runtime observability

| Field | Value |
| --- | --- |
| started_at_utc | `2026-04-18T00:45:01Z` |
| finished_at_utc | `2026-04-18T00:45:01Z` |
| duration_seconds | 0.036220 |
| browser_phase_seconds | 0.000779 |
| provider_completion_seconds | 0.000085 |
| evaluation_phase_seconds | 0.006900 |
| judge_phase_seconds | 0.000000 |

### Retry and judge summary

| Field | Value |
| --- | --- |
| retry_policy_max_attempts | None |
| total_judge_invocations | 0 |
| cells_with_judge_parse_fallback | 0 |
