# Longitudinal benchmark analysis

## Regressions (run-over-run)

| Benchmark | Cell | Δ score | Previous | Current | From → To |
| --- | --- | ---: | ---: | ---: | --- |
| `bench.fixtures.longitudinal.v1` | `v-cli__p-one` | -0.120000 | 0.820000 | 0.700000 | `fixtures/longitudinal/paired/run_2026_w02` → `fixtures/longitudinal/paired/run_2026_w03` |

## Improvements (run-over-run)

_None detected at current thresholds._

## Criterion-level drops

| Benchmark | Cell | Criterion | Prev | Curr |
| --- | --- | --- | ---: | ---: |
| `bench.fixtures.longitudinal.v1` | `v-cli__p-one` | `brevity` | 0.820000 | 0.700000 |
| `bench.fixtures.longitudinal.v1` | `v-cli__p-one` | `grounding` | 0.820000 | 0.700000 |
| `bench.fixtures.longitudinal.v1` | `v-cli__p-one` | `structure` | 0.820000 | 0.700000 |
| `bench.fixtures.longitudinal.v1` | `v-cli__p-one` | `task_fit` | 0.820000 | 0.700000 |

## Recurring low scores

_None._

## Execution mode spread (same prompt, one run)

_No multi-mode spreads above threshold._

## Score oscillation (across runs)

_None above threshold (needs at least three snapshots per cell)._

## Semantic / hybrid instability (within-run)

Rows appear when thresholds flag `FT-JUDGE-UNSTABLE` (see failure taxonomy).

_None above thresholds._

## Provider / backend mix

Per run, cells may use `mock`, `ollama`, or `openai_compatible`. Treat cross-kind comparisons as indicative only unless rubrics and prompts are held constant.

- `longitudinal-w02` (`bench.fixtures.longitudinal.v1`): backends mock
- `longitudinal-w03` (`bench.fixtures.longitudinal.v1`): backends mock

## All cells: semantic variance fields (when present)

_No semantic/hybrid provenance with variance metadata in this bundle._
