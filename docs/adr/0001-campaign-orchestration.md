# ADR 0001: Campaign orchestration as a first-class workflow

**Status:** Accepted  
**Date:** 2026-04-17  
**Supersedes / complements:** [docs/architecture/adr/0001-benchmark-campaign-orchestration.md](../architecture/adr/0001-benchmark-campaign-orchestration.md) (same decision; this file lives under `docs/adr/` per repository convention.)

## Context

Repeated `alwm benchmark run` invocations with ad hoc shell scripts are hard to review, easy to drift, and do not produce a single **aggregate manifest** tying together suites, providers, scoring axes, and optional browser overrides. Longitudinal tooling expects **glob-addressable** benchmark manifests under a stable directory layout.

## Decision

1. Introduce a **campaign definition** artifact (`BenchmarkCampaignDefinitionV1` / `campaign_definition`) describing the sweep axes and metadata.
2. Implement **`run_benchmark_campaign`** to expand the sweep and **call `run_benchmark`** for each member run (no forked scoring/matrix logic).
3. Emit a **campaign manifest** (`campaign_manifest` / `benchmark_campaign_manifest`) with **definition fingerprint**, **`campaign_experiment_fingerprints`** (six axes: campaign identity, suite stack, provider files, scoring, browser, registry override), timing, git provenance, run status summary, optional failure records, and pointers to each member **`benchmark_manifest`**.
4. Emit a **campaign summary** (`campaign_summary`) for dashboards and validation.
5. Expose **`alwm benchmark campaign run`** with **`--dry-run`** (plan-only: `campaign-dry-run.json`, no `runs/` trees).

## Consequences

- **Positive:** One command produces a longitudinal-compatible directory; definitions and manifests are diff-friendly; validation aligns with `alwm validate`.
- **Negative:** Large sweeps multiply runtime and disk; operators should **`--dry-run`** first.

## Alternatives considered

- **Shell loops** — rejected: no structured manifest, weak reproducibility.
- **Single mega-benchmark YAML** — rejected: does not compose existing suite files or reuse suite-level definitions.
- **Separate `plan` CLI** — rejected in favor of **`run --dry-run`** to keep one entrypoint.
