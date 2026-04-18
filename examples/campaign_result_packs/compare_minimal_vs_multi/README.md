# Example: comparing two campaign result packs

Generated with:

```bash
uv run alwm benchmark campaign compare-packs \
  examples/campaign_result_packs/minimal_offline \
  examples/campaign_result_packs/multi_suite \
  -o examples/campaign_result_packs/compare_minimal_vs_multi \
  --left-label minimal-offline \
  --right-label multi-suite \
  --repo-root .
```

Outputs:

- **`pack-compare.json`** — kind **`campaign_result_pack_comparison`** (schema **`schemas/v1/campaign_result_pack_comparison.schema.json`**). Includes **`comparative_analysis.browser_evidence_comparison`**: here the **left** pack has no **`browser_evidence_member_cells`** rows and the **right** (`multi_suite`) has two mock browser cells, so the JSON and report show **right-only** pairings, DOM/screenshot rollups, and **signals_digest** / **extension_digest** columns (deterministic fixtures; **Playwright** optional; **local MCP stdio** honesty copy when **`runner`** is in extension keys).
- **`pack-compare-report.md`** — human-readable summary (fingerprints, artifact paths, backend means, semantic instability, **browser evidence** subsection, FT-\* deltas, member runs, portability warnings).

Requires the sibling packs **`minimal_offline/`** and **`multi_suite/`** under **`examples/campaign_result_packs/`**. Regenerate those packs from campaign runs if their layout changes.
