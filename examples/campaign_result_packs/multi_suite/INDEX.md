# Campaign result pack: `multi-suite`

- **campaign_id:** `campaign.examples.multi_suite.v1`
- **title:** Example — multi-suite sweep (two fixtures)

_This directory is the **canonical outward-facing bundle** for a completed campaign: same layout as a campaign tree, plus **`campaign-result-pack.json`** (machine index) and this **`INDEX.md`** (human overview). **Cite, archive, or attach this pack**—not only the raw campaign output directory._

## Start here (reviewing this bundle cold)

You are looking at a **self-contained publication slice**: campaign-level artifacts plus copied **`runs/runNNNN/`** member trees (or manifest-only stubs). The machine index is **`campaign-result-pack.json`** (`pack_identity_fingerprint`, artifact paths, member inventory).

**Suggested reading order**

1. **`campaign-summary.md`** — Rollup table, sweep overview, headline scores.
2. **`reports/campaign-report.md`** (if present) — Narrative comparative report, fingerprint-axis interpretation, FT-* tags.
3. **`campaign-semantic-summary.md`** (if present) — Hybrid / judge semantic instability and confidence rollups.
4. **`reports/campaign-analysis.json`** (if present) — Machine mirror of analysis (not an `alwm validate` kind; schema version 1). 
5. **`runs/runNNNN/`** — Per-run benchmark manifests, cells, matrices, reports.

## Pack snapshot

- **Pack assembled at:** `1970-01-01T00:00:00Z`
- **Campaign manifest (created_at):** `1970-01-01T00:00:00Z`
- **Campaign definition:** `examples/campaigns/v1/multi_suite.v1.yaml`
- **Fixture mode (forced mock):** `true`
- **Member rows on source campaign:** 2
- **Member runs in this pack:** 2
- **member_depth:** `full`

- **pack_identity_fingerprint:** `sha256:d5f8361795b1218944a51eab111174aad02d1348d917bf8d5af2ae65697739de`
- **alwm_version (pack tool):** `0.2.4`

## Bundle completeness

Which layers are present in **this** directory (paths are relative to the pack root).

| Layer | Path(s) | In this pack | Role |
| --- | --- | ---: | --- |
| Campaign manifest | `manifest.json` | yes | Sweep definition, fingerprints, member rows |
| Campaign summary | `campaign-summary.json`, `campaign-summary.md` | yes | Rollup; validate `campaign_summary` |
| Semantic summary | `campaign-semantic-summary.json`, `.md` | yes | Hybrid / judge instability rollups |
| Comparative report | `reports/campaign-report.md` | yes | Narrative report + fingerprint sections |
| Comparative analysis | `reports/campaign-analysis.json` | yes | Structured analysis mirror |
| Dry-run plan | `campaign-dry-run.json` | **no** | Only when the source campaign was a `--dry-run` plan |
| Pack manifest | `campaign-result-pack.json` | yes | This bundle’s machine index (`campaign_result_pack`) |
| Human index | `INDEX.md` | yes | You are reading it |

## Publication workflow

Treat this directory as the **canonical outward-facing bundle**: what you **archive, cite, or attach**—not only the raw campaign output directory.

1. **Assemble** — `alwm benchmark campaign pack` from a completed campaign.
2. **Validate** — `alwm validate` (schema + kinds) and `alwm benchmark campaign pack-check .` (paths and consistency).
3. **Compare** (optional) — `alwm benchmark campaign compare-packs` for two packs.
4. **Publish** — commit, tarball, supplement, or issue attachment.

Step-by-step: **`docs/workflows/campaign-result-pack-publication.md`** (in the repo).

## Publish-ready checklist

Before sharing outside the repo (or locking a release artifact):

- [ ] `alwm validate campaign-result-pack.json campaign_result_pack` passes
- [ ] `alwm validate manifest.json campaign_manifest` passes
- [ ] `alwm validate campaign-summary.json campaign_summary` passes
- [ ] `alwm benchmark campaign pack-check .` passes (add `--strict` for CI gates)
- [ ] **Optional kinds:** when semantic files are present, `alwm validate campaign-semantic-summary.json campaign_semantic_summary` passes
- [ ] **Portability:** `source_campaign_dir` is absent unless you intentionally record absolute paths (`--record-source-abspath`)
- [ ] **Member depth:** `member_depth` is **full** unless reviewers only need manifests (longitudinal cell loads need full trees)
- [ ] **Completeness:** comparative + semantic layers you expect show **yes** in **Bundle completeness** above
- [ ] **Subset:** if this is a filtered pack, `notes` or PR text explains why runs were omitted
- [ ] **Secrets:** spot-check `cells/`, `request.json`, `browser_evidence.json` for tokens or private paths

## Provenance

Summary of where this bundle came from and how it was stamped:

- **Source label (repo-relative):** `examples/campaign_runs/multi_suite`
- **git_commit:** `1d6cbf5bc0c399ea757e6b38add5f4db5f10d102`
- **git_describe:** `v0.2.4-dirty`
- **definition_fingerprint:** `sha256:98d0b9852fa277dc5b164fe14a3711b50be2a72ea5f5fca5ed0dd09fe8072566`

## Fingerprints (experiment axes)

- **campaign_definition:** `sha256:98d0b9852fa277dc5b164fe14a3711b50be2a72ea5f5fca5ed0dd09fe8072566`
- **suite_definitions:** `sha256:d2b3773206bf3494af78922b52603f56a48e60aea74a7f40998fc98adbafbeca`
- **provider_configs:** `sha256:69c4ef3c9876f8d46bd609d755baa1bb850cd8d9fdcbdee0748b6e10c36cf5f1`
- **scoring_configs:** `sha256:2c7f1b6d79305cde67076936152d80992802d413157de43143bac86c13c21fc8`
- **browser_configs:** `sha256:591cbc3aa572200862e2f336261f05849fe93c17d226a939565815d0cb075961`
- **prompt_registry_state:** `sha256:d409ed75b3cb355ac6727f09877d7ef98c40adce16e3e8284c6dcfe9c5c3db21`

## Artifact inventory

Key files mirror a normal campaign output directory:

- `manifest.json` — campaign manifest
- `campaign-summary.json` / `campaign-summary.md`
- `campaign-semantic-summary.json` — semantic / hybrid rollup
- `reports/campaign-report.md` — comparative report
- `reports/campaign-analysis.json` — comparative analysis JSON
- `campaign-result-pack.json` — this pack manifest (machine)

### Member runs included

| run_index | run_id | suite | benchmark_id | manifest in pack |
| ---: | --- | --- | --- | --- |
| 0 | `campaign.examples.multi_suite.v1__0000` | `fixtures/benchmarks/campaign_micro.v1.yaml` | `bench.fixtures.campaign.micro.v1` | `runs/run0000/manifest.json` |
| 1 | `campaign.examples.multi_suite.v1__0001` | `fixtures/benchmarks/offline.v1.yaml` | `bench.offline.v1` | `runs/run0001/manifest.json` |

## Comparing two packs

1. **Identity:** `pack_identity_fingerprint` matches when the same logical bundle (members, artifact paths, experiment fingerprints, git pointers) was assembled; it ignores `pack_id`, pack `created_at`, and operator `notes`.
2. **Experiment definition:** Compare `campaign_experiment_fingerprints` axes — same six hashes mean the same sweep configuration inputs.
3. **Results:** Diff `campaign-summary.md`, `reports/campaign-report.md`, `campaign-semantic-summary.md`, and `reports/campaign-analysis.json` side by side.
4. **Member-level:** Use `runs/runNNNN/manifest.json` and per-run trees under each pack.
5. **Tree diff:** `diff -ru path/to/packA path/to/packB` (exclude `INDEX.md` churn if only timestamps changed).

## Validate and completeness

Schema validation (JSON Schema + registered kinds):

```bash
alwm validate campaign-result-pack.json campaign_result_pack
alwm validate manifest.json campaign_manifest
alwm validate campaign-summary.json campaign_summary
```

Structural check (paths, manifest/summary consistency, portability hints):

```bash
alwm benchmark campaign pack-check .
alwm benchmark campaign pack-check . --strict
```

## Longitudinal analysis

`alwm benchmark longitudinal` resolves globs from **`ALWM_REPO_ROOT`** (default: current directory). Treat the pack directory as the repo root, or pass a repo-relative glob to the pack path.

```bash
# Standalone pack directory (recommended for published bundles):
cd /path/to/this/pack
ALWM_REPO_ROOT="$(pwd)" alwm benchmark longitudinal --runs-glob 'runs/*/manifest.json' --out-dir /tmp/out
```

```bash
# From a clone where the pack lives under examples/:
alwm benchmark longitudinal --runs-glob 'examples/campaign_result_packs/my_pack/runs/*/manifest.json' --out-dir /tmp/out
```
