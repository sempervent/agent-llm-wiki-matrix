# Reporting workflow

## Report types

| Report | Description |
| --- | --- |
| Weekly summary | Roll-up of experiments, evaluations, and matrix highlights (`templates/report-weekly.md` stub) |
| Model / provider comparison | Side-by-side metrics and weighted scores (`kind: model_comparison`) |
| Agent-stack comparison | Tooling/orchestration differences (`kind: agent_stack`) |
| Browser evidence comparison | Abstracted traces/fixtures compared across runs (`kind: browser_evidence`) |

## Generating a report

1. Produce or obtain a validated **matrix** JSON artifact (`alwm validate … matrix`).
2. Run **`alwm report`** to emit a **report** JSON artifact and filled **`templates/report.md`**:

   ```bash
   alwm report --matrix examples/generated/wiki_matrix.json \
     --out-json examples/generated/wiki_report.json \
     --out-md examples/generated/wiki_report.md \
     --id wiki-report-001
   ```

3. Validate outputs:

   ```bash
   alwm validate examples/generated/wiki_report.json report
   ```

## Matrix Markdown

`alwm compare` accepts **`--out-md`** to render `templates/matrix.md` with a GitHub-flavored Markdown table built from `row_labels`, `col_labels`, and `scores`.

## Templates

- `templates/matrix.md` — placeholders: `TITLE`, `ID`, `MATRIX_KIND`, `METRIC`, `CREATED_AT`, `ROW_LABELS`, `COL_LABELS`, `SCORES_TABLE`.
- `templates/report.md` — placeholders: `TITLE`, `ID`, `REPORT_KIND`, `PERIOD_START`, `PERIOD_END`, `BODY_MARKDOWN`, `SOURCE_REFS`.

## Current state

- `alwm report` builds a structured `Report` JSON and fills `templates/report.md`.
- Weekly automation and richer narrative generation remain incremental improvements on top of the same artifacts.
