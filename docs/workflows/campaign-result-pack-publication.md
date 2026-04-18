# Campaign result pack — publication workflow

A **campaign result pack** is the **canonical outward-facing bundle** for a finished campaign: the same directory layout as a campaign output tree, plus **`campaign-result-pack.json`** (machine index: **`pack_identity_fingerprint`**, member inventory, artifact paths) and **`INDEX.md`** (human overview, checklist, fingerprints, validation commands). **Publish, cite, or archive the pack**—not only the raw **`examples/campaign_runs/…`** folder.

**Related:** [benchmark-campaigns.md](benchmark-campaigns.md) (CLI flags) · [campaign-walkthrough.md](campaign-walkthrough.md) (campaign manifest vs summary vs member manifest) · [verification.md](verification.md) (`just validate-artifacts`).

---

## 1. Assemble a pack

From the repo root, point at a **completed** campaign directory (one that already has **`manifest.json`**, summaries, and usually **`runs/runNNNN/`**):

```bash
uv run alwm benchmark campaign pack examples/campaign_runs/minimal_offline \
  --output-dir /tmp/my-pack \
  --pack-id my-release-2026-04-18 \
  --source-label examples/campaign_runs/minimal_offline
```

**Completeness guidance:**

| Goal | What to pass |
| --- | --- |
| **Smallest shareable slice** | `--run-index 0` (repeatable) to include specific member runs only |
| **Full longitudinal compatibility** | Default **`--member-depth full`** (copies full **`runs/runNNNN/`** trees) |
| **Manifest-only** (tiny, no cells) | **`--member-depth manifest`** — `pack-check` may warn; longitudinal cell loads can fail |
| **Portable bundle (no absolute paths)** | Omit **`--record-source-abspath`** (default) |
| **Clear title in the pack** | **`--title "…"`** or rely on campaign manifest title |

The command writes **`campaign-result-pack.json`**, **`INDEX.md`**, and copies campaign-level + member files into **`--output-dir`**.

---

## 2. Validate the pack

**Schema + Pydantic** (registered `alwm` kinds):

```bash
cd /tmp/my-pack
uv run alwm validate campaign-result-pack.json campaign_result_pack
uv run alwm validate manifest.json campaign_manifest
```

**Structure and consistency** (paths on disk, **`campaign_id`** alignment, portability hints):

```bash
uv run alwm benchmark campaign pack-check .
uv run alwm benchmark campaign pack-check . --strict
```

Use **`--strict`** when the bundle must pass CI-style gates (warnings become errors).

**Repository-wide drift** (optional, from repo root): committed **`examples/`** and **`fixtures/`** — **`just validate-artifacts`**.

---

## 3. Compare two packs

Emit a **comparison artifact** (JSON + Markdown) for two pack directories:

```bash
uv run alwm benchmark campaign compare-packs \
  examples/campaign_result_packs/minimal_offline \
  examples/campaign_result_packs/multi_suite \
  -o /tmp/pack-compare \
  --repo-root .

uv run alwm validate /tmp/pack-compare/pack-compare.json campaign_result_pack_comparison
```

Committed example output: **`examples/campaign_result_packs/compare_minimal_vs_multi/`** (`pack-compare.json`, `pack-compare-report.md`).

---

## 4. Interpret comparison outputs

Open **`pack-compare-report.md`** (human) and **`pack-compare.json`** (machine). Typical reading order:

| Section | What it tells you |
| --- | --- |
| **Campaign identity & fingerprints** | Whether **`campaign_id`** matches; whether **`pack_identity_fingerprint`** matches (same logical bundle ignoring **`pack_id`** / timestamps); per-axis **`campaign_experiment_fingerprints`** — same six hashes ⇒ same sweep *inputs* (definitions, suites, providers, scoring, browser, registry). |
| **Included artifacts** | Whether both packs expose the same relative paths for summaries, semantic files, comparative report, analysis JSON. |
| **Comparative analysis** | Pooled scores and instability-style metrics from **`campaign-analysis.json`** when present (backend means, semantic instability counts, etc.). |
| **Failure tags (FT-*)** | Taxonomy signals aggregated across runs (e.g. low score, mode gap) — compare counts left vs right. |
| **Semantic summary totals** | High-level rollups when semantic summaries exist. |
| **Member runs** | **Only in left** / **only in right** — different sweeps or subset packs. |
| **Portability & completeness** | Output from **`pack-check`** on each side — warnings about manifest-only members, absolute paths, etc. |

If **experiment fingerprints** differ on **`campaign_definition`** or **`suite_definitions`**, treat the two packs as **different experiments** even if scores look similar.

**Manual diff:** follow **Comparing two packs** in each pack’s **`INDEX.md`**, or use `diff -ru` on the two directories (ignore **`INDEX.md`** churn if only timestamps changed).

---

## 5. Publish

- **Git:** commit the pack under a stable path (e.g. **`examples/campaign_result_packs/<name>/`**).
- **Archive:** attach the directory or a tarball to a paper, issue, or release.
- **Review:** reviewers start with **`INDEX.md`**, then **`campaign-summary.md`** and **`reports/campaign-report.md`**.

---

## Quick reference

| Step | Command |
| --- | --- |
| Assemble | `uv run alwm benchmark campaign pack <campaign_dir> -o <pack_dir> --pack-id …` |
| Validate | `alwm validate … campaign_result_pack` + `alwm benchmark campaign pack-check <pack_dir>` |
| Compare | `uv run alwm benchmark campaign compare-packs <left> <right> -o <out> --repo-root .` |
| Drift (repo) | `just validate-artifacts` |
