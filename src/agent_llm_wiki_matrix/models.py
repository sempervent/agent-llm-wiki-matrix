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
    scoring_backend: Literal["deterministic", "semantic_judge", "hybrid"] = Field(
        default="deterministic",
        description="deterministic=byte-hash; semantic_judge=LLM; hybrid=blend of both",
    )
    judge_provenance_relpath: str | None = Field(
        default=None,
        description=(
            "Repo-relative path to evaluation_judge_provenance.json when semantic or hybrid."
        ),
    )


class JudgeProviderInfo(BaseModel):
    """Provider used for a semantic judge call."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["mock", "ollama", "openai_compatible"]
    model: str


class JudgeHybridAggregation(BaseModel):
    """How hybrid scores combined deterministic and semantic criterion scores."""

    model_config = ConfigDict(extra="forbid")

    deterministic_weight: float = Field(ge=0.0, le=1.0)
    semantic_weight: float = Field(ge=0.0, le=1.0)
    deterministic_scores: dict[str, float]
    semantic_scores: dict[str, float]
    blend_method: Literal["weighted_per_criterion"] = "weighted_per_criterion"


class EvaluationJudgeProvenance(BaseModel):
    """Full audit trail for semantic or hybrid rubric scoring."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    evaluation_id: str = Field(min_length=1)
    evaluation_ref: str = Field(description="Path to evaluation.json relative to run root")
    subject_ref: str
    rubric_id: str
    scoring_backend: Literal["semantic_judge", "hybrid"]
    judge_system_prompt: str
    judge_user_prompt: str
    provider: JudgeProviderInfo
    raw_response_text: str
    parsed_criterion_scores: dict[str, float]
    parse_ok: bool
    parse_error: str | None = None
    hybrid_aggregation: JudgeHybridAggregation | None = None
    aggregation_notes: str | None = Field(
        default=None,
        description="Short summary of how total_weighted_score was derived",
    )


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
    prompt_source: Literal["inline", "registry"] = "inline"
    prompt_registry_id: str | None = None
    registry_document_version: str | None = None
    prompt_source_relpath: str | None = Field(
        default=None,
        description="Repo-relative path to prompt body file when prompt_source is registry",
    )
    browser_runner: str | None = Field(
        default=None,
        description="Browser abstraction runner id when a browser evidence phase ran",
    )
    browser_evidence_relpath: str | None = Field(
        default=None,
        description="Cell-relative path to browser_evidence.json when written",
    )


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
    prompt_source: Literal["inline", "registry"] = "inline"
    prompt_registry_id: str | None = None
    registry_document_version: str | None = None
    prompt_source_relpath: str | None = Field(
        default=None,
        description="Repo-relative path to prompt body file when prompt_source is registry",
    )
    browser_runner: str | None = Field(
        default=None,
        description="Browser runner id when execution_mode injected browser evidence",
    )
    browser_evidence_relpath: str | None = Field(
        default=None,
        description="Cell-relative path to browser_evidence.json when present",
    )


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


BenchmarkTaskFamily = Literal[
    "repo_governance",
    "runtime_config",
    "documentation",
    "browser_evidence",
    "matrix_reasoning",
    "multi_agent_coordination",
    "campaign",
    "scaffolding",
    "integration",
    "other",
]

BenchmarkDifficulty = Literal["trivial", "low", "medium", "high", "stress"]

BenchmarkDeterminism = Literal[
    "deterministic_fixture",
    "deterministic_scoring",
    "stochastic_live",
]

BenchmarkToolRequirement = Literal[
    "none",
    "cli",
    "registry",
    "browser_mock",
    "repo_context",
    "live_llm",
    "playwright",
    "compose",
    "multi_variant",
]


class BenchmarkTaxonomyV1(BaseModel):
    """Versioned grouping metadata for benchmark definitions and run manifests."""

    model_config = ConfigDict(extra="forbid")

    taxonomy_version: Literal[1] = 1
    task_family: BenchmarkTaskFamily
    difficulty: BenchmarkDifficulty
    determinism: BenchmarkDeterminism
    tool_requirements: list[BenchmarkToolRequirement] = Field(
        default_factory=list,
        description=("Tools or harness features this suite expects (not enforced by mock runs)."),
    )


class BenchmarkRetryPolicy(BaseModel):
    """Retry hints for benchmark cells (metadata only; harness does not loop yet)."""

    model_config = ConfigDict(extra="forbid")

    max_attempts: int = Field(default=1, ge=1, le=64)
    backoff_seconds: float = Field(default=0.0, ge=0.0)


class BenchmarkCellArtifactPaths(BaseModel):
    """Relative paths for one variant × prompt cell (sorted by cell_id in the manifest)."""

    model_config = ConfigDict(extra="forbid")

    cell_id: str = Field(description="Stable slug: safe(variant)__safe(prompt)")
    request_relpath: str
    raw_response_relpath: str
    normalized_response_relpath: str
    aggregate_response_relpath: str
    evaluation_relpath: str
    browser_evidence_relpath: str | None = Field(
        default=None,
        description="Present when execution_mode browser_mock wrote browser evidence JSON",
    )
    judge_provenance_relpath: str | None = Field(
        default=None,
        description="evaluation_judge_provenance.json when semantic_judge or hybrid scoring",
    )


class BenchmarkRunManifest(BaseModel):
    """Summary of a benchmark run output directory (``manifest.json``)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    run_id: str = Field(min_length=1)
    benchmark_id: str = Field(min_length=1)
    title: str
    rubric_ref: str
    created_at: str
    variant_ids: list[str]
    prompt_ids: list[str]
    definition_source_relpath: str | None = Field(
        default=None,
        description="Path to the benchmark definition file (often repo-relative) when recorded.",
    )
    prompt_registry_effective_ref: str | None = Field(
        default=None,
        description="Effective prompt registry YAML path used when any prompt used prompt_ref.",
    )
    cells: list[BenchmarkCellArtifactPaths] = Field(
        description="Per-cell artifact paths (lexicographically sorted by cell_id)",
    )
    matrix_grid_path: str
    matrix_pairwise_path: str
    matrix_grid_row_inputs_path: str
    matrix_pairwise_row_inputs_path: str
    report_json_path: str
    report_md_path: str
    matrix_grid_md_path: str
    matrix_pairwise_md_path: str
    taxonomy: BenchmarkTaxonomyV1 | None = Field(
        default=None,
        description="Optional taxonomy copied from the benchmark definition at run time.",
    )
    time_budget_seconds: float | None = Field(
        default=None,
        description="Optional wall-clock budget hint for agents (not enforced by the harness).",
    )
    token_budget: int | None = Field(
        default=None,
        description="Optional token budget hint for providers (not enforced by the harness).",
    )
    retry_policy: BenchmarkRetryPolicy | None = Field(
        default=None,
        description="Optional retry policy metadata (future: harness may consume).",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Free-form labels for dashboards and suite filters.",
    )
    expected_artifact_kinds: list[str] = Field(
        default_factory=list,
        description="Expected alwm artifact kinds produced when reviewing cells (metadata).",
    )

    @model_validator(mode="after")
    def manifest_expected_kinds_registered(self) -> Self:
        if not self.expected_artifact_kinds:
            return self
        from agent_llm_wiki_matrix.artifacts import list_artifact_kinds

        allowed = frozenset(list_artifact_kinds())
        for k in self.expected_artifact_kinds:
            if k not in allowed:
                msg = f"Unknown expected artifact kind: {k!r} (not in {sorted(allowed)})"
                raise ValueError(msg)
        return self
