# Agentic benchmark pack (v1)

Suites for **cross-system** agent evaluation: implementation planning, docs drift repair, benchmark authoring, browser evidence interpretation, and multi-agent coordination.

Each suite defines:

- **`success_criteria`** — human- or judge-facing pass conditions (copied to manifest).
- **`failure_taxonomy_hints`** — suggested failure labels for longitudinal reports.
- **`expected_artifact_kinds`** — expected `alwm validate` kinds for the harness output.
- **`taxonomy.determinism`** — determinism classification (`deterministic_fixture` for offline mock runs).

See **`docs/workflows/agentic-benchmark-pack.md`** for how to run and compare external systems.

Registry prompts added for this pack: `bench.task.repo_implementation.v1`, `bench.task.docs_drift_repair.v1`, `bench.task.benchmark_authoring.v1`.

Committed example runs: `examples/benchmark_runs/agentic-pack-*/`.
