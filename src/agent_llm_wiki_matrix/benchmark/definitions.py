"""Versioned benchmark definitions (YAML / JSON on disk)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from agent_llm_wiki_matrix.models import BenchmarkRetryPolicy, BenchmarkTaxonomyV1


class BackendSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["mock", "ollama", "openai_compatible"]
    model: str = "mock-model"


class EvalHybridWeights(BaseModel):
    """Blend deterministic byte-hash scores with semantic judge scores (per criterion)."""

    model_config = ConfigDict(extra="forbid")

    deterministic_weight: float = Field(0.5, ge=0.0, le=1.0)
    semantic_weight: float = Field(0.5, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _sum_to_one(self) -> Self:
        s = self.deterministic_weight + self.semantic_weight
        if abs(s - 1.0) > 1e-5:
            msg = "eval_scoring.hybrid weights must sum to 1.0"
            raise ValueError(msg)
        return self


class EvalScoringSpec(BaseModel):
    """Optional scoring mode for benchmark cells (default: deterministic only)."""

    model_config = ConfigDict(extra="forbid")

    backend: Literal["deterministic", "semantic_judge", "hybrid"] = "deterministic"
    hybrid: EvalHybridWeights | None = None
    judge_provider_ref: str | None = Field(
        default=None,
        description=(
            "Optional providers YAML path relative to repo root for the judge. "
            "Defaults to the same --provider-config as the benchmark run when unset."
        ),
    )


class BrowserBenchConfig(BaseModel):
    """How to obtain browser evidence for ``execution_mode: browser_mock`` cells."""

    model_config = ConfigDict(extra="forbid")

    runner: Literal["mock", "file", "playwright", "mcp"] = "mock"
    scenario_id: str | None = Field(
        default=None,
        description="For file/mcp runners: id under fixtures/browser_evidence/v1/<id>.json",
    )
    fixture_relpath: str | None = Field(
        default=None,
        description="Repo-relative path to a browser_evidence JSON file.",
    )
    start_url: str | None = Field(
        default=None,
        description="Required for playwright when not using a file-only shim.",
    )
    steps: list[str] = Field(
        default_factory=list,
        description="Extra navigation steps (runner-specific; see browser_execution).",
    )

    @model_validator(mode="after")
    def _browser_runner_fields(self) -> Self:
        if self.runner == "playwright" and not self.start_url:
            msg = "browser.playwright requires start_url for benchmark runs"
            raise ValueError(msg)
        if self.runner in ("file", "mcp") and not self.scenario_id and not self.fixture_relpath:
            msg = f"browser.{self.runner} requires scenario_id and/or fixture_relpath"
            raise ValueError(msg)
        return self


class VariantSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    agent_stack: str = Field(min_length=1)
    execution_mode: Literal["cli", "browser_mock", "repo_governed"]
    backend: BackendSpec
    browser: BrowserBenchConfig | None = Field(
        default=None,
        description=(
            "When set, use only with execution_mode browser_mock (browser evidence phase)."
        ),
    )

    @model_validator(mode="after")
    def _browser_only_with_mode(self) -> Self:
        if self.browser is not None and self.execution_mode != "browser_mock":
            msg = "variant.browser may only be set when execution_mode is browser_mock"
            raise ValueError(msg)
        return self


class PromptItem(BaseModel):
    """One prompt slot: either inline ``text`` or a ``prompt_ref`` into the registry."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    text: str | None = Field(
        default=None,
        description="Inline prompt body (mutually exclusive with prompt_ref).",
    )
    prompt_ref: str | None = Field(
        default=None,
        description="Registry prompt id (see prompts/registry.yaml or prompt_registry_ref).",
    )
    registry_version: str | None = Field(
        default=None,
        description=(
            "Optional pin: must equal the registry file's top-level version when set "
            "(only valid with prompt_ref)."
        ),
    )

    @model_validator(mode="after")
    def _inline_xor_registry(self) -> Self:
        has_text = self.text is not None
        has_ref = self.prompt_ref is not None
        if has_text == has_ref:
            msg = f"Prompt {self.id!r}: set exactly one of text or prompt_ref"
            raise ValueError(msg)
        if self.registry_version is not None and not has_ref:
            msg = f"Prompt {self.id!r}: registry_version requires prompt_ref"
            raise ValueError(msg)
        if has_text and self.text is not None and not self.text.strip():
            msg = f"Prompt {self.id!r}: inline text must be non-empty"
            raise ValueError(msg)
        if has_ref and (not self.prompt_ref or not str(self.prompt_ref).strip()):
            msg = f"Prompt {self.id!r}: prompt_ref must be a non-empty string"
            raise ValueError(msg)
        return self


class BenchmarkDefinitionV1(BaseModel):
    """Benchmark bundle: prompts × variants (agent stack, backend, execution mode)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    rubric_ref: str = Field(
        min_length=1,
        description="Path relative to repository root",
    )
    prompt_registry_ref: str | None = Field(
        default=None,
        description=(
            "Optional path to prompt registry YAML relative to repo root. "
            "Defaults to prompts/registry.yaml when any prompt uses prompt_ref."
        ),
    )
    prompts: list[PromptItem] = Field(min_length=1)
    variants: list[VariantSpec] = Field(min_length=1)
    taxonomy: BenchmarkTaxonomyV1 | None = Field(
        default=None,
        description="Optional task family, difficulty, determinism, and tool-requirement tags.",
    )
    time_budget_seconds: float | None = Field(
        default=None,
        gt=0,
        description="Optional wall-clock budget hint for agent runners (harness does not enforce).",
    )
    token_budget: int | None = Field(
        default=None,
        ge=1,
        description="Optional provider token budget hint (harness does not enforce).",
    )
    retry_policy: BenchmarkRetryPolicy | None = Field(
        default=None,
        description="Optional retry policy metadata for agent implementations.",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Free-form labels (e.g. campaign id, owner team).",
    )
    expected_artifact_kinds: list[str] = Field(
        default_factory=list,
        description="Artifact kinds reviewers expect under each cell (metadata).",
    )
    eval_scoring: EvalScoringSpec | None = Field(
        default=None,
        description="Scoring backend: deterministic (default), semantic_judge, or hybrid.",
    )

    @model_validator(mode="after")
    def _eval_scoring_hybrid_weights(self) -> Self:
        if self.eval_scoring is None:
            return self
        if self.eval_scoring.backend == "hybrid" and self.eval_scoring.hybrid is None:
            msg = "eval_scoring.backend hybrid requires eval_scoring.hybrid weights"
            raise ValueError(msg)
        if self.eval_scoring.backend != "hybrid" and self.eval_scoring.hybrid is not None:
            msg = "eval_scoring.hybrid is only valid when backend is hybrid"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def _expected_artifact_kinds_registered(self) -> Self:
        if not self.expected_artifact_kinds:
            return self
        from agent_llm_wiki_matrix.artifacts import list_artifact_kinds

        allowed = frozenset(list_artifact_kinds())
        for k in self.expected_artifact_kinds:
            if k not in allowed:
                msg = f"Unknown expected artifact kind: {k!r} (not in {sorted(allowed)})"
                raise ValueError(msg)
        return self


def load_benchmark_definition(path: Path) -> BenchmarkDefinitionV1:
    """Load a versioned benchmark definition from YAML or JSON."""
    raw_text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        data = yaml.safe_load(raw_text)
    else:
        import json

        data = json.loads(raw_text)
    if not isinstance(data, dict):
        msg = "Benchmark definition root must be an object"
        raise TypeError(msg)
    return BenchmarkDefinitionV1.model_validate(data)
