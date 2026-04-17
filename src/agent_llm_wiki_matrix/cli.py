"""CLI entrypoint for agent-llm-wiki-matrix."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import click

from agent_llm_wiki_matrix import __version__
from agent_llm_wiki_matrix.logging_config import configure_logging, get_logger


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
