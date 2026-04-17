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


class RubricCriterion(BaseModel):
    """Single weighted criterion in a rubric."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    weight: float = Field(ge=0.0)
    description: str = ""


class Rubric(BaseModel):
    """Weighted rubric for deterministic or LLM-assisted evaluation."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    version: str = "1"
    criteria: list[RubricCriterion] = Field(min_length=1)


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


class BenchmarkResponse(BaseModel):
    """Aggregate cell record; ``response_text`` is normalized (post execution-mode tag)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    id: str = Field(min_length=1)
    benchmark_id: str = Field(min_length=1)
    variant_id: str = Field(min_length=1)
    prompt_id: str = Field(min_length=1)
    agent_stack: str = Field(min_length=1)
    execution_mode: Literal["cli", "browser_mock", "repo_governed"]
    backend_kind: Literal["mock", "ollama", "openai_compatible"]
    backend_model: str
    prompt_text: str
    response_text: str
    duration_ms: int | None = Field(default=None, ge=0)
    created_at: str = Field(description="RFC 3339 date-time")


class BenchmarkRequestRecord(BaseModel):
    """Persisted provider request (prompt + model) for one benchmark cell."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    cell_id: str = Field(min_length=1)
    benchmark_id: str = Field(min_length=1)
    variant_id: str = Field(min_length=1)
    prompt_id: str = Field(min_length=1)
    prompt_text: str
    model: str
    temperature: float | None = None
    created_at: str = Field(description="RFC 3339 date-time")


class MatrixGridInputEntry(BaseModel):
    """One cell of the grid matrix with pointers to evaluation artifacts."""

    model_config = ConfigDict(extra="forbid")

    row_label: str
    col_label: str
    variant_id: str
    prompt_id: str
    evaluation_relpath: str
    total_weighted_score: float


class MatrixGridInputs(BaseModel):
    """Row/column inputs and evaluation refs used to build the grid matrix."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    run_id: str = Field(min_length=1)
    benchmark_id: str = ""
    matrix_id: str = Field(min_length=1)
    metric: str = Field(min_length=1)
    created_at: str
    entries: list[MatrixGridInputEntry] = Field(min_length=1)


class MatrixPairwiseInputEntry(BaseModel):
    """One cell of the pairwise matrix with contributing prompt ids."""

    model_config = ConfigDict(extra="forbid")

    row_label: str
    col_label: str
    variant_i: str
    variant_j: str
    mean_abs_score_delta: float
    prompt_ids: list[str]


class MatrixPairwiseInputs(BaseModel):
    """Inputs used to build the pairwise delta matrix."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    run_id: str = Field(min_length=1)
    benchmark_id: str = ""
    matrix_id: str = Field(min_length=1)
    metric: str = Field(min_length=1)
    created_at: str
    entries: list[MatrixPairwiseInputEntry] = Field(min_length=1)


class BenchmarkExecutionMetadata(BaseModel):
    """Hints for how to run a benchmark case (stack, backend policy, execution mode)."""

    model_config = ConfigDict(extra="forbid")

    mode: Literal["cli", "browser_mock", "repo_governed"]
    agent_stack_label: str = Field(min_length=1)
    backend_policy: Literal["mock", "ollama", "openai_compatible", "any"]
    notes: str | None = None


class BenchmarkCase(BaseModel):
    """Versioned benchmark task template (prompt + rubric + expected outputs)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    task_kind: Literal[
        "repo_scaffolding",
        "markdown_synthesis",
        "comparison_matrix",
        "browser_evidence",
    ]
    prompt: str = Field(min_length=1)
    expected_artifact_kinds: list[str] = Field(
        min_length=1,
        description="Expected structured outputs for scoring (alwm artifact kind names)",
    )
    rubric_ref: str = Field(min_length=1, description="Path to rubric JSON relative to repo root")
    execution: BenchmarkExecutionMetadata
    deterministic_fixture_mode: bool

    @model_validator(mode="after")
    def expected_kinds_are_registered(self) -> Self:
        from agent_llm_wiki_matrix.artifacts import list_artifact_kinds

        allowed = frozenset(list_artifact_kinds())
        for k in self.expected_artifact_kinds:
            if k not in allowed:
                msg = f"Unknown expected artifact kind: {k} (not in {sorted(allowed)})"
                raise ValueError(msg)
        return self
