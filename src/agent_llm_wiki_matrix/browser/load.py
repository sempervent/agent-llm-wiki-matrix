"""Load and validate browser evidence JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from agent_llm_wiki_matrix.browser.models import BrowserEvidence
from agent_llm_wiki_matrix.schema import load_schema, validate_json


def load_browser_evidence(path: Path) -> BrowserEvidence:
    """Load `BrowserEvidence` from JSON, validating against the canonical schema."""
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        msg = "Browser evidence JSON must be an object at the top level"
        raise TypeError(msg)
    schema = load_schema("schemas/v1/browser_evidence.schema.json")
    validate_json(cast(dict[str, Any], data), schema)
    return BrowserEvidence.model_validate(data)
