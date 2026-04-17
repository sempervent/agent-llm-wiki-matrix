# Benchmark cases (v1)

Each file is a **`benchmark_case`** artifact (see `schemas/v1/benchmark_case.schema.json`): task kind, prompt, **expected artifact kinds** (must be registered `alwm validate` kinds), **rubric reference**, **execution** metadata, and **deterministic fixture mode**.

| File | `task_kind` |
| --- | --- |
| `case.repo.scaffold.v1.json` | `repo_scaffolding` |
| `case.markdown.synthesis.v1.json` | `markdown_synthesis` |
| `case.comparison.matrix.v1.json` | `comparison_matrix` |
| `case.browser.evidence.v1.json` | `browser_evidence` |

Validate:

```bash
alwm validate benchmarks/cases/v1/case.repo.scaffold.v1.json benchmark_case
```

Load in Python: `agent_llm_wiki_matrix.benchmark.cases.load_benchmark_case`.
