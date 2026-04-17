"""Resolve benchmark definition prompts from inline text and/or the prompt registry."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from agent_llm_wiki_matrix.benchmark.definitions import BenchmarkDefinitionV1, PromptItem
from agent_llm_wiki_matrix.benchmark.errors import BenchmarkPromptResolutionError
from agent_llm_wiki_matrix.prompt_registry import (
    PromptRegistryDocument,
    find_prompt_entry,
    load_prompt_registry_yaml,
    resolve_prompt_text,
)


@dataclass(frozen=True)
class ResolvedBenchmarkPrompt:
    """One prompt slot after resolving inline ``text`` or ``prompt_ref``."""

    prompt_id: str
    rendered_text: str
    prompt_source: Literal["inline", "registry"]
    prompt_registry_id: str | None
    registry_document_version: str | None
    prompt_source_relpath: str | None


DEFAULT_REGISTRY_RELPATH = "prompts/registry.yaml"


def resolve_registry_yaml_path(
    *,
    repo_root: Path,
    definition: BenchmarkDefinitionV1,
    prompt_registry_path: Path | None,
) -> Path:
    """Absolute path to the prompt registry YAML used for ``prompt_ref`` resolution."""
    if prompt_registry_path is not None:
        return prompt_registry_path.resolve()
    ref = definition.prompt_registry_ref or DEFAULT_REGISTRY_RELPATH
    return (repo_root / ref).resolve()


def resolve_benchmark_prompts(
    repo_root: Path,
    definition: BenchmarkDefinitionV1,
    *,
    prompt_registry_path: Path | None = None,
) -> list[ResolvedBenchmarkPrompt]:
    """Resolve every prompt in ``definition`` in order.

    Loads the registry YAML at most once when any ``prompt_ref`` is present.
    """
    repo_root = repo_root.resolve()
    needs_registry = any(p.prompt_ref is not None for p in definition.prompts)
    registry_doc: PromptRegistryDocument | None = None
    registry_path: Path | None = None

    if needs_registry:
        registry_path = resolve_registry_yaml_path(
            repo_root=repo_root,
            definition=definition,
            prompt_registry_path=prompt_registry_path,
        )
        if not registry_path.is_file():
            msg = f"Prompt registry not found: {registry_path}"
            raise BenchmarkPromptResolutionError(msg)
        registry_doc = load_prompt_registry_yaml(registry_path)

    out: list[ResolvedBenchmarkPrompt] = []
    for item in definition.prompts:
        out.append(
            _resolve_one(
                repo_root=repo_root,
                item=item,
                registry_doc=registry_doc,
                registry_path=registry_path,
            )
        )
    return out


def _resolve_one(
    *,
    repo_root: Path,
    item: PromptItem,
    registry_doc: PromptRegistryDocument | None,
    registry_path: Path | None,
) -> ResolvedBenchmarkPrompt:
    if item.text is not None:
        if item.registry_version is not None:
            msg = "registry_version is only valid when prompt_ref is set"
            raise BenchmarkPromptResolutionError(msg)
        return ResolvedBenchmarkPrompt(
            prompt_id=item.id,
            rendered_text=item.text,
            prompt_source="inline",
            prompt_registry_id=None,
            registry_document_version=None,
            prompt_source_relpath=None,
        )

    assert item.prompt_ref is not None
    if registry_doc is None or registry_path is None:
        msg = f"prompt_ref set for {item.id!r} but registry was not loaded"
        raise BenchmarkPromptResolutionError(msg)

    if item.registry_version is not None and item.registry_version != registry_doc.version:
        msg = (
            f"Registry version mismatch for prompt {item.id!r}: "
            f"definition pins {item.registry_version!r} but "
            f"{registry_path.as_posix()} has version {registry_doc.version!r}"
        )
        raise BenchmarkPromptResolutionError(msg)

    try:
        entry = find_prompt_entry(registry_doc, item.prompt_ref)
    except KeyError as e:
        msg = (
            f"Unknown prompt_ref {item.prompt_ref!r} for benchmark prompt id {item.id!r} "
            f"(registry {registry_path.as_posix()})"
        )
        raise BenchmarkPromptResolutionError(msg) from e

    try:
        text = resolve_prompt_text(repo_root=repo_root, entry=entry)
    except (OSError, ValueError) as e:
        msg = f"Failed to load prompt file for {item.prompt_ref!r}: {e}"
        raise BenchmarkPromptResolutionError(msg) from e

    return ResolvedBenchmarkPrompt(
        prompt_id=item.id,
        rendered_text=text,
        prompt_source="registry",
        prompt_registry_id=item.prompt_ref,
        registry_document_version=registry_doc.version,
        prompt_source_relpath=entry.path.replace("\\", "/"),
    )
