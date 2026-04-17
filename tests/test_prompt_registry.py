"""Prompt registry YAML: schema validation and CLI."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from agent_llm_wiki_matrix.cli import main
from agent_llm_wiki_matrix.prompt_registry import (
    find_prompt_entry,
    load_prompt_registry_yaml,
    resolve_prompt_text,
)

_REPO = Path(__file__).resolve().parents[1]


def test_load_default_registry() -> None:
    path = _REPO / "prompts" / "registry.yaml"
    doc = load_prompt_registry_yaml(path)
    assert doc.version
    assert len(doc.prompts) >= 1
    entry = find_prompt_entry(doc, "scaffold.echo.v1")
    assert "scaffold" in entry.tags


def test_resolve_prompt_text() -> None:
    path = _REPO / "prompts" / "registry.yaml"
    doc = load_prompt_registry_yaml(path)
    entry = find_prompt_entry(doc, "scaffold.echo.v1")
    body = resolve_prompt_text(repo_root=_REPO, entry=entry)
    assert "OK" in body


def test_resolve_rejects_path_traversal(tmp_path: Path) -> None:
    from agent_llm_wiki_matrix.prompt_registry import PromptRegistryEntry

    evil = PromptRegistryEntry(
        id="x",
        description="",
        path="../../etc/passwd",
    )
    with pytest.raises(ValueError, match="escapes"):
        resolve_prompt_text(repo_root=tmp_path, entry=evil)


def test_prompts_check_cli() -> None:
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["prompts", "check", "--registry", "prompts/registry.yaml"],
        env={"ALWM_REPO_ROOT": str(_REPO)},
    )
    assert result.exit_code == 0
    assert "ok:" in result.output


def test_prompts_show_cli() -> None:
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["prompts", "show", "scaffold.echo.v1"],
        env={"ALWM_REPO_ROOT": str(_REPO)},
    )
    assert result.exit_code == 0
    assert "OK" in result.output
