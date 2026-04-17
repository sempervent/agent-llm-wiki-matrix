"""CLI entrypoint for agent-llm-wiki-matrix."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import click

from agent_llm_wiki_matrix import __version__
from agent_llm_wiki_matrix.artifacts import list_artifact_kinds, load_artifact_file
from agent_llm_wiki_matrix.logging_config import configure_logging, get_logger
from agent_llm_wiki_matrix.providers.config import load_provider_config


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="alwm")
@click.option(
    "--log-level",
    envvar="ALWM_LOG_LEVEL",
    default="INFO",
    show_default=True,
    help="Logging level (DEBUG, INFO, WARNING, ERROR).",
)
@click.pass_context
def main(ctx: click.Context, log_level: str) -> None:
    """LLM wiki + comparison matrix orchestration (markdown-first, git-native)."""
    ctx.ensure_object(dict)
    ctx.obj["log_level"] = log_level
    configure_logging(log_level)
    log = get_logger("cli")
    log.debug("cli_start", version=__version__)


@main.command("version")
def cmd_version() -> None:
    """Print version string."""
    click.echo(__version__)


@main.group("providers")
def providers_cmd() -> None:
    """Inspect provider configuration (Phase 3)."""


@providers_cmd.command("show")
@click.option(
    "--config-yaml",
    type=click.Path(path_type=Path, exists=True, dir_okay=False, readable=True),
    default=None,
    help=(
        "Optional YAML file. Defaults: $ALWM_PROVIDER_CONFIG, else "
        "<repo>/config/providers.yaml if present."
    ),
)
def cmd_providers_show(config_yaml: Path | None) -> None:
    """Print resolved provider configuration (API keys redacted)."""
    repo = Path(os.environ.get("ALWM_REPO_ROOT", ".")).resolve()
    path = config_yaml
    if path is None:
        env_path = os.environ.get("ALWM_PROVIDER_CONFIG")
        if env_path:
            path = Path(env_path)
        else:
            candidate = repo / "config" / "providers.yaml"
            path = candidate if candidate.is_file() else None
    cfg = load_provider_config(yaml_path=path, environ=os.environ)
    data = cfg.model_dump()
    key = data["openai_compatible"]["api_key"]
    data["openai_compatible"]["api_key"] = "***" if key else ""
    click.echo(json.dumps(data, indent=2, sort_keys=True))


@main.command("validate")
@click.argument(
    "path",
    type=click.Path(path_type=Path, exists=True, dir_okay=False, readable=True),
)
@click.argument("kind", type=click.Choice(list_artifact_kinds()))
def cmd_validate(path: Path, kind: str) -> None:
    """Validate a JSON artifact file against schema + domain model."""
    load_artifact_file(path, kind)
    click.echo(f"ok: {path} ({kind})")


@main.command("info")
def cmd_info() -> None:
    """Print environment summary (paths, fixture mode)."""
    log = get_logger("cli.info")
    repo_root = Path(os.environ.get("ALWM_REPO_ROOT", ".")).resolve()
    fixture_mode = os.environ.get("ALWM_FIXTURE_MODE", "0")
    log.info("info", repo_root=str(repo_root), fixture_mode=fixture_mode)
    click.echo(f"repo_root={repo_root}")
    click.echo(f"fixture_mode={fixture_mode}")
    click.echo(f"version={__version__}")


if __name__ == "__main__":
    try:
        main(obj={})
    except SystemExit as e:
        sys.exit(e.code)
