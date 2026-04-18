# Agentic benchmark pack (cross-system evaluation)

This repository ships a **first-class benchmark pack** for comparing **external agent systems** (IDE agents, headless runners, multi-agent orchestrators) on tasks that mirror real software work: implementation planning, documentation repair, benchmark authoring, browser evidence interpretation, and multi-agent coordination.

## Where it lives

| Path | Role |
| --- | --- |
| `examples/benchmark_suites/v1/agentic/suite.agentic.*.v1.yaml` | Five suite definitions; each includes taxonomy, **success criteria**, **failure taxonomy hints**, **expected artifact kinds**, and **determinism classification** (`taxonomy.determinism`). |
| `prompts/registry.yaml` | Registry prompts `bench.task.repo_implementation.v1`, `bench.task.docs_drift_repair.v1`, `bench.task.benchmark_authoring.v1`; plus existing tasks for browser and multi-agent. |
| `examples/benchmark_runs/agentic-pack-*/` | Committed **offline** (`ALWM_FIXTURE_MODE=1`) example runs for validation and diffing. |

## Determinism classification

Each suite sets **`taxonomy.determinism`**. For this pack, offline runs use **`deterministic_fixture`**: mock backends and (where applicable) file-backed browser evidence produce stable harness outputs so **matrices and reports are comparable** across runs and machines.

When you move to **live** models or Playwright, treat runs as **`stochastic_live`** for interpretation even if scoring remains deterministic—repeat cells and track variance.

## How to compare external agent systems

1. **Align agent labels** — Map each external system to **`variants[].agent_stack`** (or run separate jobs per system with the same definition and different `run_id`).
2. **Run the same definition** — Use one YAML under `examples/benchmark_suites/v1/agentic/`; keep **`rubric_ref`** fixed so scores are comparable.
3. **Use manifest metadata** — After `alwm benchmark run`, read **`manifest.json`**:
   - **`success_criteria`**: checklist for human or LLM-as-judge review of raw responses.
   - **`failure_taxonomy_hints`**: map failures into a shared taxonomy for longitudinal reports (see `docs/workflows/longitudinal-reporting.md` if present).
   - **`expected_artifact_kinds`**: what reviewers should find under each cell when the harness is complete.
   - **`taxonomy.determinism`**: how to interpret score stability.
4. **Score and compare** — Use **`evaluation.json`** / matrices as usual; for systems that **do not** run inside this repo, use the **prompt text** (from `prompts/versions/` via registry) as the external task and compare outputs against the same rubric criteria manually or with a scripted judge.

## Offline reproduction

```bash
export ALWM_FIXTURE_MODE=1
alwm benchmark run \
  --definition examples/benchmark_suites/v1/agentic/suite.agentic.repo_implementation.v1.yaml \
  --output-dir /tmp/agentic-repo \
  --created-at 1970-01-01T00:00:00Z \
  --run-id external-system-a
alwm validate /tmp/agentic-repo/manifest.json benchmark_manifest
```

Repeat for the other suite files under `examples/benchmark_suites/v1/agentic/`.

## Suite index (task intent)

| Suite file | Focus |
| --- | --- |
| `suite.agentic.repo_implementation.v1.yaml` | Bounded implementation plan (paths, tests, verification). |
| `suite.agentic.docs_drift_repair.v1.yaml` | Find and fix documentation drift vs canonical policy. |
| `suite.agentic.benchmark_authoring.v1.yaml` | `BenchmarkDefinitionV1` literacy and authoring. |
| `suite.agentic.browser_interpretation.v1.yaml` | Interpret `browser_evidence` / fixture traces (file-backed runner). |
| `suite.agentic.browser_checkout.v1.yaml` | Checkout narrative (`checkout_flow.json`): multi-screenshot + structured **extensions**. |
| `suite.agentic.multi_agent_coordination.v1.yaml` | Coordination, handoffs, `cli` vs `repo_governed` variants. |

## Cross-links

- Harness behavior and artifact layout: [benchmarking.md](benchmarking.md)  
- Benchmark JSON schema: `schemas/v1/benchmark_definition.schema.json`, `schemas/v1/manifest.schema.json`
