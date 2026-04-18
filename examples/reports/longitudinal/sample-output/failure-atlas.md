# Failure atlas

Grouped signals from the analyzed benchmark runs. Paths are relative to the repository root.

## FT-ABS-LOW

Cell total score below the configured low-score threshold.

_No signals in this pass._

## FT-RUN-REG

Run-over-run regression: total score dropped more than the regression delta vs the previous snapshot for the same benchmark + cell.

- `bench.fixtures.longitudinal.v1::v-cli__p-one`

## FT-CRIT-DROP

At least one rubric criterion dropped vs the previous run for that cell.

- `bench.fixtures.longitudinal.v1::v-cli__p-one::brevity`
- `bench.fixtures.longitudinal.v1::v-cli__p-one::grounding`
- `bench.fixtures.longitudinal.v1::v-cli__p-one::structure`
- `bench.fixtures.longitudinal.v1::v-cli__p-one::task_fit`

## FT-RECUR-LOW

Cell scored below the low threshold in at least `min_recurring` distinct runs.

_No signals in this pass._

## FT-MODE-GAP

Within a single run, spread of cell means across execution modes for the same prompt exceeds the mode-gap threshold.

_No signals in this pass._

## FT-PROV-SPLIT

Within a single run, multiple backend kinds present — compare mock vs live paths explicitly when interpreting scores.

_No signals in this pass._

## FT-JUDGE-UNSTABLE

Semantic or hybrid judge flagged low confidence, or repeat-run stdev/range exceeded the configured semantic threshold for that cell.

_No signals in this pass._

## FT-SERIES-SWING

High variance of total score across three or more snapshots for the same benchmark cell (oscillation / instability over time).

_No signals in this pass._
