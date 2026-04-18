# Campaign result pack: `multi-suite`

**campaign_id:** `campaign.examples.multi_suite.v1` · **title:** Example — multi-suite sweep (two fixtures)

## For reviewers (read this first)

**What this is:** A **frozen, portable slice** of a finished campaign—the same directory layout as a harness output tree, plus **`campaign-result-pack.json`** (machine index) and this **`INDEX.md`**. Use it to **review, cite, archive, or attach** results — preferred handoff, not only the raw campaign folder.

**Suggested reading order** (about 10–20 minutes for a typical pack):

1. **`campaign-summary.md`** — Rollups, sweep overview, headline scores.
2. **`reports/campaign-report.md`** — When present: narrative comparative report and fingerprint-axis interpretation.
3. **`campaign-semantic-summary.md`** — When present: hybrid / judge instability and confidence rollups.
4. **`reports/campaign-analysis.json`** — When present: machine-readable analysis mirror.
5. **`runs/runNNNN/`** — Per-run manifests, cells, matrices, and reports.

**Machine index:** `campaign-result-pack.json` records `pack_identity_fingerprint`, member inventory, optional layer paths, and `membership_scope` / `optional_layers_present` when emitted by this tool version.

## Scope of this bundle

| | |
| --- | --- |
| **member_depth** | `full` — full per-run trees (default; needed for longitudinal cell loads). |
| **Member runs** | **2** copied **of 2** campaign manifest row(s) · `membership_scope`: **`all_runs`** |
| **Pack assembled** | `1970-01-01T00:00:00Z` |

- **Campaign manifest timestamp:** `1970-01-01T00:00:00Z`
- **Campaign definition:** `examples/campaigns/v1/multi_suite.v1.yaml`
- **Fixture mode (forced mock):** `true`
- **pack_identity_fingerprint:** `sha256:c3947bc1509720962e40d617c6ca76d71635efb748441a966db7cd0df8f2e6b2`
- **alwm_version (assembler):** `0.2.5`

_Every campaign manifest member row is represented in this pack (`included_member_count` equals `campaign_run_count`)._

## What is included

**Core (always in a pack):** `manifest.json`, `campaign-summary.json`, `campaign-summary.md`, `campaign-result-pack.json`, this index, and the member run trees listed under **Member runs included** (or manifest stubs when `member_depth` is `manifest`).

**Optional layers in this directory:**

- `reports/campaign-analysis.json` — structured analysis mirror (not an `alwm validate` kind)
- `reports/campaign-report.md` — narrative + fingerprint interpretation
- `campaign-semantic-summary.{json,md}` — hybrid / judge rollups

## Publication workflow

1. **Validate** — `alwm validate` on the pack manifest and key kinds; `alwm benchmark campaign pack-check .` for on-disk consistency.
2. **Compare** (optional) — `alwm benchmark campaign compare-packs` vs another pack.
3. **Publish** — commit, archive, or attach this directory.

Full operator checklist: **`docs/workflows/campaign-result-pack-publication.md`** (in the repository).

## Publish-ready checklist

- [ ] `alwm validate campaign-result-pack.json campaign_result_pack`
- [ ] `alwm validate manifest.json campaign_manifest`
- [ ] `alwm validate campaign-summary.json campaign_summary`
- [ ] `alwm benchmark campaign pack-check .` (`--strict` if warnings must fail CI)
- [ ] **Optional layers:** validate semantic JSON when present (`alwm validate campaign-semantic-summary.json campaign_semantic_summary`)
- [ ] **Portability:** no accidental `source_campaign_dir` unless intended
- [ ] **Subset:** if filtered, **`notes`** or cover text explains omissions
- [ ] **Secrets:** spot-check `cells/`, `request.json`, `browser_evidence.json`

## Provenance

- **Source label (repo-relative):** `examples/campaign_runs/multi_suite`
- **git_commit:** `78ab7d2e11d5cb179271c2b6a0894f2ecc595489`
- **git_describe:** `v0.2.4-dirty`
- **definition_fingerprint:** `sha256:98d0b9852fa277dc5b164fe14a3711b50be2a72ea5f5fca5ed0dd09fe8072566`

## Fingerprints (experiment axes)

- **campaign_definition:** `sha256:98d0b9852fa277dc5b164fe14a3711b50be2a72ea5f5fca5ed0dd09fe8072566`
- **suite_definitions:** `sha256:d2b3773206bf3494af78922b52603f56a48e60aea74a7f40998fc98adbafbeca`
- **provider_configs:** `sha256:69c4ef3c9876f8d46bd609d755baa1bb850cd8d9fdcbdee0748b6e10c36cf5f1`
- **scoring_configs:** `sha256:2c7f1b6d79305cde67076936152d80992802d413157de43143bac86c13c21fc8`
- **browser_configs:** `sha256:591cbc3aa572200862e2f336261f05849fe93c17d226a939565815d0cb075961`
- **prompt_registry_state:** `sha256:d409ed75b3cb355ac6727f09877d7ef98c40adce16e3e8284c6dcfe9c5c3db21`

## Member runs included

| run_index | run_id | suite | benchmark_id | manifest in pack |
| ---: | --- | --- | --- | --- |
| 0 | `campaign.examples.multi_suite.v1__0000` | `fixtures/benchmarks/campaign_micro.v1.yaml` | `bench.fixtures.campaign.micro.v1` | `runs/run0000/manifest.json` |
| 1 | `campaign.examples.multi_suite.v1__0001` | `fixtures/benchmarks/offline.v1.yaml` | `bench.offline.v1` | `runs/run0001/manifest.json` |

## Comparing two packs

1. **Identity:** `pack_identity_fingerprint` matches when the same logical bundle was assembled (ignores `pack_id`, pack `created_at`, `notes`).
2. **Experiment:** same **`campaign_experiment_fingerprints`** ⇒ same sweep inputs.
3. **Results:** diff summaries, `reports/campaign-report.md`, semantic summary, `reports/campaign-analysis.json`.
4. **Members:** compare `runs/runNNNN/` trees.
5. **Tree:** `diff -ru packA packB` (skip `INDEX.md` if only timestamp churn).

## Validate

```bash
alwm validate campaign-result-pack.json campaign_result_pack
alwm validate manifest.json campaign_manifest
alwm validate campaign-summary.json campaign_summary
alwm benchmark campaign pack-check .
alwm benchmark campaign pack-check . --strict
```

## Longitudinal analysis

`alwm benchmark longitudinal` uses **`ALWM_REPO_ROOT`** (default: cwd). For a standalone pack, `cd` into it or pass a repo-relative glob.

```bash
cd /path/to/this/pack
ALWM_REPO_ROOT="$(pwd)" alwm benchmark longitudinal --runs-glob 'runs/*/manifest.json' --out-dir /tmp/out
```

```bash
alwm benchmark longitudinal --runs-glob 'examples/campaign_result_packs/<pack>/runs/*/manifest.json' --out-dir /tmp/out
```
