"""Optional ``run_context.json`` for longitudinal grouping (git ref, release tag, provider)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict


class BenchmarkRunContextV1(BaseModel):
    """Optional metadata for longitudinal grouping (not written by default harness)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    git_ref: str | None = None
    release_tag: str | None = None
    provider_fingerprint: str | None = None
    notes: str | None = None


def load_run_context_optional(run_root: Path) -> BenchmarkRunContextV1 | None:
    p = run_root / "run_context.json"
    if not p.is_file():
        return None
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        msg = "run_context.json must be a JSON object"
        raise TypeError(msg)
    return BenchmarkRunContextV1.model_validate(raw)
