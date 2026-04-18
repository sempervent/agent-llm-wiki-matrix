# Regression report — Longitudinal benchmark analysis

Condensed view for triage: regressions, criterion drops, recurring lows, run-level score oscillation, and semantic-judge instability.

## Regressions

| Benchmark | Cell | Δ | From → To |
| --- | --- | ---: | --- |
| `bench.fixtures.longitudinal.v1` | `v-cli__p-one` | -0.120000 | `fixtures/longitudinal/paired/run_2026_w02` → `fixtures/longitudinal/paired/run_2026_w03` |

## Criterion drops

| Benchmark | Cell | Criterion | Prev | Curr |
| --- | --- | --- | ---: | ---: |
| `bench.fixtures.longitudinal.v1` | `v-cli__p-one` | `brevity` | 0.820000 | 0.700000 |
| `bench.fixtures.longitudinal.v1` | `v-cli__p-one` | `grounding` | 0.820000 | 0.700000 |
| `bench.fixtures.longitudinal.v1` | `v-cli__p-one` | `structure` | 0.820000 | 0.700000 |
| `bench.fixtures.longitudinal.v1` | `v-cli__p-one` | `task_fit` | 0.820000 | 0.700000 |

## Recurring lows

_None._

## Score oscillation (across runs)

_None above threshold._

## Semantic judge instability (within run)

_None._
