# Browser evidence examples (v1)

Canonical committed traces live under **`fixtures/browser_evidence/v1/`** (this folder mirrors **`export_flow.json`** for `alwm validate` examples). Narratives:

- **`export_flow.json`** — Home → Settings → Export (matches benchmark case `case.browser.evidence.v1`).
- **`checkout_flow.json`** — Cart → Checkout → Confirm (multi-screenshot, structured **extensions**).
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
