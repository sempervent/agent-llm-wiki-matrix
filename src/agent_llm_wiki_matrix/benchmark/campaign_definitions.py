"""Benchmark campaign definitions (YAML / JSON): sweep axes over one or more suites."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from agent_llm_wiki_matrix.benchmark.definitions import BrowserBenchConfig, EvalScoringSpec
from agent_llm_wiki_matrix.models import BenchmarkRetryPolicy
from agent_llm_wiki_matrix.schema import load_schema, validate_json


class BenchmarkCampaignDefinitionV1(BaseModel):
    """Sweep: suites × providers × eval scoring × optional browser overrides."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    suite_refs: list[str] = Field(
        min_length=1,
        description="Repo-relative benchmark definition paths.",
    )
    provider_config_refs: list[str | None] = Field(
        default_factory=list,
        description="Providers YAML per run; empty means one run with harness default.",
    )
    eval_scoring_options: list[EvalScoringSpec | None] = Field(
        default_factory=list,
        description="null keeps each suite's eval_scoring; empty means one null entry.",
    )
    execution_modes: list[Literal["cli", "browser_mock", "repo_governed"]] | None = Field(
        default=None,
        description="If set, variants not matching these execution modes are dropped.",
    )
    browser_configs: list[BrowserBenchConfig | None] = Field(
        default_factory=list,
        description="Merged into browser_mock variants; null keeps suite defaults.",
    )
    campaign_tags: list[str] = Field(
        default_factory=list,
        description="Appended to each member benchmark definition's tags.",
    )
    prompt_registry_ref: str | None = Field(
        default=None,
        description="Optional prompt registry override for all member runs.",
    )
    campaign_version: str | None = Field(
        default=None,
        description="Optional version label for this campaign definition (copied to manifests).",
    )
    description: str | None = Field(default=None)
    owner: str | None = Field(default=None)
    created_at: str | None = Field(
        default=None,
        description="RFC 3339 date-time from the definition file when authored (metadata only).",
    )
    notes: str | None = Field(default=None)
    expected_artifact_kinds: list[str] = Field(
        default_factory=list,
        description=(
            "Expected outputs for longitudinal dashboards (metadata; not enforced by harness)."
        ),
    )
    retry_policy: BenchmarkRetryPolicy | None = Field(default=None)
    time_budget_seconds: float | None = Field(default=None, gt=0.0)
    token_budget: int | None = Field(default=None, ge=1)

    @model_validator(mode="before")
    @classmethod
    def _coerce_yaml_aliases(cls, data: Any) -> Any:
        """Map synonym keys from YAML/JSON (matches schema aliases)."""
        if not isinstance(data, dict):
            return data
        out = dict(data)
        if "benchmark_suites" in out and "suite_refs" not in out:
            out["suite_refs"] = out.pop("benchmark_suites")
        if "provider_configs" in out and "provider_config_refs" not in out:
            out["provider_config_refs"] = out.pop("provider_configs")
        if "scoring_configs" in out and "eval_scoring_options" not in out:
            out["eval_scoring_options"] = out.pop("scoring_configs")
        if "tags" in out and "campaign_tags" not in out:
            out["campaign_tags"] = out.pop("tags")
        return out

    @model_validator(mode="after")
    def _default_empty_axes(self) -> Self:
        prov = self.provider_config_refs if self.provider_config_refs else [None]
        evs = self.eval_scoring_options if self.eval_scoring_options else [None]
        br = self.browser_configs if self.browser_configs else [None]
        return self.model_copy(
            update={
                "provider_config_refs": prov,
                "eval_scoring_options": evs,
                "browser_configs": br,
            },
        )

    @model_validator(mode="after")
    def _expected_kinds_registered(self) -> Self:
        if not self.expected_artifact_kinds:
            return self
        from agent_llm_wiki_matrix.artifacts import list_artifact_kinds

        allowed = frozenset(list_artifact_kinds())
        for k in self.expected_artifact_kinds:
            if k not in allowed:
                msg = f"Unknown expected artifact kind: {k!r} (not in {sorted(allowed)})"
                raise ValueError(msg)
        return self


def load_benchmark_campaign_definition(path: Path) -> BenchmarkCampaignDefinitionV1:
    """Load and validate a campaign definition from YAML or JSON."""
    raw_text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        data = yaml.safe_load(raw_text)
    else:
        import json

        data = json.loads(raw_text)
    if not isinstance(data, dict):
        msg = "Campaign definition root must be an object"
        raise TypeError(msg)
    validate_json(data, load_schema("schemas/v1/benchmark_campaign.schema.json"))
    return BenchmarkCampaignDefinitionV1.model_validate(data)
