# Browser evidence examples (v1)

Canonical committed traces live under **`fixtures/browser_evidence/v1/`** (this folder mirrors **`export_flow.json`** for `alwm validate` examples). Narratives:

- **`export_flow.json`** — Home → Settings → Export (matches benchmark case `case.browser.evidence.v1`).
- **`checkout_flow.json`** — Cart → Checkout → Confirm (multi-screenshot, structured **extensions**: network / accessibility / performance).
- **`form_validation.json`** — Single-page form errors (a11y roles + console).

Validate:

```bash
alwm validate examples/browser_evidence/v1/export_flow.json browser_evidence
alwm validate fixtures/browser_evidence/v1/checkout_flow.json browser_evidence
```

Render a prompt block:

```bash
alwm browser prompt-block examples/browser_evidence/v1/export_flow.json
```

## MCP stdio (local, optional)

With **`uv pip install -e ".[dev]"`**, you can exercise the **same** JSON through the **MCP stdio** path (real protocol client + local subprocess; **not** remote or IDE-hosted):

```bash
export ALWM_MCP_BROWSER_COMMAND="python fixtures/mcp_servers/stdio_browser_evidence_server.py"
uv run alwm browser run-mcp --stdio --step alwm:checkout_flow
# or: --step alwm:form_validation
```

The shipped server maps **`--step alwm:…`** / URL hints to **`checkout_flow.json`** / **`form_validation.json`** / **`export_flow.json`** — see **`docs/architecture/browser.md`**. That path proves MCP wiring and **`BrowserEvidence`** validation; it does **not** drive a live browser. For live capture, use **Playwright** (`[browser]` extra), documented in **`docs/workflows/live-verification.md`**.

**Interpretation rubrics:** **`examples/dataset/rubrics/browser_realism.v1.json`** scores how well an answer uses the **structured trace**; it does not, by itself, mean the trace was captured from a real DOM session.

**Campaign-level comparison:** committed output **`examples/campaign_runs/browser_evidence_compare/`** (definition **`examples/campaigns/v1/browser_evidence_compare.v1.yaml`**) shows **Cross-run contrast** in **`reports/campaign-report.md`** for checkout vs form fixtures without a live browser.
