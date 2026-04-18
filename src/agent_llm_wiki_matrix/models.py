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
    judge_repeat_count: int | None = Field(
        default=None,
        description="Semantic judge invocations when >1; omitted for deterministic",
    )
    judge_semantic_aggregation: Literal["mean", "median", "trimmed_mean"] | None = Field(
        default=None,
        description="How repeated semantic scores were combined",
    )
    judge_low_confidence: bool | None = Field(
        default=None,
        description="True when disagreement thresholds flagged instability",
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
    semantic_repeat_count: int = Field(
        default=1,
        ge=1,
        description="Semantic judge runs aggregated before blending",
    )


class JudgeRepeatRunRecord(BaseModel):
    """One semantic judge invocation."""

    model_config = ConfigDict(extra="forbid")

    run_index: int = Field(ge=0)
    raw_response_text: str
    parsed_criterion_scores: dict[str, float]
    parse_ok: bool
    parse_error: str | None = None


class JudgeCriterionDisagreement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min: float
    max: float
    score_range: float
    stdev: float


class JudgeDisagreementSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    per_criterion: dict[str, JudgeCriterionDisagreement]
    mean_stdev_across_criteria: float
    total_weighted_per_run: list[float]
    total_weighted_stdev: float
    max_range_across_criteria: float


class JudgeRepeatConfidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    low_confidence: bool
    flags: list[str] = Field(default_factory=list)
    thresholds: dict[str, float | None] = Field(default_factory=dict)


class JudgeRepeatAggregation(BaseModel):
    """Repeated semantic runs: per-run records, aggregation, disagreement, confidence."""

    model_config = ConfigDict(extra="forbid")

    repeat_count: int = Field(ge=1)
    strategy: Literal["mean", "median", "trimmed_mean"]
    trim_fraction: float = Field(0.1, ge=0.0, le=0.45)
    runs: list[JudgeRepeatRunRecord] = Field(min_length=1)
    aggregated_semantic_scores: dict[str, float]
    disagreement: JudgeDisagreementSummary
    confidence: JudgeRepeatConfidence


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
    repeat_aggregation: JudgeRepeatAggregation | None = Field(
        default=None,
        description="Present when multiple semantic judge runs were aggregated",
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
    kind: Literal[
        "weekly",
        "model_comparison",
        "agent_stack",
        "browser_evidence",
        "longitudinal",
        "benchmark_weekly",
        "failure_atlas",
    ]
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


class BenchmarkCampaignRunEntry(BaseModel):
    """One benchmark run produced inside a campaign output directory."""

    model_config = ConfigDict(extra="forbid")

    run_index: int = Field(ge=0, description="Stable ordering within the campaign (0-based).")
    run_id: str = Field(min_length=1)
    suite_ref: str = Field(description="Repo-relative path to the benchmark definition YAML/JSON.")
    benchmark_id: str = Field(min_length=1)
    provider_config_ref: str | None = Field(
        default=None,
        description="Repo-relative providers YAML, or null for harness default resolution.",
    )
    eval_scoring_label: str = Field(
        min_length=1,
        description="Label for the eval_scoring axis (e.g. suite_default, deterministic).",
    )
    execution_modes_filter: list[str] | None = Field(
        default=None,
        description="If set, variants were restricted to these execution_mode values.",
    )
    browser_config_applied: bool = Field(
        default=False,
        description="True when a campaign browser_configs entry was merged into browser_mock.",
    )
    status: Literal["succeeded", "failed"] = Field(
        default="succeeded",
        description="Whether this member run completed without harness error.",
    )
    error: str | None = Field(default=None, description="Populated when status is failed.")
    duration_seconds: float | None = Field(
        default=None,
        ge=0.0,
        description="Wall time for this member run (seconds).",
    )
    output_relpath: str = Field(
        min_length=1,
        description="Directory for this run, relative to campaign root (e.g. runs/run0000).",
    )
    manifest_relpath: str = Field(
        min_length=1,
        description="manifest.json for this run, relative to campaign root.",
    )
    comparison_fingerprints: BenchmarkComparisonFingerprints | None = Field(
        default=None,
        description="Copied from member manifest.json when present for cross-run comparison.",
    )
    mean_total_weighted_score: float | None = Field(
        default=None,
        description="Mean of cell total_weighted_score values when evaluations were readable.",
    )
    cell_count: int = Field(ge=0)


class CampaignRunStatusSummary(BaseModel):
    """Aggregate counts for campaign execution."""

    model_config = ConfigDict(extra="forbid")

    succeeded: int = Field(ge=0, default=0)
    failed: int = Field(ge=0, default=0)


class CampaignFailureRecord(BaseModel):
    """One failed member run."""

    model_config = ConfigDict(extra="forbid")

    run_index: int = Field(ge=0)
    run_id: str = Field(min_length=1)
    message: str = Field(min_length=1)


class CampaignGeneratedReportPaths(BaseModel):
    """Repo-relative paths to top-level campaign artifacts."""

    model_config = ConfigDict(extra="forbid")

    campaign_manifest: str = Field(default="manifest.json")
    campaign_summary_json: str = Field(default="campaign-summary.json")
    campaign_summary_md: str = Field(default="campaign-summary.md")


class CampaignExperimentFingerprints(BaseModel):
    """Per-axis stable hashes for a campaign definition (longitudinal grouping, reporting)."""

    model_config = ConfigDict(extra="forbid")

    campaign_definition: str = Field(
        min_length=8,
        description="sha256:… canonical campaign definition (cosmetic fields excluded).",
    )
    suite_definitions: str = Field(
        min_length=8,
        description="sha256:… composite of loaded suite definition fingerprints (sorted by path).",
    )
    provider_configs: str = Field(
        min_length=8,
        description="sha256:… provider YAML paths + file digests (campaign axis order).",
    )
    scoring_configs: str = Field(
        min_length=8,
        description="sha256:… eval_scoring_options axis (including null entries).",
    )
    browser_configs: str = Field(
        min_length=8,
        description="sha256:… browser_configs axis (including null entries).",
    )
    prompt_registry_state: str = Field(
        min_length=8,
        description="sha256:… campaign prompt_registry_ref path + bytes when set.",
    )


class BenchmarkCampaignManifest(BaseModel):
    """Index of a campaign: each run has a normal benchmark manifest.json."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    campaign_id: str = Field(min_length=1)
    title: str
    created_at: str = Field(description="RFC 3339 date-time used for member runs.")
    definition_source_relpath: str = Field(
        min_length=1,
        description="Repo-relative path to the campaign definition YAML/JSON.",
    )
    fixture_mode_force_mock: bool = Field(
        default=True,
        description="Whether member runs forced mock providers (offline fixture mode).",
    )
    campaign_definition_fingerprint: str | None = Field(
        default=None,
        description="sha256:… over canonical campaign definition payload.",
    )
    campaign_experiment_fingerprints: CampaignExperimentFingerprints | None = Field(
        default=None,
        description=(
            "Per-axis fingerprints (definition, suites, providers, scoring, browser, registry)."
        ),
    )
    campaign_version: str | None = Field(default=None)
    description: str | None = Field(default=None)
    owner: str | None = Field(default=None)
    definition_created_at: str | None = Field(
        default=None,
        description="created_at from the campaign definition when present.",
    )
    tags: list[str] = Field(default_factory=list)
    notes: str | None = Field(default=None)
    expected_artifact_kinds: list[str] = Field(default_factory=list)
    retry_policy: BenchmarkRetryPolicy | None = Field(default=None)
    time_budget_seconds: float | None = Field(default=None)
    token_budget: int | None = Field(default=None)
    dry_run: bool = Field(default=False, description="True when no member runs executed.")
    run_status_summary: CampaignRunStatusSummary | None = Field(default=None)
    run_count: int | None = Field(default=None, ge=0)
    started_at_utc: str | None = Field(default=None)
    finished_at_utc: str | None = Field(default=None)
    duration_seconds: float | None = Field(default=None, ge=0.0)
    failures: list[CampaignFailureRecord] = Field(default_factory=list)
    generated_report_paths: CampaignGeneratedReportPaths | None = Field(default=None)
    git_commit_sha: str | None = Field(default=None)
    git_describe: str | None = Field(default=None)
    inputs_snapshot: dict[str, object] | None = Field(default=None)
    runs: list[BenchmarkCampaignRunEntry] = Field(
        default_factory=list,
        description="Member runs in stable order (longitudinal glob: runs/*/manifest.json).",
    )


class CampaignSummaryV1(BaseModel):
    """Structured campaign-summary.json (artifact kind campaign_summary)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    campaign_id: str = Field(min_length=1)
    title: str
    created_at: str
    definition_source_relpath: str
    fixture_mode_force_mock: bool = True
    campaign_definition_fingerprint: str | None = None
    campaign_experiment_fingerprints: CampaignExperimentFingerprints | None = None
    campaign_version: str | None = None
    run_count: int = Field(ge=0)
    run_status_summary: CampaignRunStatusSummary | None = None
    dry_run: bool = False
    failures: list[CampaignFailureRecord] = Field(default_factory=list)
    git_commit_sha: str | None = None
    git_describe: str | None = None
    runs: list[dict[str, object]] = Field(default_factory=list)


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


class BenchmarkComparisonFingerprints(BaseModel):
    """Stable SHA-256 fingerprints for comparing benchmark configurations across runs."""

    model_config = ConfigDict(extra="forbid")

    suite_definition: str = Field(
        min_length=8,
        description=(
            "sha256:… hash of canonical suite definition (title excluded; sorted tag lists)."
        ),
    )
    prompt_set: str = Field(
        description=(
            "sha256:… hash of resolved prompt ids + inline/registry provenance + text digests"
        ),
    )
    provider_config: str = Field(
        description="sha256:… hash of per-variant resolved ProviderConfig (sorted by variant id)",
    )
    scoring_config: str = Field(
        description=(
            "sha256:… hash of effective scoring backend, eval_scoring, judge repeat, "
            "judge provider"
        ),
    )
    browser_config: str = Field(
        description="sha256:… hash of per-variant browser blocks (sorted by variant id)",
    )
    prompt_registry_state: str = Field(
        min_length=8,
        description=(
            "sha256:… hash of effective prompt registry YAML (path + bytes) when "
            "prompt_ref is used; otherwise inline-only sentinel"
        ),
    )


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
    success_criteria: list[str] = Field(
        default_factory=list,
        description="Human-readable pass conditions for external agent evaluations (metadata).",
    )
    failure_taxonomy_hints: list[str] = Field(
        default_factory=list,
        description="Suggested failure labels when comparing systems on this suite (metadata).",
    )
    comparison_fingerprints: BenchmarkComparisonFingerprints | None = Field(
        default=None,
        description=(
            "Stable hashes of suite, prompts, providers, scoring, browser, and prompt registry"
        ),
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
