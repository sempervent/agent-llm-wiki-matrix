"""Domain models (Pydantic) aligned with JSON Schemas under schemas/v1/."""

from __future__ import annotations

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Thought(BaseModel):
    """Atomic idea or hypothesis."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str
    body_markdown: str
    created_at: str = Field(description="RFC 3339 date-time")
    status: Literal["draft", "published"] = "draft"
    tags: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)


class Event(BaseModel):
    """Timestamped occurrence (run, incident, observation)."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    kind: Literal["run", "incident", "observation", "other"]
    title: str
    occurred_at: str = Field(description="RFC 3339 date-time")
    summary_markdown: str
    refs: list[str] = Field(default_factory=list)


class Experiment(BaseModel):
    """Structured experiment protocol and lifecycle."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str
    hypothesis: str
    protocol_markdown: str
    parameters: dict[str, float | int | str | bool] = Field(default_factory=dict)
    status: Literal["planned", "running", "completed", "aborted"] = "planned"
    started_at: str = Field(description="RFC 3339 date-time")
    ended_at: str | None = Field(default=None, description="RFC 3339 date-time when completed")
    tags: list[str] = Field(default_factory=list)


class Evaluation(BaseModel):
    """Rubric-scored assessment of a subject artifact or run."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    subject_ref: str = Field(description="Repo-relative path or stable logical id")
    rubric_id: str
    scores: dict[str, float] = Field(description="Criterion id -> raw score")
    weights: dict[str, float] = Field(description="Criterion id -> weight")
    total_weighted_score: float
    evaluated_at: str = Field(description="RFC 3339 date-time")
    evaluator: Literal["human", "agent", "pipeline"]
    notes_markdown: str | None = None


class ComparisonMatrix(BaseModel):
    """Pairwise or grid comparison of labeled dimensions."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str
    matrix_kind: Literal["pairwise", "grid"]
    row_labels: list[str] = Field(min_length=1)
    col_labels: list[str] = Field(min_length=1)
    scores: list[list[float]] = Field(
        description="Row-major scores[row][col]; length must match labels",
    )
    metric: str
    created_at: str = Field(description="RFC 3339 date-time")

    @model_validator(mode="after")
    def scores_match_labels(self) -> Self:
        if len(self.scores) != len(self.row_labels):
            msg = "scores row count must match row_labels"
            raise ValueError(msg)
        expected_cols = len(self.col_labels)
        for i, row in enumerate(self.scores):
            if len(row) != expected_cols:
                msg = f"scores[{i}] length must match col_labels"
                raise ValueError(msg)
        return self


class Report(BaseModel):
    """Aggregated narrative report for humans."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str
    kind: Literal["weekly", "model_comparison", "agent_stack", "browser_evidence"]
    period_start: str = Field(description="RFC 3339 date (or date-time)")
    period_end: str = Field(description="RFC 3339 date (or date-time)")
    body_markdown: str
    source_refs: list[str] = Field(default_factory=list)
