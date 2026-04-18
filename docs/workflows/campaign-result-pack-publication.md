# End-to-end campaign publication workflow

This page is the **operator checklist** for campaigns: **run → validate artifacts → assemble a result pack → validate the pack → compare (packs or raw directories) → interpret outputs → publish or share**. It complements the **field and CLI reference** in **[benchmark-campaigns.md](benchmark-campaigns.md)** (definitions, outputs, flags).

**Milestone & releases:** [v0.2.5 (shipped)](../releases/v0.2.5.md) · [Roadmap v0.2.5 (complete)](../roadmap/v0.2.5.md) · [Tracking v0.2.5 (closed)](../tracking/v0.2.5-campaign.md) · prior [v0.2.4](../releases/v0.2.4.md) · [v0.2.3](../releases/v0.2.3.md).

**Read next for depth:** **[campaign-walkthrough.md](campaign-walkthrough.md)** (what each file is, using committed trees only). **Verification matrix** (CI vs drift vs live): **[verification.md](verification.md)**. **MkDocs:** **[Home](../index.md)** (publication table) · **[docs-site.md](docs-site.md)** (nav, `just docs-build`, CI).

| Doc | Role |
| --- | --- |
| **[benchmark-campaigns.md](benchmark-campaigns.md)** | Campaign definitions, CLI tables, outputs, result packs, comparisons |
| **[verification.md](verification.md)** | `just ci`, `just validate-artifacts`, fallbacks |
| **[campaign-walkthrough.md](campaign-walkthrough.md)** | Step-through on committed `examples/campaign_runs/` |
| **[examples/campaign_result_packs/README.md](../../examples/campaign_result_packs/README.md)** | Example packs and compare-packs |
| **[examples/campaign_compares/README.md](../../examples/campaign_compares/README.md)** | Campaign-vs-campaign compare (`campaign-compare.json`) |

---

## Workflow at a glance

| Phase | Goal | Typical commands | Committed examples |
| --- | --- | --- | --- |
| **1. Run** | Produce a finished campaign tree | `alwm benchmark campaign run` | `examples/campaign_runs/minimal_offline/`, `examples/campaign_runs/multi_suite/` |
| **2. Validate (campaign)** | Schema + kinds on raw outputs | `alwm validate … campaign_manifest` etc. | Same paths |
| **3. Pack** | Build the **canonical outward-facing bundle** | `alwm benchmark campaign pack` | `examples/campaign_result_packs/minimal_offline/` |
| **4. Validate (pack)** | Pack JSON + on-disk consistency | `alwm validate … campaign_result_pack`, `pack-check` | Pack dirs above |
| **5. Compare** | Diff two packs **or** two campaign dirs | `compare-packs` or `compare` | `examples/campaign_result_packs/compare_minimal_vs_multi/`, `examples/campaign_compares/minimal_offline_vs_multi_suite/` |
| **6. Interpret** | Read fingerprints, scores, FT-\*, browser rows | Markdown + JSON reports | See §6 |
| **7. Publish** | Git, archive, review handoff | §7 | — |

**Default posture:** **offline / deterministic** — use mock backends and `ALWM_FIXTURE_MODE=1` in CI as in **[verification.md](verification.md)**. Live provider or browser paths are **opt-in** (see **[live-verification.md](live-verification.md)**, **[benchmarking.md](benchmarking.md)**).

---

## 1. Run a campaign

Execute the sweep from a **campaign definition** into an output directory:

```bash
uv run alwm benchmark campaign run \
  --definition examples/campaigns/v1/minimal_offline.v1.yaml \
  --output-dir examples/campaign_runs/minimal_offline
```

**Plan without executing member runs** (manifest + `campaign-dry-run.json`, no `runs/runNNNN/`):

```bash
uv run alwm benchmark campaign run --dry-run \
  --definition examples/campaigns/v1/minimal_offline.v1.yaml \
  --output-dir /tmp/campaign-plan
```

Definitions and flags: **[benchmark-campaigns.md](benchmark-campaigns.md)** (Campaign definition + CLI). Multi-suite sample: **`examples/campaign_runs/multi_suite/`** (`README.md` inside).

---

## 2. Validate campaign artifacts

Before packing, confirm the **campaign tree** validates as registered kinds (offline):

```bash
uv run alwm validate examples/campaign_runs/minimal_offline/manifest.json campaign_manifest
uv run alwm validate examples/campaign_runs/minimal_offline/campaign-summary.json campaign_summary
# When present:
uv run alwm validate examples/campaign_runs/minimal_offline/campaign-semantic-summary.json campaign_semantic_summary
uv run alwm validate examples/campaign_runs/minimal_offline/runs/run0000/manifest.json benchmark_manifest
```

**Repository contract sweep** (committed `examples/` + `fixtures/` JSON): from the repo root, **`just validate-artifacts`** (see **[verification.md](verification.md)** — same scope as `pytest tests/test_schema_drift_contracts.py`).

---

## 3. Assemble a result pack

A **result pack** mirrors the campaign layout and adds **`campaign-result-pack.json`** + **`INDEX.md`**. Prefer publishing the **pack**, not only the raw campaign folder.

```bash
uv run alwm benchmark campaign pack examples/campaign_runs/minimal_offline \
  --output-dir /tmp/my-pack \
  --pack-id my-release-2026-04-18 \
  --source-label examples/campaign_runs/minimal_offline
```

| Goal | What to pass |
| --- | --- |
| **Smallest shareable slice** | `--run-index 0` (repeatable) |
| **Full longitudinal compatibility** | Default **`--member-depth full`** |
| **Manifest-only (tiny)** | **`--member-depth manifest`** — `pack-check` may warn |
| **Portable bundle** | Omit **`--record-source-abspath`** (default) |
| **Clear title** | **`--title "…"`** or use campaign manifest title |

Flags and outputs: **[benchmark-campaigns.md](benchmark-campaigns.md)** (Result pack). Example pack: **`examples/campaign_result_packs/minimal_offline/`**.

---

## 4. Validate the pack

**Schema + Pydantic** (registered kinds):

```bash
cd /tmp/my-pack
uv run alwm validate campaign-result-pack.json campaign_result_pack
uv run alwm validate manifest.json campaign_manifest
```

**Structure and consistency** (paths on disk, `campaign_id` alignment, portability hints):

```bash
uv run alwm benchmark campaign pack-check .
uv run alwm benchmark campaign pack-check . --strict
```

Use **`--strict`** when warnings must fail CI. Completeness table: **[benchmark-campaigns.md](benchmark-campaigns.md)** (Result packs — “Completeness”).

**Publication-readiness (reviewers):** Open **`INDEX.md`** first. It includes **For reviewers (read this first)** (what the folder is, suggested reading order), **Scope of this bundle** (member counts, **`membership_scope`**, **`member_depth`**), **What is included** (core vs optional layers), **Publish-ready checklist**, and provenance. **`campaign-result-pack.json`** lists optional artifact paths (for example **`campaign_dry_run_json`**) and derived **`membership_scope`** / **`optional_layers_present`** for machines and diff tools.

**Determinism:** When regenerating committed example packs, pass a fixed **`--created-at`** (for example **`1970-01-01T00:00:00Z`**) so **`created_at`** stays stable.

---

## 5. Compare two bundles

### 5a. Compare two result packs

Emits **`pack-compare.json`** (kind **`campaign_result_pack_comparison`**) + **`pack-compare-report.md`**:

```bash
uv run alwm benchmark campaign compare-packs \
  examples/campaign_result_packs/minimal_offline \
  examples/campaign_result_packs/multi_suite \
  -o /tmp/pack-compare \
  --repo-root .

uv run alwm validate /tmp/pack-compare/pack-compare.json campaign_result_pack_comparison
```

Committed example: **`examples/campaign_result_packs/compare_minimal_vs_multi/`**.

### 5b. Compare two completed campaign directories

No pack required — **`campaign-compare.json`** (kind **`campaign_compare`**) + **`campaign-compare-report.md`**:

```bash
uv run alwm benchmark campaign compare \
  examples/campaign_runs/minimal_offline \
  examples/campaign_runs/multi_suite \
  -o /tmp/campaign-compare \
  --repo-root .

uv run alwm validate /tmp/campaign-compare/campaign-compare.json campaign_compare
```

Committed example: **`examples/campaign_compares/minimal_offline_vs_multi_suite/`** — see **[examples/campaign_compares/README.md](../../examples/campaign_compares/README.md)**.

Details and highlights: **[benchmark-campaigns.md](benchmark-campaigns.md)** (comparing packs and comparing campaign directories).

---

## 6. Interpret outputs

### Single campaign or pack (human order)

1. **`INDEX.md`** (pack) — cold-reader intro, reading order, scope (**`membership_scope`**, subset callouts), **What is included**, **`pack_identity_fingerprint`**, provenance, **Publish-ready checklist**, validation commands, **Comparing two packs**.
2. **`campaign-summary.md`** — rollups and **At a glance** when comparative artifacts exist.
3. **`reports/campaign-report.md`** — executive narrative, fingerprint-axis interpretation, FT-\*, browser evidence sections when present.
4. **`campaign-semantic-summary.md`** — semantic / hybrid judge rollups when emitted.
5. **`reports/campaign-analysis.json`** — machine mirror (not all keys are `alwm validate` kinds; still deterministic to diff).

### Pack comparison (`pack-compare-report.md`)

| Section | Use |
| --- | --- |
| **At a glance** | **`pack-compare.json`** field **`reader_interpretation`** (Markdown **`## At a glance`**): **non-causal** orientation — **what changed**, fingerprint mismatch axes, sweep/spread one-liners (directory compare), **`evidence_strength`**, **`uncertainty_caveats`**. Detailed instability / browser / semantic / FT-\* **counts** are only in **Analysis deltas** (not duplicated in At a glance). |
| **Campaign identity & fingerprints** | Same **`campaign_id`**? Same **`pack_identity_fingerprint`** (logical bundle)? Per-axis **`campaign_experiment_fingerprints`** — matching six hashes ⇒ same sweep *inputs*. |
| **Included artifacts** | Same relative paths for summaries, semantic files, comparative report, analysis JSON. |
| **Comparative analysis** | Backend means, semantic instability counts, **`browser_evidence_comparison`** when browser rows exist. |
| **Failure tags (FT-\*)** | Signal counts left vs right. |
| **Semantic summary totals** | When both sides have semantic summaries. |
| **Member runs** | Run ids only on one side ⇒ different sweeps or subsets. |
| **Portability & completeness** | **`pack-check`** output per side. |

If **`campaign_definition`** or **`suite_definitions`** fingerprints differ, treat runs as **different experiments** even if scores look close.

### Campaign directory comparison (`campaign-compare-report.md`)

Adds the same **`## At a glance`** + **`reader_interpretation`** JSON as pack compare (see table), **sweep dimensions** (which axes *vary* across member runs), and **fingerprint_axis_insights** diffs from each **`campaign-analysis.json`**, plus **Analysis deltas** (scores, instability, FT-\*, browser, semantic) in one block.

**Manual diff:** `diff -ru` on two pack or campaign directories; ignore **`INDEX.md`** churn if only timestamps changed.

---

## 7. Publish or share

- **Git:** commit the **pack** under a stable path (e.g. **`examples/campaign_result_packs/<name>/`**) or attach the compare outputs next to it.
- **Archive:** tarball the pack directory (or full campaign tree if reviewers need raw `runs/`).
- **Review:** reviewers start with **`INDEX.md`**, then **`campaign-summary.md`** and **`reports/campaign-report.md`**.
- **Cite:** point readers at **`campaign-result-pack.json`** (`pack_id`, `pack_identity_fingerprint`) and the **`definition_source_relpath`** in the pack or manifest.

---

## Quick reference

| Step | Command |
| --- | --- |
| Run | `uv run alwm benchmark campaign run --definition … --output-dir …` |
| Validate campaign | `alwm validate <path> <kind>` — see **[benchmark-campaigns.md](benchmark-campaigns.md)** |
| Drift (repo) | `just validate-artifacts` — **[verification.md](verification.md)** |
| Assemble pack | `uv run alwm benchmark campaign pack <campaign_dir> -o <pack_dir> --pack-id …` |
| Validate pack | `alwm validate … campaign_result_pack` + `alwm benchmark campaign pack-check <pack_dir>` |
| Compare packs | `uv run alwm benchmark campaign compare-packs <L> <R> -o <out> [--repo-root .]` |
| Compare campaigns | `uv run alwm benchmark campaign compare <L> <R> -o <out> [--repo-root .]` |

---

## See also

- **[README.md](../../README.md)** — milestone context, verification table, campaign CLI row.
- **[AGENTS.md](../../AGENTS.md)** — contributor expectations, offline campaigns, validation.
- **[verification.md](verification.md)** — `just ci` vs `validate-artifacts`.
- **[benchmark-campaigns.md](benchmark-campaigns.md)** — authoritative CLI and output reference.
- **[docs/wiki/benchmark-campaigns.md](../wiki/benchmark-campaigns.md)** — wiki index.
- **[docs/roadmap/v0.2.4.md](../roadmap/v0.2.4.md)** — publication workflow milestone.
