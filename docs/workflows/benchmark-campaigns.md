# Benchmark campaign sweeps

A **campaign** runs multiple **benchmark harness** executions from one **campaign definition** file. Each member run is a normal benchmark output tree (``cells/``, ``matrices/``, ``manifest.json``), so results are **longitudinal-compatible**: point ``alwm benchmark longitudinal`` at ``runs/*/manifest.json`` under the campaign directory (see [longitudinal-reporting.md](longitudinal-reporting.md)). The campaign root adds **`manifest.json`** (**campaign manifest**: **`campaign_definition_fingerprint`**, **`campaign_experiment_fingerprints`** — six axes) and **`campaign-summary.json`** / **`.md`** (**campaign summary**).

**Walkthrough (committed examples):** [campaign-walkthrough.md](campaign-walkthrough.md) · **End-to-end publication:** [campaign-result-pack-publication.md](campaign-result-pack-publication.md) · **Verification:** [verification.md](verification.md) · **Wiki:** [Campaign orchestration (index)](../wiki/campaign-orchestration.md) · **ADR:** [Benchmark campaign orchestration](../architecture/adr/0001-benchmark-campaign-orchestration.md) · **Tracking:** [Campaign orchestration](../tracking/campaign-orchestration.md).

## Campaign definition

YAML or JSON validated by ``schemas/v1/benchmark_campaign.schema.json`` and loaded as ``BenchmarkCampaignDefinitionV1`` (see ``src/agent_llm_wiki_matrix/benchmark/campaign_definitions.py``). Synonyms: ``benchmark_suites`` → ``suite_refs``, ``provider_configs`` → ``provider_config_refs``, ``scoring_configs`` → ``eval_scoring_options``, ``tags`` → ``campaign_tags``.

| Field | Role |
| --- | --- |
| ``suite_refs`` / ``benchmark_suites`` | Repo-relative paths to **benchmark definition** files (each is a full ``BenchmarkDefinitionV1``). |
| ``provider_config_refs`` / ``provider_configs`` | Optional list of providers YAML paths; ``null`` entries use harness default resolution. **Empty list** expands to a single ``null`` (one run with defaults). |
| ``eval_scoring_options`` / ``scoring_configs`` | Optional list of ``eval_scoring`` overrides; ``null`` keeps each suite’s own ``eval_scoring``. **Empty list** expands to one ``null``. |
| ``execution_modes`` | If set, **only variants** whose ``execution_mode`` is in this list are kept (others dropped before the run). |
| ``browser_configs`` | Optional list of ``browser`` blocks merged into **browser_mock** variants. **Empty list** expands to one ``null``. If the suite has no ``browser_mock`` variant, only ``null`` is used (no extra redundant runs). |
| ``campaign_tags`` / ``tags`` | Strings appended to each member definition’s ``tags`` (plus ``campaign:<id>`` and ``campaign_run:NNNN``). |
| ``prompt_registry_ref`` | Optional override for **all** member runs (registry YAML relative to repo root). |
| ``campaign_version``, ``description``, ``owner``, ``created_at``, ``notes`` | Metadata copied into the **campaign manifest** for dashboards and provenance. |
| ``retry_policy``, ``time_budget_seconds``, ``token_budget`` | Hints for external agent runners (harness records; does not auto-retry cells yet). |
| ``expected_artifact_kinds`` | Expected ``alwm validate`` kinds for reviewing outputs (metadata). |

The sweep is the Cartesian product of **suites × provider refs × eval_scoring options × (pruned) browser configs**.

## CLI

**Execute** the full sweep:

```bash
uv run alwm benchmark campaign run \
  --definition examples/campaigns/v1/minimal_offline.v1.yaml \
  --output-dir examples/campaign_runs/minimal_offline
```

**Dry-run** (no member ``runs/``; writes ``campaign-dry-run.json`` plus top-level manifest and summaries):

```bash
uv run alwm benchmark campaign run --dry-run \
  --definition examples/campaigns/v1/minimal_offline.v1.yaml \
  --output-dir /tmp/campaign-plan
```

| Option | Default | Meaning |
| --- | --- | --- |
| ``--created-at`` | ``1970-01-01T00:00:00Z`` | RFC 3339 timestamp for member runs and the campaign manifest. |
| ``--no-fixture-mock`` | off | When set, does **not** force mock providers in fixture mode (for live integration). |
| ``--dry-run`` | off | Plan only: no ``runs/runNNNN/`` trees; still writes ``manifest.json``, ``campaign-summary.*``, ``campaign-dry-run.json``. |

**Offline / deterministic (default):** omit ``--no-fixture-mock`` and use mock backends in suite definitions; keep ``ALWM_FIXTURE_MODE=1`` in CI as today.

### Result pack (publish / compare)

After a campaign finishes, assemble a **markdown-first** **result pack** — the **canonical outward-facing unit** for a completed campaign: a directory that copies key campaign outputs plus **`campaign-result-pack.json`** (machine index) and **`INDEX.md`** (human overview). Prefer citing, archiving, and diffing **the pack** rather than only the raw campaign output tree.

```bash
uv run alwm benchmark campaign pack \
  examples/campaign_runs/minimal_offline \
  -o examples/campaign_result_packs/minimal_offline \
  --pack-id minimal-offline \
  --source-label examples/campaign_runs/minimal_offline
```

| Option | Default | Meaning |
| --- | --- | --- |
| ``--pack-id`` | (required) | Stable id stored in ``campaign-result-pack.json``. |
| ``--source-label`` | off | Optional repo-relative path recorded in the pack (portable provenance). |
| ``--member-depth`` | ``full`` | ``full`` copies entire member run trees (best for **longitudinal** cell loads); ``manifest`` copies only ``runs/runNNNN/manifest.json`` (smaller). |
| ``--run-index`` | all | Repeatable 0-based run index filter. |
| ``--include-failed-members`` | off | Include failed member runs (default: succeeded only). |
| ``--record-source-abspath`` | off | Store absolute source path in JSON (default off for git-friendly bundles). |

Outputs under ``-o`` include ``campaign-result-pack.json`` (kind ``campaign_result_pack``), ``INDEX.md``, and the same relative layout as a campaign tree so ``runs/*/manifest.json`` globs stay familiar. The pack manifest records **provenance** (campaign ``created_at``, definition path, fixture mode, git pointers), **``alwm_version``** (tool that assembled the pack), and **``pack_identity_fingerprint``** (stable hash of bundled experiment identity; comparable across ``pack_id`` / pack assembly timestamps). Example: ``examples/campaign_result_packs/minimal_offline/``.

## Outputs (git-friendly)

Under ``--output-dir``:

| Path | Contents |
| --- | --- |
| ``manifest.json`` | **Campaign manifest** (kinds ``benchmark_campaign_manifest`` or ``campaign_manifest``): ``campaign_definition_fingerprint``, ``campaign_experiment_fingerprints`` (six axes), timing, git provenance, ``run_status_summary``, ``runs[]`` with per-row status and copied **six-axis** ``comparison_fingerprints``, paths to each run’s benchmark ``manifest.json``. |
| ``runs/runNNNN/`` | Full per-run benchmark directory (same layout as ``alwm benchmark run``). Omitted when using ``--dry-run``. |
| ``campaign-summary.json`` | JSON rollup (kinds ``campaign_summary`` or legacy validation path). |
| ``campaign-summary.md`` | Publication-style index: **metadata**, **experiment fingerprints**, **execution context**, **Snapshot digest** (when comparative artifacts ran), **Member run index** table, optional **Generated reports** links. The digest summarizes best/worst mean scores by sweep axis, backend means, semantic instability, mode gaps, **FT-\*** tags, and judge rollups (when ``campaign-semantic-summary.json`` exists). |
| ``campaign-semantic-summary.json`` | **Semantic / hybrid judge rollup** (kind ``campaign_semantic_summary``): per-cell metrics from **evaluation** + **evaluation_judge_provenance**; **totals** split ``Evaluation.judge_low_confidence`` vs repeat ``confidence.low_confidence``; **criterion_instability** (per-criterion **score_range** from ``repeat_aggregation.disagreement``); **instability_highlights** (ranked unstable suites / providers / modes + **confidence_flag_counts**); rollups by suite / provider / mode. Deterministic-only campaigns still emit zeros / empty lists. |
| ``campaign-semantic-summary.md`` | Human-readable mirror: **Campaign semantic summary** title, **Executive snapshot**, threshold flags, criteria, instability hotspots, detailed rollups, per-cell low-confidence table. |
| ``reports/campaign-report.md`` | **Comparative report:** **Executive summary** first, optional **Semantic judge variance** embed, sweep dimensions, member mean-score tables, fingerprint-axis interpretation, backends, instability, mode gaps, **FT-\*** tags, failure atlas. **browser_mock** runs add **Browser evidence** sections as before. |
| ``reports/campaign-analysis.json`` | Machine-readable mirror (``fingerprint_compare_axes``, ``fingerprint_axis_insights`` — per-group **run_count** when varied; **``fingerprint_axis_interpretation``** — **attribution_by_axis** rows add **attribution_label**, **evidence_strength**, **uncertainty_notes**, **metrics** (incl. **min_bucket_cell_count**); **differentiation_overview**, **interpretation_caveats**, spread ranking, hotspots, hints with **signal_class**; schema **1**; not ``alwm validate``). May include ``browser_evidence_member_cells`` and **judge_campaign_semantic**. |
| ``campaign-dry-run.json`` | Only for ``--dry-run``: planned run count + inputs snapshot + ``campaign_definition_fingerprint`` + ``campaign_experiment_fingerprints`` (no ``runs/`` trees). |

Validate:

```bash
uv run alwm validate examples/campaign_runs/minimal_offline/manifest.json campaign_manifest
# equivalent: benchmark_campaign_manifest
uv run alwm validate examples/campaign_runs/minimal_offline/campaign-summary.json campaign_summary
uv run alwm validate examples/campaign_runs/minimal_offline/campaign-semantic-summary.json campaign_semantic_summary
uv run alwm validate examples/campaign_runs/minimal_offline/runs/run0000/manifest.json benchmark_manifest
```

Campaign **definitions** are YAML; for ``alwm validate`` on definitions, export to JSON or rely on ``load_benchmark_campaign_definition`` in code (schema: ``campaign_definition``).

## Longitudinal analysis

From the repo root:

```bash
uv run alwm benchmark longitudinal \
  --runs-glob 'examples/campaign_runs/minimal_offline/runs/*/manifest.json' \
  --out-dir /tmp/campaign-longitudinal
```

## Result packs (publishing and comparison)

**End-to-end publication workflow** (run campaign, validate, pack, compare, interpret, publish): **[campaign-result-pack-publication.md](campaign-result-pack-publication.md)** — single checklist with committed example paths; this section remains the **detailed CLI and output reference**.

A **campaign result pack** is the **canonical outward-facing bundle** for a completed campaign: a **git-friendly** directory that copies the important parts of a finished campaign tree—**campaign manifest**, **summaries**, **semantic summary** (when present), **comparative report** + **analysis JSON** (when present), optional **`campaign-dry-run.json`** (plan-only campaigns), and **selected member runs** (full trees by default). The pack root adds **`campaign-result-pack.json`** (kind **`campaign_result_pack`**) and **`INDEX.md`**. The JSON records which optional layers are included (paths such as **`campaign_dry_run_json`** when the dry-run file was copied). **`INDEX.md`** is written for **cold reviewers**: **Start here** (reading order), **Bundle completeness** (yes/no per layer), **Publish-ready checklist**, provenance, fingerprints, and validation commands.

**What to publish:** the **pack directory**, not only the raw **`examples/campaign_runs/…`** output. The pack is what you **cite, archive, or attach**; it includes **`pack_identity_fingerprint`** and a consistent **artifact inventory** for reviewers.

**Completeness (what “done” usually means):**

| Check | Command / signal |
| --- | --- |
| Pack JSON valid | `alwm validate …/campaign-result-pack.json campaign_result_pack` |
| Campaign manifest valid | `alwm validate …/manifest.json campaign_manifest` |
| Campaign summary valid | `alwm validate …/campaign-summary.json campaign_summary` |
| Optional layers | When semantic files exist: `alwm validate …/campaign-semantic-summary.json campaign_semantic_summary`; confirm **Bundle completeness** in **`INDEX.md`** matches expectations |
| On-disk layout matches manifest | `alwm benchmark campaign pack-check <pack_dir>` (`--strict` for stricter CI) |
| No accidental absolute paths | `source_campaign_dir` absent unless you used `--record-source-abspath` on purpose |
| Member trees sufficient for your audience | `member_depth: full` in pack JSON unless reviewers only need manifests |
| Subset packs explained | If `included_member_count` < `campaign_run_count`, document why in **`notes`** or the PR |
| Repo contracts unchanged | `just validate-artifacts` (swept `examples/` + `fixtures/`) |

Assemble from a completed campaign directory:

```bash
uv run alwm benchmark campaign pack examples/campaign_runs/minimal_offline \
  --output-dir /tmp/campaign-pack \
  --pack-id minimal-offline-2026-04-18 \
  --source-label examples/campaign_runs/minimal_offline
```

| Option | Meaning |
| --- | --- |
| ``--member-depth full`` (default) | Copy each member run tree (longitudinal-compatible: evaluations and responses available under ``runs/runNNNN/``). |
| ``--member-depth manifest`` | Only ``manifest.json`` per member (smaller; longitudinal cell loads may fail). |
| ``--run-index N`` | Repeatable filter by member ``run_index``. |
| ``--include-failed-members`` | Include runs that did not succeed (default: succeeded only). |
| ``--record-source-abspath`` | Store absolute source path in JSON (omit for portable bundles). |
| ``--title`` | Override pack title (default: campaign manifest title). |

Validate (schema + registered kinds):

```bash
uv run alwm validate /tmp/campaign-pack/campaign-result-pack.json campaign_result_pack
```

Completeness and portability (paths on disk, manifest/summary ``campaign_id`` consistency; ``--strict`` flags portability warnings such as manifest-only members):

```bash
uv run alwm benchmark campaign pack-check /tmp/campaign-pack
uv run alwm benchmark campaign pack-check /tmp/campaign-pack --strict
```

**Comparing two packs (CLI):** emit **`pack-compare.json`** (kind **`campaign_result_pack_comparison`**) and **`pack-compare-report.md`** summarizing identity and **campaign_experiment_fingerprints** diffs, included artifact paths, **`campaign-analysis.json`** deltas (backend means, semantic instability counts), **`browser_evidence_comparison`** when **`browser_evidence_member_cells`** exists (paired DOM/screenshot counts, signals/extension digests, extension keys; honest **Playwright** optional / **local MCP stdio** wording), **FT-\*** counts, semantic summary totals (when present), member run ids, **pack-check** portability warnings, and optional **`reader_interpretation`** (non-causal **Reader interpretation** section + JSON block — orientation, not proof). Use **`--repo-root .`** (from the repo root) to store pack paths **relative** to the repo for git-friendly committed reports.

```bash
uv run alwm benchmark campaign compare-packs \
  examples/campaign_result_packs/minimal_offline \
  examples/campaign_result_packs/multi_suite \
  -o /tmp/pack-compare \
  --repo-root .

uv run alwm validate /tmp/pack-compare/pack-compare.json campaign_result_pack_comparison
```

Example output: **`examples/campaign_result_packs/compare_minimal_vs_multi/`**. Manual review: **`INDEX.md`** in each pack still lists fingerprints and validation commands.

**Comparing two completed campaign directories (CLI):** emit **`campaign-compare.json`** (kind **`campaign_compare`**) and **`campaign-compare-report.md`** without building result packs first. The report highlights **sweep dimensions** (which axes vary per manifest), **campaign_experiment_fingerprints** and **fingerprint_axis_insights** (from each **`campaign-analysis.json`**), **pooled backend mean scores**, **semantic instability** counts, the same **`browser_evidence_comparison`** block as pack compare (plus legacy **`browser_evidence`** rollups in JSON), **FT-\*** deltas, **member run_id** overlap, and optional **`reader_interpretation`** (same role as pack compare). Default is **offline** (reads committed JSON only). Use a fixed **`--created-at`** for reproducible committed examples.

```bash
uv run alwm benchmark campaign compare \
  examples/campaign_runs/minimal_offline \
  examples/campaign_runs/multi_suite \
  -o /tmp/campaign-compare \
  --repo-root .

uv run alwm validate /tmp/campaign-compare/campaign-compare.json campaign_compare
```

Committed example: **`examples/campaign_compares/minimal_offline_vs_multi_suite/`** (see **`examples/campaign_compares/README.md`**).

**Longitudinal on a standalone pack:** set ``ALWM_REPO_ROOT`` to the pack directory and use ``--runs-glob 'runs/*/manifest.json'``, or pass a repo-relative glob that points at the pack’s ``runs/*/manifest.json`` (see ``INDEX.md`` inside the pack).

## Examples

- Definitions: ``examples/campaigns/v1/`` (including ``sweep_modes.v1.yaml``, ``multi_suite.v1.yaml``, ``semantic_repeats_offline.v1.yaml`` for semantic judge with ``judge_repeats`` > 1, ``fingerprint_axes_probe.v1.yaml`` for two runs that differ on **scoring_config** fingerprints)
- Fixture suite: ``fixtures/benchmarks/campaign_micro.v1.yaml``
- Sample output: ``examples/campaign_runs/minimal_offline/`` (single member run; regenerate with the CLI above).
- Result pack workflow: **Result packs** section above; example commands in ``examples/campaign_result_packs/README.md``.
- **Campaign vs campaign:** ``examples/campaign_compares/README.md`` (``campaign-compare.json``).
- **Multi-run sample:** ``examples/campaign_runs/multi_suite/`` — two ``suite_ref`` values; shows **At a glance** spreads, mode-gap rows, and FT-* signals in ``campaign-summary.md`` / ``reports/campaign-report.md`` (see ``examples/campaign_runs/multi_suite/README.md``).
