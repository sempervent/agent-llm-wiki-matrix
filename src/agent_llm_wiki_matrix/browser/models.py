"""Typed records for browser execution results and evidence."""

from __future__ import annotations

from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class DomExcerpt(BaseModel):
    """Fixture-backed visible text and/or HTML aligned to a selector."""

    model_config = ConfigDict(extra="forbid")

    label: str | None = None
    selector: str | None = None
    visible_text: str | None = Field(
        default=None,
        description="Visible text captured from the DOM.",
    )
    html_snippet: str | None = Field(
        default=None,
        description="Small HTML fragment for auditors.",
    )

    @model_validator(mode="after")
    def _has_content(self) -> Self:
        if not (self.visible_text or self.html_snippet):
            msg = "DomExcerpt requires visible_text and/or html_snippet"
            raise ValueError(msg)
        return self


class ScreenshotMetadata(BaseModel):
    """Metadata for a viewport capture (binary may live outside the repo)."""

    model_config = ConfigDict(extra="forbid")

    relpath: str | None = Field(
        default=None,
        description="Repo-relative path to image or sidecar when committed.",
    )
    content_sha256: str | None = Field(
        default=None,
        description="Hex SHA-256 of image bytes.",
        pattern=r"^[a-f0-9]{64}$",
    )
    viewport_width: int | None = Field(default=None, ge=1)
    viewport_height: int | None = Field(default=None, ge=1)
    mime_type: str | None = None
    caption: str | None = None
    captured_at: str | None = None

    @model_validator(mode="after")
    def _has_identity(self) -> Self:
        if self.relpath is None and self.content_sha256 is None:
            msg = "ScreenshotMetadata requires relpath and/or content_sha256"
            raise ValueError(msg)
        return self


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
        description="Opaque id or repo-relative path to a full DOM snapshot artifact.",
    )
    dom_excerpts: list[DomExcerpt] = Field(
        default_factory=list,
        description="Snippets of visible text/HTML for grounding.",
    )
    screenshots: list[ScreenshotMetadata] = Field(
        default_factory=list,
        description="Screenshot metadata (integrity and layout).",
    )
    extensions: dict[str, Any] | None = Field(
        default=None,
        description="Arbitrary JSON-serializable fields for runners or experiments.",
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
