# Campaign result pack comparison

Two **`campaign_result_pack`** trees. **Δ** = right − left (numeric). Structured diff: **`pack-compare.json`**.

- **Left:** `examples/campaign_result_packs/minimal_offline` — `examples/campaign_result_packs/minimal_offline` (`pack_id`: `minimal-offline`)
- **Right:** `examples/campaign_result_packs/multi_suite` — `examples/campaign_result_packs/multi_suite` (`pack_id`: `multi-suite`)
- **Generated:** `2026-04-18T01:59:01Z`

## At a glance

> **Non-causal** — orientation only; confirm in per-campaign reports, manifests, and the **Analysis deltas** section below.

- **Evidence strength (aggregate):** **weak** (heuristic — not a power analysis).

### What changed

- **Different `campaign_id`** — these are different campaign definitions or outputs.
- **Pack identity fingerprint differs** — pack contents or provenance are not the same bundle.
- **Campaign definition fingerprint differs** — the underlying sweep definition changed.
- **Experiment fingerprint axes that differ:** `campaign_definition`, `suite_definitions`.
- **Member runs:** 1 only on left, 2 only on right, 0 in both — overlap affects how directly you can compare pooled tables.

### Experiment fingerprints (mismatch)

Digests **differ** on: `campaign_definition`, `suite_definitions` (configuration / suite / provider / scoring / registry / browser).

_Instability counts, browser trace pairings, semantic rollups, and **FT-*** tables are in **Analysis deltas** — not repeated here._

### Uncertainty & limits

- Comparison uses **aggregates** from each side's `campaign-analysis.json` (when present). This is **not** a paired statistical test.
- Deltas (right − left) describe **reported** counts and means — not proven causal effects.
- When **evidence_strength** is **weak**, treat narratives as **orientation**, not proof.
- **No overlapping member run_ids** — pooled backend/instability rows are **not** paired runs.

## Member run overlap

- **Left count:** 1 · **Right count:** 2
- **In both:** 0 · **Only left:** 1 · **Only right:** 2
- **Run IDs only on left:** `campaign.examples.minimal_offline.v1__0000`
- **Run IDs only on right:** `campaign.examples.multi_suite.v1__0000`, `campaign.examples.multi_suite.v1__0001`

## Identity & fingerprints

| Check | Value |
| --- | --- |
| Same **campaign_id** | **no** |
| **pack_identity_fingerprint** match | **no** |
| **campaign_definition_fingerprint** match | **no** |

### campaign_experiment_fingerprints (per axis)

| Axis | Left | Right | Match |
| --- | --- | --- | --- |
| `browser_configs` | `sha256:591cbc3aa572200862e2f336261f05849fe93c17d226a939565815d0cb075961` | `sha256:591cbc3aa572200862e2f336261f05849fe93c17d226a939565815d0cb075961` | yes |
| `campaign_definition` | `sha256:340780556158635e0b33298b726f530cbc86f7dcfdd8923934bbb14a0734e47b` | `sha256:98d0b9852fa277dc5b164fe14a3711b50be2a72ea5f5fca5ed0dd09fe8072566` | no |
| `prompt_registry_state` | `sha256:d409ed75b3cb355ac6727f09877d7ef98c40adce16e3e8284c6dcfe9c5c3db21` | `sha256:d409ed75b3cb355ac6727f09877d7ef98c40adce16e3e8284c6dcfe9c5c3db21` | yes |
| `provider_configs` | `sha256:69c4ef3c9876f8d46bd609d755baa1bb850cd8d9fdcbdee0748b6e10c36cf5f1` | `sha256:69c4ef3c9876f8d46bd609d755baa1bb850cd8d9fdcbdee0748b6e10c36cf5f1` | yes |
| `scoring_configs` | `sha256:2c7f1b6d79305cde67076936152d80992802d413157de43143bac86c13c21fc8` | `sha256:2c7f1b6d79305cde67076936152d80992802d413157de43143bac86c13c21fc8` | yes |
| `suite_definitions` | `sha256:89fed34c06b5afbe00f18b22f21c268389fdf928f73f446796d8c19666514348` | `sha256:d2b3773206bf3494af78922b52603f56a48e60aea74a7f40998fc98adbafbeca` | no |

## Included artifacts (paths in pack)

| Artifact key | Left | Right | Same path |
| --- | --- | --- | --- |
| `campaign_analysis_json` | `reports/campaign-analysis.json` | `reports/campaign-analysis.json` | yes |
| `campaign_comparative_report_md` | `reports/campaign-report.md` | `reports/campaign-report.md` | yes |
| `campaign_dry_run_json` | `—` | `—` | yes |
| `campaign_manifest` | `manifest.json` | `manifest.json` | yes |
| `campaign_result_pack_json` | `campaign-result-pack.json` | `campaign-result-pack.json` | yes |
| `campaign_semantic_summary_json` | `campaign-semantic-summary.json` | `campaign-semantic-summary.json` | yes |
| `campaign_semantic_summary_md` | `campaign-semantic-summary.md` | `campaign-semantic-summary.md` | yes |
| `campaign_summary_json` | `campaign-summary.json` | `campaign-summary.json` | yes |
| `campaign_summary_md` | `campaign-summary.md` | `campaign-summary.md` | yes |
| `index_md` | `INDEX.md` | `INDEX.md` | yes |

## Analysis deltas (`campaign-analysis.json`)

- **`campaign-analysis.json` on left:** True · **on right:** True

### Pooled backend means

| backend_kind | Left | Right | Δ (R−L) |
| --- | ---: | ---: | ---: |
| `mock` | 0.667276 | 0.410112 | -0.257164 |

### Semantic instability (by scoring_backend)

_No unstable events reported (all counts zero on both sides). Pooled longitudinal counts only — see analysis JSON for definitions._

### Failure tags (FT-*)

**With movement** (Δ ≠ 0 or left ≠ right counts):

| Code | Left signals | Right signals | Δ |
| --- | ---: | ---: | ---: |
| `FT-ABS-LOW` | None | 4 | — |
| `FT-MODE-GAP` | None | 2 | — |

- **Codes only on right:** `FT-ABS-LOW`, `FT-MODE-GAP`

### Browser evidence (`browser_evidence_member_cells`)

Per-cell **`browser_evidence_member_cells`** from each `campaign-analysis.json`: DOM/screenshot counts, digests, extension keys (**fixture/mock** unless you ran a live browser). **`runner`** in extension keys → inspect cell **`browser_evidence`** JSON (**local MCP stdio** bridge, not remote IDE hosting).

**Rollups (analysis rows, not scored cells):**

- **Left:** 0 row(s), **Σ DOM excerpts:** 0, **Σ screenshots:** 0
- **Right:** 2 row(s), **Σ DOM excerpts:** 2, **Σ screenshots:** 2
- **Δ (R−L):** DOM excerpts **2**, screenshots **2**

- **Member run_ids with evidence only on right:** `campaign.examples.multi_suite.v1__0001`

**Pairing** (by suite/cell/benchmark): **0** both · **0** left-only · **2** right-only. Table uses `(suite_ref, cell_id, benchmark_id)`; **Signals** / **extension digest** = captured counts and hashes (not remote MCP).

| suite_ref | cell_id | Pairing | L DOM | R DOM | Δ DOM | L shot | R shot | Δ shot | Runner L | Runner R | Signals (L / R) | Extension digest (L / R) |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| `fixtures/benchmarks/offline.v1.yaml` | `v-browser__p-one` | right only | — | 1 | — | — | 1 | — | — | `mock` | — / nav×2 · console×1 · dom×1 · shot×1 | — / net 0 req/ok · a11y 0v · trace 94de29738ca1 |
| `fixtures/benchmarks/offline.v1.yaml` | `v-browser__p-two` | right only | — | 1 | — | — | 1 | — | — | `mock` | — / nav×2 · console×1 · dom×1 · shot×1 | — / net 0 req/ok · a11y 0v · trace 692a9af2e692 |

**Unpaired cell keys** (present on one side only): 
right → `fixtures/benchmarks/offline.v1.yaml / v-browser__p-one / bench.offline.v1`, `fixtures/benchmarks/offline.v1.yaml / v-browser__p-two / bench.offline.v1`


### Semantic summary (selected numeric Δ)

Full totals in JSON; **Δ** = right − left when both numeric.
- **`cells_flagged_judge_low_confidence`:** 0.0
- **`cells_flagged_repeat_confidence_low`:** 0.0
- **`cells_semantic_or_hybrid`:** 0.0
- **`cells_total`:** 6.0
- **`cells_with_repeat_judge`:** 0.0
- **`low_confidence_cells`:** 0.0

## Portability & completeness

### Left pack

- **member_depth:** `full`
- **longitudinal_member_glob:** `runs/*/manifest.json`
- **source_campaign_dir set:** no (absolute paths reduce portability)
- **included / campaign_run_count:** `1/1`

### Right pack

- **member_depth:** `full`
- **longitudinal_member_glob:** `runs/*/manifest.json`
- **source_campaign_dir set:** no (absolute paths reduce portability)
- **included / campaign_run_count:** `2/2`

_Machine-readable summary: `pack-compare.json` (kind `campaign_result_pack_comparison`)._
