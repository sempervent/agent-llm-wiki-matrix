# Campaign result packs

This directory holds **example packs** — the **canonical outward-facing bundles** you publish, cite, or archive after a campaign finishes. A pack is **not** the same as the raw campaign output folder under **`examples/campaign_runs/`** alone: assembling a pack adds **`campaign-result-pack.json`** (machine index: optional layer paths, **`membership_scope`**, **`optional_layers_present`**) and **`INDEX.md`** (**For reviewers** intro, reading order, **Scope** / **What is included**, publish checklist, provenance, fingerprints, compare/validate commands).

**End-to-end publication workflow** (run campaign, validate artifacts, assemble pack, compare, interpret, share): **[docs/workflows/campaign-result-pack-publication.md](../docs/workflows/campaign-result-pack-publication.md)**. **CLI and field reference:** **[docs/workflows/benchmark-campaigns.md](../docs/workflows/benchmark-campaigns.md)** (Result packs). **Verification** (`just ci`, `validate-artifacts`): **[docs/workflows/verification.md](../docs/workflows/verification.md)**.

Use **`alwm benchmark campaign pack`** to copy a **completed** campaign directory into a publishable tree: same layout as a campaign output directory, plus the pack manifest and **`INDEX.md`**. Contents include the campaign manifest, summaries, semantic rollup (if present), comparative report + analysis JSON (if present), and selected **`runs/runNNNN/`** member trees (full or manifest-only).

## Example: assemble from committed campaign output

```bash
uv run alwm benchmark campaign pack examples/campaign_runs/minimal_offline \
  --output-dir /tmp/my-pack \
  --pack-id minimal-offline-example \
  --source-label examples/campaign_runs/minimal_offline
```

Then:

```bash
uv run alwm validate /tmp/my-pack/campaign-result-pack.json campaign_result_pack
uv run alwm benchmark campaign pack-check /tmp/my-pack
```

**Compare two packs** (Markdown + JSON, fingerprints, scores, FT-\*, portability):

```bash
uv run alwm benchmark campaign compare-packs \
  examples/campaign_result_packs/minimal_offline \
  examples/campaign_result_packs/multi_suite \
  -o /tmp/pack-compare \
  --repo-root .
uv run alwm validate /tmp/pack-compare/pack-compare.json campaign_result_pack_comparison
```

Committed example: **`compare_minimal_vs_multi/`** (see **`README.md`** inside).

Full field and flag reference: **`docs/workflows/benchmark-campaigns.md`** (sections **Result pack** and **Result packs**). Tests: **`tests/test_campaign_result_pack.py`**, **`tests/test_campaign_result_pack_compare.py`**.
