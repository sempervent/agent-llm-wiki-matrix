# Example dataset (prompts + rubrics)

This directory holds **canonical content** for documentation and larger benchmark examples:

| Path | Contents |
| --- | --- |
| `prompts/catalog.v1.yaml` | **15** stable prompts (`q01`–`q15`): neutral (q01–q05), failure/recovery themed (q06–q10), success/checklist themed (q11–q15). |
| `rubrics/balanced.v1.json` | Three-criterion **balanced** rubric (`rubric.examples.balanced.v1`). |
| `rubrics/strict.v1.json` | Four-criterion **strict** rubric for failure-heavy suites (`rubric.examples.strict.v1`). |
| `rubrics/generous.v1.json` | Two-criterion **generous** rubric for success-heavy suites (`rubric.examples.generous.v1`). |
| `rubrics/comparison.v1.json` | Four-criterion comparison rubric (`rubric.examples.comparison.v1`). |
| `rubrics/browser_realism.v1.json` | Browser interpretation: **grounding**, **hallucination_resistance**, **source_fidelity** (`rubric.examples.browser_realism.v1`). |

Benchmark suites that use these live under `examples/benchmark_suites/v1/`; generated mock runs are committed under `examples/benchmark_runs/`.

Validate a rubric:

```bash
alwm validate examples/dataset/rubrics/balanced.v1.json rubric
```
