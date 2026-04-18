# Example benchmark suites (v1)

| File | Rubric | Prompts | Variants | Tone |
| --- | --- | --- | --- | --- |
| `campaign.neutral.v1.yaml` | Balanced | q01–q05 | 3 (cli, browser_mock, repo_governed) | General comparison |
| `campaign.failure_heavy.v1.yaml` | Strict | q06–q10 | 2 | Failure / recovery / regression stress |
| `campaign.success_heavy.v1.yaml` | Generous | q11–q15 | 2 | Success / shipping / onboarding |
| `registry.mixed.v1.yaml` | Balanced | one inline + one `prompt_ref` (`bench.sample.prompt.v1`) | 1 | Registry-backed + inline |
| `suite.registry.four_modes.v1.yaml` | Comparison (`comparison.v1`) | four `prompt_ref` tasks (repo, Markdown, matrix, browser fixture) | 1 (`cli`) | Registry-only multi-task smoke |
| `suite.registry.strict_duo.v1.yaml` | Strict | `bench.task.repo_governed.v1` + `bench.task.matrix_reasoning.v1` | 2 (`cli`, `repo_governed`) | Cross-mode deltas under strict scoring |
| `suite.registry.generous_duo.v1.yaml` | Generous | `bench.task.markdown_synthesis.v1` + `bench.task.browser_evidence.v1` | 2 (`cli`, `browser_mock`) | Markdown + browser-tagged outputs |

### Agentic cross-system pack

Five suites under **`agentic/`** compare external agent behaviors (implementation, docs drift, benchmark authoring, browser evidence, multi-agent coordination). Each includes **`success_criteria`**, **`failure_taxonomy_hints`**, **`expected_artifact_kinds`**, and **`taxonomy.determinism`**. See **`docs/workflows/agentic-benchmark-pack.md`** and **`examples/benchmark_suites/v1/agentic/README.md`**.

Committed offline runs: `examples/benchmark_runs/agentic-pack-repo-implementation/`, `agentic-pack-docs-drift/`, `agentic-pack-benchmark-authoring/`, `agentic-pack-browser-interpretation/`, `agentic-pack-multi-agent-coordination/`.

### Taxonomy-tagged suites (task family + budgets + tags)

Each file below sets `taxonomy` (`task_family`, `difficulty`, `determinism`, `tool_requirements`) and usually `tags`, `expected_artifact_kinds`, and optional time/token/retry metadata. See `docs/workflows/benchmarking.md`.

| File | Task family | Notes |
| --- | --- | --- |
| `suite.taxonomy.repo_governance.v1.yaml` | `repo_governance` | Registry: `bench.task.repo_governed.v1` |
| `suite.taxonomy.runtime_config.v1.yaml` | `runtime_config` | Registry: `bench.task.runtime_config.v1` (Docker/Compose/Bake) |
| `suite.taxonomy.documentation.v1.yaml` | `documentation` | Registry: `bench.task.markdown_synthesis.v1` |
| `suite.taxonomy.browser_evidence.v1.yaml` | `browser_evidence` | `browser_mock` variant + registry browser task |
| `suite.taxonomy.matrix_reasoning.v1.yaml` | `matrix_reasoning` | Two variants (`cli`, `repo_governed`) |
| `suite.taxonomy.multi_agent_coordination.v1.yaml` | `multi_agent_coordination` | Registry: `bench.task.multi_agent_coord.v1` |
| `suite.taxonomy.campaign_coordination.v1.yaml` | `campaign` | Inline prompts × three execution modes |
| `suite.taxonomy.integration_stress.v1.yaml` | `integration` | Stress budgets; `stochastic_live` metadata for optional live runs |

Committed example runs: `examples/benchmark_runs/taxonomy-repo-governance/`, `examples/benchmark_runs/taxonomy-runtime-config/`.

After a run, validate the output index: `alwm validate examples/benchmark_runs/<id>/manifest.json benchmark_manifest`.

Run offline (mock) and write `examples/benchmark_runs/<id>/`:

```bash
export ALWM_FIXTURE_MODE=1
alwm benchmark run \
  --definition examples/benchmark_suites/v1/campaign.neutral.v1.yaml \
  --output-dir examples/benchmark_runs/campaign-neutral \
  --created-at 1970-01-01T00:00:00Z \
  --run-id examples-campaign-neutral
```

Repeat for `campaign.failure_heavy.v1.yaml` → `campaign-failure-heavy`, and `campaign.success_heavy.v1.yaml` → `campaign-success-heavy`.

Registry-backed example:

```bash
alwm benchmark run \
  --definition examples/benchmark_suites/v1/registry.mixed.v1.yaml \
  --output-dir examples/benchmark_runs/registry-mixed \
  --created-at 1970-01-01T00:00:00Z \
  --run-id examples-registry-mixed
```

Four-mode registry suite (comparison rubric):

```bash
alwm benchmark run \
  --definition examples/benchmark_suites/v1/suite.registry.four_modes.v1.yaml \
  --output-dir examples/benchmark_runs/registry-four-modes \
  --created-at 1970-01-01T00:00:00Z \
  --run-id examples-registry-four-modes
```

Strict / generous duo suites:

```bash
alwm benchmark run \
  --definition examples/benchmark_suites/v1/suite.registry.strict_duo.v1.yaml \
  --output-dir examples/benchmark_runs/registry-strict-duo \
  --created-at 1970-01-01T00:00:00Z \
  --run-id examples-registry-strict-duo

alwm benchmark run \
  --definition examples/benchmark_suites/v1/suite.registry.generous_duo.v1.yaml \
  --output-dir examples/benchmark_runs/registry-generous-duo \
  --created-at 1970-01-01T00:00:00Z \
  --run-id examples-registry-generous-duo
```
