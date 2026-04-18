# Longitudinal and weekly benchmark reporting

This workflow turns one or more completed benchmark **run directories** (each with `manifest.json`, per-cell `evaluation.json`, and `benchmark_response.json`) into **Markdown-first**, git-friendly artifacts: weekly rollups, run-over-run comparisons, and a **failure atlas** keyed by a small **failure taxonomy**.

## When to use it

- Comparing CI or weekly harness runs for the **same benchmark id** over time.
- Surfacing **regressions**, **improvements**, recurring weak cells, and **execution-mode** spread within a run.
- Publishing human-readable reports next to code without a database.

## CLI

From the repository root (or set `ALWM_REPO_ROOT` to the repo root):

```bash
alwm benchmark longitudinal \
  --runs-glob 'fixtures/longitudinal/paired/*/manifest.json' \
  --out-dir examples/reports/longitudinal/sample-output
```

### Options

| Option | Default | Role |
| --- | --- | --- |
| `--runs-glob` | (required) | Glob pattern **relative to repo root**; typically `.../*/manifest.json` under a folder of runs. |
| `--out-dir` | (required) | Output directory (created if needed). |
| `--title` | `Longitudinal benchmark analysis` | H1 title inside `longitudinal.md`. |
| `--regression-delta` | `0.03` | Minimum score **drop** (same benchmark + cell, consecutive time order) to flag a regression. |
| `--low-score` | `0.55` | Absolute low threshold (per cell) and input to recurring-low detection. |
| `--min-recurring` | `2` | How many distinct runs below `--low-score` trigger recurring-low. |
| `--mode-gap` | `0.12` | Minimum spread across **execution modes** for the same prompt in one run to flag mode-gap. |
| `--semantic-stdev-threshold` | `0.12` | Flag `FT-JUDGE-UNSTABLE` when repeat `total_weighted_stdev` exceeds this. |
| `--semantic-range-threshold` | `0.22` | Flag `FT-JUDGE-UNSTABLE` when `max_range_across_criteria` exceeds this. |
| `--series-swing-threshold` | `0.06` | Flag `FT-SERIES-SWING` when population stdev of total scores exceeds this (needs ≥3 runs). |
| `--min-runs-for-swing` | `3` | Minimum snapshots per cell to evaluate `FT-SERIES-SWING`. |

## Outputs

Written under `--out-dir`:

| File | Contents |
| --- | --- |
| `weekly.md` | Runs grouped by **ISO week**; task families from manifest taxonomy when present; **run labels** table (`run_context.json` git ref, release tag, provider fingerprint). |
| `longitudinal.md` | Full narrative: regressions, improvements, criterion drops, recurring lows, mode spread, score oscillation, semantic instability, backend mix, per-cell variance fields. |
| `regression.md` | Regression-focused report (regressions, criterion drops, recurring lows, oscillation, semantic instability). |
| `provider-comparison.md` | **Comparison fingerprints** table (truncated `sha256:` hashes from each run’s `manifest.json`), then mean scores by **backend_kind** and by **scoring_backend**; notes on `group_snapshots_by` including fingerprint keys. |
| `failure-atlas.md` | Signals grouped by taxonomy code (`FT-*`). |
| `failure-taxonomy.md` | Reference table of all `FT-*` codes. |
| `summary.json` | Machine-readable mirror of counts and rows (for CI or dashboards); includes **`comparison_fingerprints_by_run`**. |

## Failure taxonomy (`FT-*`)

Codes are stable string keys, e.g. `FT-RUN-REG` (run-over-run regression), `FT-CRIT-DROP` (criterion dropped vs previous run), `FT-RECUR-LOW`, `FT-MODE-GAP`, `FT-PROV-SPLIT` (mixed backend kinds in one run), `FT-JUDGE-UNSTABLE` (semantic/hybrid judge repeat variance or low confidence), `FT-SERIES-SWING` (high variance of total score across ≥3 runs for the same cell). See `failure-taxonomy.md` in any bundle or `FAILURE_TAXONOMY` in `src/agent_llm_wiki_matrix/pipelines/longitudinal.py`.

## Comparison fingerprints

Each **`manifest.json`** written by `alwm benchmark run` includes optional **`comparison_fingerprints`**: six **`sha256:`** digests over canonical JSON (suite definition with **title excluded**, resolved prompt set with text digests, sorted per-variant provider configs, effective scoring + judge repeat + judge provider config, sorted browser blocks, **prompt registry state** when `prompt_ref` is used). Use them to confirm two runs are comparable before trusting score deltas. Fingerprints are also copied onto **`BenchmarkCampaignRunEntry`** when using **`alwm benchmark campaign run`**. Campaign roots add **`campaign_experiment_fingerprints`** (per-axis hashes for the campaign definition).

## Grouping runs (Python)

Use `group_snapshots_by(snapshots, key)` with `key` in `git_ref`, `release_tag`, `provider_fingerprint`, `scoring_backend`, `execution_mode`, `task_family`, or **`suite_definition_fingerprint`**, **`prompt_set_fingerprint`**, **`provider_config_fingerprint`**, **`scoring_config_fingerprint`**, **`browser_config_fingerprint`**, **`prompt_registry_state_fingerprint`** (from manifest; unknown when fingerprints are missing). Place optional `run_context.json` beside each run’s `manifest.json` (see `schemas/v1/benchmark_run_context.schema.json`); taxonomy comes from the manifest when recorded.

**Campaign runs:** after `alwm benchmark campaign run`, `reports/campaign-analysis.json` and `reports/campaign-report.md` reuse the same keys (subset documented in `benchmark/campaign_fingerprint_compare.py`) to compare member runs by fingerprint bucket. **`fingerprint_axis_interpretation`** adds **per-axis attribution** with **`attribution_label`** (configuration-dominant / instability-dominant / mixed / inconclusive), **`evidence_strength`** (weak / moderate — from aggregate cell counts, not p-values), **`uncertainty_notes`**, and **`metrics.min_bucket_cell_count`**. The Markdown section spells out **sample limits** and downgrades confidence when evidence is thin. Also: **differentiation overview**, **caveats**, spread ranking, instability hotspots, and **raw signals** grouped by **`signal_class`**. See [benchmark-campaigns.md](benchmark-campaigns.md).

**Longitudinal CLI bundle:** `summary.json` from `alwm benchmark longitudinal` includes the same **`fingerprint_axis_interpretation`** block (derived from loaded snapshots), and **provider-comparison.md** embeds the interpretation Markdown after the comparison-fingerprint table.

## Data sources

- **Manifest** — run metadata, cell paths, and **`comparison_fingerprints`** when produced by a current harness.
- **Evaluations** — `total_weighted_score` and per-criterion scores.
- **Benchmark responses** — variant, prompt, execution mode, backend kind/model (for mode and provider narratives).
- **`evaluation_judge_provenance.json`** — optional; when semantic/hybrid scoring includes repeat runs, variance fields feed instability detection and Markdown.
- **`run_context.json`** — optional; git ref, release tag, provider fingerprint for longitudinal grouping.
- **`matrices/grid.json`** — optional; loaded when present for the run (used in snapshot loading for future matrix-aware reporting).

## Fixtures and examples

- **Synthetic pair:** `fixtures/longitudinal/paired/run_2026_w02/` and `run_2026_w03/` (one cell; deliberate score drop).
- **Rendered example:** `examples/reports/longitudinal/sample-output/` (generated from that pair; safe to regenerate with the CLI command above).
