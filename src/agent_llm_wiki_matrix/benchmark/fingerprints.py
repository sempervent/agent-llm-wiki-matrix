"""Stable SHA-256 fingerprints for comparing benchmark configurations across runs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from agent_llm_wiki_matrix.benchmark.definitions import (
    BenchmarkDefinitionV1,
    EvalHybridWeights,
    load_benchmark_definition,
)
from agent_llm_wiki_matrix.benchmark.prompt_resolution import (
    ResolvedBenchmarkPrompt,
    resolve_registry_yaml_path,
)
from agent_llm_wiki_matrix.models import (
    BenchmarkComparisonFingerprints,
    CampaignExperimentFingerprints,
)
from agent_llm_wiki_matrix.pipelines.evaluation_backends import JudgeRepeatParams
from agent_llm_wiki_matrix.providers.config import ProviderConfig


def sha256_canonical(obj: Any) -> str:
    """Return ``sha256:`` + hex digest of canonical JSON (sorted keys, compact separators)."""
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _suite_definition_payload(definition: BenchmarkDefinitionV1) -> dict[str, Any]:
    """Canonical suite identity: excludes human-facing title (cosmetic for dashboards)."""
    d = definition.model_dump(mode="json")
    d.pop("title", None)
    tags = d.get("tags")
    if isinstance(tags, list):
        d["tags"] = sorted(tags)
    kinds = d.get("expected_artifact_kinds")
    if isinstance(kinds, list):
        d["expected_artifact_kinds"] = sorted(kinds)
    return d


def fingerprint_suite_definition(definition: BenchmarkDefinitionV1) -> str:
    return sha256_canonical(_suite_definition_payload(definition))


def fingerprint_prompt_set(resolved: list[ResolvedBenchmarkPrompt]) -> str:
    rows: list[dict[str, Any]] = []
    for p in resolved:
        text_hash = hashlib.sha256(p.rendered_text.encode("utf-8")).hexdigest()
        rows.append(
            {
                "prompt_id": p.prompt_id,
                "prompt_source": p.prompt_source,
                "rendered_text_sha256": text_hash,
                "prompt_registry_id": p.prompt_registry_id,
                "registry_document_version": p.registry_document_version,
            },
        )
    return sha256_canonical({"prompts": rows})


def fingerprint_provider_configs(variant_provider_configs: dict[str, ProviderConfig]) -> str:
    ordered = sorted(variant_provider_configs.items(), key=lambda kv: kv[0])
    blocks = [
        {"variant_id": vid, "provider": cfg.model_dump(mode="json")}
        for vid, cfg in ordered
    ]
    return sha256_canonical({"variants": blocks})


def fingerprint_browser_configs(definition: BenchmarkDefinitionV1) -> str:
    ordered = sorted(definition.variants, key=lambda v: v.id)
    blocks: list[dict[str, Any]] = []
    for v in ordered:
        blocks.append(
            {
                "variant_id": v.id,
                "browser": v.browser.model_dump(mode="json") if v.browser is not None else None,
            },
        )
    return sha256_canonical({"variants": blocks})


def fingerprint_scoring_config(
    *,
    scoring_backend: str,
    definition: BenchmarkDefinitionV1,
    judge_repeat_params: JudgeRepeatParams,
    judge_provider_cfg: ProviderConfig | None,
    hybrid_weights: EvalHybridWeights | None,
) -> str:
    jr = asdict(judge_repeat_params)
    payload: dict[str, Any] = {
        "effective_backend": scoring_backend,
        "definition_eval_scoring": (
            definition.eval_scoring.model_dump(mode="json") if definition.eval_scoring else None
        ),
        "judge_repeat": jr,
        "hybrid_weights": hybrid_weights.model_dump(mode="json") if hybrid_weights else None,
        "judge_provider": (
            judge_provider_cfg.model_dump(mode="json") if judge_provider_cfg else None
        ),
    }
    return sha256_canonical(payload)


def fingerprint_prompt_registry_effective_state(
    *,
    repo_root: Path,
    definition: BenchmarkDefinitionV1,
    resolved_prompts: list[ResolvedBenchmarkPrompt],
    prompt_registry_path: Path | None,
) -> str:
    """Hash of effective registry file bytes + resolution metadata, or inline-only sentinel."""
    uses_registry = any(p.prompt_source == "registry" for p in resolved_prompts)
    if not uses_registry:
        return sha256_canonical(
            {
                "kind": "inline_prompts_only",
                "definition_prompt_registry_ref": definition.prompt_registry_ref,
            },
        )
    reg_abs = resolve_registry_yaml_path(
        repo_root=repo_root,
        definition=definition,
        prompt_registry_path=prompt_registry_path,
    )
    raw = reg_abs.read_bytes()
    file_digest = hashlib.sha256(raw).hexdigest()
    try:
        rel = str(reg_abs.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        rel = str(reg_abs)
    rows = [
        {
            "prompt_id": p.prompt_id,
            "prompt_registry_id": p.prompt_registry_id,
            "registry_document_version": p.registry_document_version,
        }
        for p in resolved_prompts
        if p.prompt_source == "registry"
    ]
    rows_sorted = sorted(
        rows,
        key=lambda r: (r["prompt_id"], r.get("prompt_registry_id") or ""),
    )
    return sha256_canonical(
        {
            "kind": "registry_resolved",
            "registry_relpath": rel,
            "registry_yaml_sha256": file_digest,
            "resolved_prompts": rows_sorted,
        },
    )


def _campaign_definition_identity_payload(campaign: object) -> dict[str, Any]:
    """Canonical campaign identity: drops cosmetic / human-only fields."""
    from agent_llm_wiki_matrix.benchmark.campaign_definitions import BenchmarkCampaignDefinitionV1

    if not isinstance(campaign, BenchmarkCampaignDefinitionV1):
        msg = "expected BenchmarkCampaignDefinitionV1"
        raise TypeError(msg)
    d = campaign.model_dump(mode="json")
    for k in ("title", "description", "notes", "owner", "created_at"):
        d.pop(k, None)
    d["suite_refs"] = sorted(d.get("suite_refs", []))
    d["campaign_tags"] = sorted(d.get("campaign_tags", []))
    kinds = d.get("expected_artifact_kinds")
    if isinstance(kinds, list):
        d["expected_artifact_kinds"] = sorted(kinds)
    return d


def fingerprint_campaign_definition(campaign: object) -> str:
    """Stable identity hash for a campaign definition (canonical payload, title excluded)."""
    return sha256_canonical(_campaign_definition_identity_payload(campaign))


def _fingerprint_campaign_provider_axis(repo_root: Path, refs: list[str | None]) -> str:
    blocks: list[dict[str, Any]] = []
    root = repo_root.resolve()
    for r in refs:
        if r is None:
            blocks.append({"ref": None, "sha256": None})
        else:
            p = (root / r).resolve()
            raw = p.read_bytes()
            blocks.append({"ref": r, "sha256": hashlib.sha256(raw).hexdigest()})
    return sha256_canonical({"provider_config_refs": blocks})


def _fingerprint_campaign_prompt_registry_override(repo_root: Path, ref: str | None) -> str:
    if ref is None:
        return sha256_canonical({"kind": "no_campaign_registry_override", "ref": None})
    p = (repo_root / ref).resolve()
    raw = p.read_bytes()
    try:
        rel = str(p.relative_to(repo_root.resolve()))
    except ValueError:
        rel = ref
    return sha256_canonical(
        {
            "kind": "campaign_prompt_registry_override",
            "ref": rel,
            "sha256": hashlib.sha256(raw).hexdigest(),
        },
    )


def build_campaign_experiment_fingerprints(
    repo_root: Path,
    campaign: object,
) -> CampaignExperimentFingerprints:
    """Stable per-axis fingerprints for longitudinal grouping and campaign reporting."""
    from agent_llm_wiki_matrix.benchmark.campaign_definitions import BenchmarkCampaignDefinitionV1

    if not isinstance(campaign, BenchmarkCampaignDefinitionV1):
        msg = "build_campaign_experiment_fingerprints expects BenchmarkCampaignDefinitionV1"
        raise TypeError(msg)

    root = repo_root.resolve()
    suite_blocks: list[dict[str, Any]] = []
    for suite_ref in sorted(campaign.suite_refs):
        suite_path = root / suite_ref
        loaded = load_benchmark_definition(suite_path)
        suite_blocks.append(
            {
                "suite_ref": suite_ref,
                "suite_definition": fingerprint_suite_definition(loaded),
            },
        )
    suite_stack = sha256_canonical({"suites": suite_blocks})

    scoring_axis = sha256_canonical(
        {
            "eval_scoring_options": [
                o.model_dump(mode="json") if o is not None else None
                for o in campaign.eval_scoring_options
            ],
        },
    )
    browser_axis = sha256_canonical(
        {
            "browser_configs": [
                b.model_dump(mode="json") if b is not None else None
                for b in campaign.browser_configs
            ],
        },
    )

    prov_refs = list(campaign.provider_config_refs)
    return CampaignExperimentFingerprints(
        campaign_definition=fingerprint_campaign_definition(campaign),
        suite_definitions=suite_stack,
        provider_configs=_fingerprint_campaign_provider_axis(root, prov_refs),
        scoring_configs=scoring_axis,
        browser_configs=browser_axis,
        prompt_registry_state=_fingerprint_campaign_prompt_registry_override(
            root,
            campaign.prompt_registry_ref,
        ),
    )


def build_benchmark_comparison_fingerprints(
    *,
    repo_root: Path,
    definition: BenchmarkDefinitionV1,
    resolved_prompts: list[ResolvedBenchmarkPrompt],
    variant_provider_configs: dict[str, ProviderConfig],
    scoring_backend: str,
    hybrid_weights: EvalHybridWeights | None,
    judge_repeat_params: JudgeRepeatParams,
    judge_provider_cfg: ProviderConfig | None,
    prompt_registry_path: Path | None = None,
) -> BenchmarkComparisonFingerprints:
    """Compute comparison fingerprints for a benchmark run (pre-cells)."""
    return BenchmarkComparisonFingerprints(
        suite_definition=fingerprint_suite_definition(definition),
        prompt_set=fingerprint_prompt_set(resolved_prompts),
        provider_config=fingerprint_provider_configs(variant_provider_configs),
        scoring_config=fingerprint_scoring_config(
            scoring_backend=scoring_backend,
            definition=definition,
            judge_repeat_params=judge_repeat_params,
            judge_provider_cfg=judge_provider_cfg,
            hybrid_weights=hybrid_weights,
        ),
        browser_config=fingerprint_browser_configs(definition),
        prompt_registry_state=fingerprint_prompt_registry_effective_state(
            repo_root=repo_root,
            definition=definition,
            resolved_prompts=resolved_prompts,
            prompt_registry_path=prompt_registry_path,
        ),
    )
