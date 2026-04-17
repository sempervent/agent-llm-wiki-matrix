# Browser evidence examples (v1)

`export_flow.json` matches the narrative used in benchmark case `case.browser.evidence.v1` (Home → Settings → Export; deterministic; no PII).

Validate:

```bash
alwm validate examples/browser_evidence/v1/export_flow.json browser_evidence
```

Render a prompt block:

```bash
alwm browser prompt-block examples/browser_evidence/v1/export_flow.json
```
