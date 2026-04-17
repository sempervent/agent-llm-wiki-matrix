# Example dataset

Small Markdown wiki pages used to exercise **ingest → evaluate → compare → report** without network access.

- `pages/` — source Markdown files.
- Generated artifacts (JSON + Markdown) live under `../generated/` and are checked in as a reference matrix/report pair.

Reproduce locally from the repository root:

```bash
alwm ingest examples/dataset/pages examples/dataset/thoughts --created-at 1970-01-01T00:00:00Z
alwm evaluate --subject examples/dataset/pages/retrieval-basics.md \
  --rubric examples/v1/rubric.json \
  --out examples/dataset/evals/retrieval-basics.eval.json --id eval-retrieval-basics
alwm evaluate --subject examples/dataset/pages/chunking-strategies.md \
  --rubric examples/v1/rubric.json \
  --out examples/dataset/evals/chunking-strategies.eval.json --id eval-chunking
alwm compare examples/dataset/evals/retrieval-basics.eval.json \
  examples/dataset/evals/chunking-strategies.eval.json \
  --out examples/generated/wiki_matrix.json \
  --out-md examples/generated/wiki_matrix.md \
  --id wiki-matrix-001 \
  --title "Wiki pages (example dataset)"
alwm report --matrix examples/generated/wiki_matrix.json \
  --out-json examples/generated/wiki_report.json \
  --out-md examples/generated/wiki_report.md \
  --id wiki-report-001
```
