"""Typed records for browser execution results and evidence."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ConsoleMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    level: Literal["log", "warn", "error", "debug"]
    text: str


class NavigationStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str = Field(min_length=1)
    title: str | None = None
    action: str | None = Field(
        default=None,
        description="High-level action (navigate, click, submit, …)",
    )


class BrowserEvidence(BaseModel):
    """Structured, serializable capture from a browser session (or fixture)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    id: str = Field(min_length=1)
    title: str | None = None
    navigation_sequence: list[NavigationStep] = Field(min_length=1)
    console_messages: list[ConsoleMessage] = Field(default_factory=list)
    dom_snapshot_ref: str | None = Field(
        default=None,
        description="Opaque id or repo-relative path to a DOM snapshot (future).",
    )
    notes: str | None = None


class BrowserRunRequest(BaseModel):
    """Input to a browser runner (mock, file-backed, or future Playwright/MCP)."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str | None = Field(
        default=None,
        description="Logical id; file runner resolves fixtures/browser_evidence/v1/<id>.json",
    )
    fixture_relpath: str | None = Field(
        default=None,
        description="Repo-relative path to a browser_evidence JSON file.",
    )
    start_url: str | None = None
    steps: list[str] = Field(default_factory=list)


class BrowserRunResult(BaseModel):
    """Output of a browser run: evidence plus runner metadata."""

    model_config = ConfigDict(extra="forbid")

    evidence: BrowserEvidence
    runner: str = Field(min_length=1)
    duration_ms: int = Field(default=0, ge=0)
