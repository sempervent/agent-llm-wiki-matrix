# Examples (documentation)

**Canonical example artifacts and datasets** live in the repository root: **`examples/`** (JSON, Markdown, benchmark suites, campaign outputs, browser evidence samples).

This folder (`docs/examples/`) exists so workflows can link to **“docs vs repo root examples”** without confusion:

- **Use `examples/`** for committed files you validate with `alwm validate` or run through pipelines.
- **Use `docs/workflows/`** for step-by-step commands (e.g. benchmarking, local dev).
- **Use `docs/wiki/`** for short topic indexes (e.g. [benchmark campaigns](../wiki/benchmark-campaigns.md)).
- **Use `docs/audits/`** for capability and drift audits.

For multi-agent handoffs when touching example data, see `docs/workflows/multi-agent-parallel.md`.
