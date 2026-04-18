# Benchmark campaign sweeps

A **campaign** runs multiple **benchmark harness** executions from one **campaign definition** file. Each member run is a normal benchmark output tree (``cells/``, ``matrices/``, ``manifest.json``), so results are **longitudinal-compatible**: point ``alwm benchmark longitudinal`` at ``runs/*/manifest.json`` under the campaign directory (see [longitudinal-reporting.md](longitudinal-reporting.md)).

**Wiki:** [docs/wiki/campaign-orchestration.md](../wiki/campaign-orchestration.md) · **Workflow (this page)** · **ADR:** [docs/architecture/adr/0001-benchmark-campaign-orchestration.md](../architecture/adr/0001-benchmark-campaign-orchestration.md) · **Tracking:** [docs/tracking/campaign-orchestration.md](../tracking/campaign-orchestration.md).

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

## Outputs (git-friendly)

Under ``--output-dir``:

| Path | Contents |
| --- | --- |
| ``manifest.json`` | **Campaign manifest** (kinds ``benchmark_campaign_manifest`` or ``campaign_manifest``): ``campaign_definition_fingerprint``, ``campaign_experiment_fingerprints`` (six axes), timing, git provenance, ``run_status_summary``, ``runs[]`` with per-row status and copied **six-axis** ``comparison_fingerprints``, paths to each run’s benchmark ``manifest.json``. |
| ``runs/runNNNN/`` | Full per-run benchmark directory (same layout as ``alwm benchmark run``). Omitted when using ``--dry-run``. |
| ``campaign-summary.json`` | JSON rollup (kinds ``campaign_summary`` or legacy validation path). |
| ``campaign-summary.md`` | Markdown table for humans. |
| ``campaign-dry-run.json`` | Only for ``--dry-run``: planned run count + inputs snapshot + ``campaign_definition_fingerprint`` + ``campaign_experiment_fingerprints`` (no ``runs/`` trees). |

Validate:

```bash
uv run alwm validate examples/campaign_runs/minimal_offline/manifest.json campaign_manifest
uv run alwm validate examples/campaign_runs/minimal_offline/campaign-summary.json campaign_summary
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

## Examples

- Definitions: ``examples/campaigns/v1/`` (including ``sweep_modes.v1.yaml``, ``multi_suite.v1.yaml``)
- Fixture suite: ``fixtures/benchmarks/campaign_micro.v1.yaml``
- Sample output: ``examples/campaign_runs/minimal_offline/`` (regenerate with the CLI above).
