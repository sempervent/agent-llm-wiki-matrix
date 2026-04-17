# Example benchmark runs (committed)

These directories are **offline mock runs** produced with `ALWM_FIXTURE_MODE=1` so CI stays deterministic.

| Directory | Suite definition |
| --- | --- |
| `campaign-neutral/` | `examples/benchmark_suites/v1/campaign.neutral.v1.yaml` |
| `campaign-failure-heavy/` | `examples/benchmark_suites/v1/campaign.failure_heavy.v1.yaml` |
| `campaign-success-heavy/` | `examples/benchmark_suites/v1/campaign.success_heavy.v1.yaml` |

Regenerate (from repo root):

```bash
export ALWM_FIXTURE_MODE=1
alwm benchmark run \
  --definition examples/benchmark_suites/v1/campaign.neutral.v1.yaml \
  --output-dir examples/benchmark_runs/campaign-neutral \
  --created-at 1970-01-01T00:00:00Z \
  --run-id examples-campaign-neutral
# …repeat for failure-heavy and success-heavy suites
```
