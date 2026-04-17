# Example benchmark suites (v1)

| File | Rubric | Prompts | Variants | Tone |
| --- | --- | --- | --- | --- |
| `campaign.neutral.v1.yaml` | Balanced | q01–q05 | 3 (cli, browser_mock, repo_governed) | General comparison |
| `campaign.failure_heavy.v1.yaml` | Strict | q06–q10 | 2 | Failure / recovery / regression stress |
| `campaign.success_heavy.v1.yaml` | Generous | q11–q15 | 2 | Success / shipping / onboarding |

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
