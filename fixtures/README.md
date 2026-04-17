# Fixtures

Deterministic JSON under `fixtures/v1/` validates against `schemas/v1/*.schema.json` and `src/agent_llm_wiki_matrix/models.py` (see `tests/test_domain.py`).

**Browser evidence:** `fixtures/browser_evidence/v1/*.json` (`BrowserEvidence` schema) for offline browser-style traces; use with `FileBrowserRunner` or `alwm browser prompt-block`.

Do not point integration tests at live model endpoints without explicit opt-in; prefer `ALWM_FIXTURE_MODE` for future pipeline tests.
