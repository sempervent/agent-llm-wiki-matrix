# ADR 0001: First-class benchmark campaign orchestration

**Status:** Accepted  
**Date:** 2026-04-17  
**Context:** Benchmark comparison work (matrices, longitudinal reports, fingerprints) needs **reproducible multi-run sweeps** across suites, providers, scoring backends, execution modes, and browser configs—without ad hoc shell loops or undocumented local state.

## Context

- Single-run harness (`alwm benchmark run`) already emits a standard tree (`cells/`, `matrices/`, `manifest.json` as **`benchmark_manifest`**).
- Longitudinal tooling expects **glob**-addressable benchmark manifests under a stable directory layout.
- Sweeps must be **git-reviewable**: YAML definitions, JSON manifests, and Markdown summaries committed like other artifacts.

## Decision

1. **Campaign definition** — `BenchmarkCampaignDefinitionV1` + `schemas/v1/benchmark_campaign.schema.json` describe the Cartesian sweep (suites × provider refs × eval scoring × browser overrides, with optional execution-mode filter and registry override).
2. **Campaign orchestrator** — `run_benchmark_campaign` in `benchmark/campaign_runner.py` expands the sweep, runs each member with `run_benchmark`, and writes:
   - **`manifest.json`** at campaign root (`BenchmarkCampaignManifest` / **`benchmark_campaign_manifest`**)
   - **`campaign-summary.json`** / **`campaign-summary.md`** (rollup for dashboards and humans)
   - Per-run trees under **`runs/runNNNN/`** (same contract as a standalone benchmark run)
3. **Fingerprints** — The campaign root records **`campaign_definition_fingerprint`** and **`campaign_experiment_fingerprints`** (six per-axis hashes). Member **`comparison_fingerprints`** (six axes, including **prompt registry state**) are copied onto each **`BenchmarkCampaignRunEntry`** for comparability checks across campaign rows.
4. **Planning without execution** — `dry_run=True` records planned run count, writes `campaign-dry-run.json`, and is exposed as **`alwm benchmark campaign run --dry-run`** (same entrypoint as execution; no separate `plan` subcommand).

## Consequences

- **Positive:** One command produces a **longitudinal-compatible** directory; `alwm validate` applies to manifests and summaries; definitions stay in-repo and diff-friendly.
- **Negative:** Large sweeps multiply disk and time; operators should use **`--dry-run`** first and scope `suite_refs` / axes carefully.
