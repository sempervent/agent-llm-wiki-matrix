# Example artifacts (v1)

These JSON files mirror `fixtures/v1/` and demonstrate the canonical shapes for:

- `thought`, `event`, `experiment`, `evaluation`, `matrix`, `report`, `rubric`, `benchmark_response`, `benchmark_manifest`

Validate locally:

```bash
alwm validate examples/v1/thought.json thought
alwm validate examples/v1/rubric.json rubric
# Benchmark run output index (see examples/benchmark_runs/*/manifest.json):
alwm validate examples/v1/manifest.json benchmark_manifest
```
