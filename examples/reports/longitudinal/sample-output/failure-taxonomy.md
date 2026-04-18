# Failure taxonomy (benchmark longitudinal)

| Code | Description |
| --- | --- |
| `FT-ABS-LOW` | Cell total score below the configured low-score threshold. |
| `FT-RUN-REG` | Run-over-run regression: total score dropped more than the regression delta vs the previous snapshot for the same benchmark + cell. |
| `FT-CRIT-DROP` | At least one rubric criterion dropped vs the previous run for that cell. |
| `FT-RECUR-LOW` | Cell scored below the low threshold in at least `min_recurring` distinct runs. |
| `FT-MODE-GAP` | Within a single run, spread of cell means across execution modes for the same prompt exceeds the mode-gap threshold. |
| `FT-PROV-SPLIT` | Within a single run, multiple backend kinds present — compare mock vs live paths explicitly when interpreting scores. |
| `FT-JUDGE-UNSTABLE` | Semantic or hybrid judge flagged low confidence, or repeat-run stdev/range exceeded the configured semantic threshold for that cell. |
| `FT-SERIES-SWING` | High variance of total score across three or more snapshots for the same benchmark cell (oscillation / instability over time). |
