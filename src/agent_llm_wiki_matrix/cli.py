"""CLI entrypoint for agent-llm-wiki-matrix."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Literal, cast

import click

from agent_llm_wiki_matrix import __version__
from agent_llm_wiki_matrix.artifacts import list_artifact_kinds, load_artifact_file
from agent_llm_wiki_matrix.benchmark import load_benchmark_definition, run_benchmark
from agent_llm_wiki_matrix.benchmark.live_probe import (
    ollama_model_available,
    probe_ollama_api,
    probe_openai_compatible_api,
)
from agent_llm_wiki_matrix.browser import (
    MockBrowserRunner,
    PlaywrightBrowserRunner,
    evidence_to_prompt_block,
    load_browser_evidence,
)
from agent_llm_wiki_matrix.browser.models import BrowserRunRequest
from agent_llm_wiki_matrix.logging_config import configure_logging, get_logger
from agent_llm_wiki_matrix.models import ComparisonMatrix
from agent_llm_wiki_matrix.pipelines.compare import evaluations_to_matrix
from agent_llm_wiki_matrix.pipelines.evaluate import evaluate_subject, evaluation_to_json
from agent_llm_wiki_matrix.pipelines.ingest import ingest_markdown_pages
from agent_llm_wiki_matrix.pipelines.reporting import (
    build_report_from_matrix,
    render_matrix_markdown,
    render_report_markdown,
)
from agent_llm_wiki_matrix.prompt_registry import (
    find_prompt_entry,
    load_prompt_registry_yaml,
    resolve_prompt_text,
)
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


@main.group("prompts")
def prompts_grp() -> None:
    """Versioned prompt registry under ``prompts/registry.yaml`` (YAML + schema)."""


@prompts_grp.command("check")
@click.option(
    "--registry",
    "registry_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default="prompts/registry.yaml",
    show_default=True,
    help="Registry YAML path relative to ALWM_REPO_ROOT.",
)
def cmd_prompts_check(registry_path: Path) -> None:
    """Validate ``prompts/registry.yaml`` against JSON Schema + Pydantic."""
    repo = Path(os.environ.get("ALWM_REPO_ROOT", ".")).resolve()
    full = (repo / registry_path).resolve()
    if not full.is_file():
        raise click.ClickException(f"Registry file not found: {full}")
    load_prompt_registry_yaml(full)
    click.echo(f"ok: {full}")


@prompts_grp.command("list")
@click.option(
    "--registry",
    "registry_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default="prompts/registry.yaml",
    show_default=True,
)
def cmd_prompts_list(registry_path: Path) -> None:
    """Print prompt ids and paths (tab-separated)."""
    repo = Path(os.environ.get("ALWM_REPO_ROOT", ".")).resolve()
    full = (repo / registry_path).resolve()
    doc = load_prompt_registry_yaml(full)
    for p in doc.prompts:
        click.echo(f"{p.id}\t{p.path}")


@prompts_grp.command("show")
@click.argument("prompt_id")
@click.option(
    "--registry",
    "registry_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default="prompts/registry.yaml",
    show_default=True,
)
def cmd_prompts_show(prompt_id: str, registry_path: Path) -> None:
    """Print prompt body for ``prompt_id`` (path resolved from registry)."""
    repo = Path(os.environ.get("ALWM_REPO_ROOT", ".")).resolve()
    full = (repo / registry_path).resolve()
    doc = load_prompt_registry_yaml(full)
    try:
        entry = find_prompt_entry(doc, prompt_id)
    except KeyError:
        raise click.ClickException(f"Unknown prompt id: {prompt_id}") from None
    text = resolve_prompt_text(repo_root=repo, entry=entry)
    # Avoid double newline when the file already ends with one.
    click.echo(text, nl=not text.endswith("\n"))


@main.group("browser")
def browser_grp() -> None:
    """Browser evidence: mock/file fixtures, or optional Playwright (`run-playwright`)."""


@browser_grp.command("prompt-block")
@click.argument(
    "path",
    type=click.Path(path_type=Path, exists=True, dir_okay=False, readable=True),
)
def cmd_browser_prompt_block(path: Path) -> None:
    """Load a browser_evidence JSON file and print a stable prompt-sized block."""
    evidence = load_browser_evidence(path)
    click.echo(evidence_to_prompt_block(evidence))


@browser_grp.command("run-mock")
@click.option("--scenario-id", default=None, help="Logical id for deterministic output.")
@click.option("--start-url", default=None, help="Optional start URL for the mock trace.")
@click.option(
    "--step",
    "steps",
    multiple=True,
    help="Optional step labels appended to the trace.",
)
def cmd_browser_run_mock(
    scenario_id: str | None,
    start_url: str | None,
    steps: tuple[str, ...],
) -> None:
    """Run MockBrowserRunner and print JSON (offline; no browser binary)."""
    runner = MockBrowserRunner()
    req = BrowserRunRequest(
        scenario_id=scenario_id,
        start_url=start_url,
        steps=list(steps),
    )
    result = runner.run(req)
    click.echo(result.model_dump_json(indent=2))


@browser_grp.command("run-playwright")
@click.option("--scenario-id", default=None, help="Logical id for evidence labeling.")
@click.option(
    "--start-url",
    required=True,
    help="Initial URL (http(s) or file://); each --step resolves relative to the current URL.",
)
@click.option(
    "--step",
    "steps",
    multiple=True,
    help="Additional navigation targets (relative path or absolute URL).",
)
@click.option(
    "--headless/--no-headless",
    default=True,
    show_default=True,
    help="Run browser headless (default) or headed.",
)
def cmd_browser_run_playwright(
    scenario_id: str | None,
    start_url: str,
    steps: tuple[str, ...],
    headless: bool,
) -> None:
    """Run PlaywrightBrowserRunner and print JSON (needs `pip install '.[browser]'`)."""
    runner = PlaywrightBrowserRunner(headless=headless)
    req = BrowserRunRequest(
        scenario_id=scenario_id,
        start_url=start_url,
        steps=list(steps),
    )
    try:
        result = runner.run(req)
    except RuntimeError as e:
        raise click.ClickException(str(e)) from e
    except ValueError as e:
        raise click.ClickException(str(e)) from e
    click.echo(result.model_dump_json(indent=2))


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


@main.command("ingest")
@click.argument(
    "input_dir",
    type=click.Path(path_type=Path, exists=True, file_okay=False, readable=True),
)
@click.argument("output_dir", type=click.Path(path_type=Path, file_okay=False))
@click.option(
    "--created-at",
    default="1970-01-01T00:00:00Z",
    show_default=True,
    help="RFC 3339 timestamp written on each Thought (deterministic ingest).",
)
@click.option(
    "--status",
    type=click.Choice(["draft", "published"]),
    default="draft",
    show_default=True,
)
def cmd_ingest(input_dir: Path, output_dir: Path, created_at: str, status: str) -> None:
    """Convert Markdown pages in INPUT_DIR to Thought JSON files in OUTPUT_DIR."""
    written = ingest_markdown_pages(
        input_dir,
        output_dir,
        created_at=created_at,
        status=cast(Literal["draft", "published"], status),
    )
    for p in written:
        click.echo(f"wrote {p}")


@main.command("evaluate")
@click.option(
    "--subject",
    "subject_path",
    type=click.Path(path_type=Path, exists=True, dir_okay=False, readable=True),
    required=True,
    help="Markdown page or Thought JSON to score.",
)
@click.option(
    "--rubric",
    "rubric_path",
    type=click.Path(path_type=Path, exists=True, dir_okay=False, readable=True),
    required=True,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, file_okay=True, writable=True),
    required=True,
)
@click.option(
    "--id",
    "evaluation_id",
    default=None,
    help="Evaluation id (default: derived from subject and rubric paths).",
)
@click.option("--evaluated-at", default="1970-01-01T00:00:00Z", show_default=True)
def cmd_evaluate(
    subject_path: Path,
    rubric_path: Path,
    out_path: Path,
    evaluation_id: str | None,
    evaluated_at: str,
) -> None:
    """Run deterministic rubric scoring (pipeline evaluator; no network)."""
    eid = evaluation_id or f"eval-{subject_path.stem}-{rubric_path.stem}"
    ev = evaluate_subject(
        subject_path,
        rubric_path,
        evaluation_id=eid,
        evaluated_at=evaluated_at,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(evaluation_to_json(ev), encoding="utf-8")
    click.echo(f"wrote {out_path}")


@main.command("compare")
@click.argument(
    "eval_files",
    nargs=-1,
    required=True,
    type=click.Path(path_type=Path, exists=True, dir_okay=False, readable=True),
)
@click.option("--out", "out_path", type=click.Path(path_type=Path), required=True)
@click.option("--id", "matrix_id", required=True)
@click.option("--title", required=True)
@click.option("--metric", default="per_criterion_score", show_default=True)
@click.option("--created-at", default="1970-01-01T00:00:00Z", show_default=True)
@click.option(
    "--out-md",
    "out_md",
    type=click.Path(path_type=Path),
    default=None,
    help="Optional path to render templates/matrix.md for the same matrix.",
)
def cmd_compare(
    eval_files: tuple[Path, ...],
    out_path: Path,
    matrix_id: str,
    title: str,
    metric: str,
    created_at: str,
    out_md: Path | None,
) -> None:
    """Build a comparison matrix JSON from evaluation artifacts."""
    matrix = evaluations_to_matrix(
        list(eval_files),
        matrix_id=matrix_id,
        title=title,
        metric=metric,
        created_at=created_at,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        matrix.model_dump_json(indent=2, exclude_none=True) + "\n",
        encoding="utf-8",
    )
    click.echo(f"wrote {out_path}")
    if out_md is not None:
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_md.write_text(render_matrix_markdown(matrix), encoding="utf-8")
        click.echo(f"wrote {out_md}")


@main.command("report")
@click.option(
    "--matrix",
    "matrix_path",
    type=click.Path(path_type=Path, exists=True, dir_okay=False, readable=True),
    required=True,
)
@click.option("--out-json", "out_json", type=click.Path(path_type=Path), required=True)
@click.option("--out-md", "out_md", type=click.Path(path_type=Path), required=True)
@click.option("--id", "report_id", required=True)
@click.option("--period-start", default="1970-01-01", show_default=True)
@click.option("--period-end", default="1970-01-07", show_default=True)
def cmd_report(
    matrix_path: Path,
    out_json: Path,
    out_md: Path,
    report_id: str,
    period_start: str,
    period_end: str,
) -> None:
    """Render a Report JSON plus Markdown from a matrix artifact."""
    raw = load_artifact_file(matrix_path, "matrix")
    if not isinstance(raw, ComparisonMatrix):
        msg = "Expected a matrix artifact"
        raise TypeError(msg)
    report = build_report_from_matrix(
        raw,
        report_id=report_id,
        period_start=period_start,
        period_end=period_end,
    )
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(
        report.model_dump_json(indent=2, exclude_none=True) + "\n",
        encoding="utf-8",
    )
    out_md.write_text(render_report_markdown(report), encoding="utf-8")
    click.echo(f"wrote {out_json}")
    click.echo(f"wrote {out_md}")


@main.group("benchmark")
def benchmark_cmd() -> None:
    """Run versioned benchmark harnesses (prompts × variants × backends)."""


@benchmark_cmd.command("run")
@click.option(
    "--definition",
    "definition_path",
    type=click.Path(path_type=Path, exists=True, dir_okay=False, readable=True),
    required=True,
    help="Benchmark YAML or JSON (see benchmarks/v1/).",
)
@click.option(
    "--output-dir",
    "output_dir",
    type=click.Path(path_type=Path, file_okay=False, writable=True),
    required=True,
)
@click.option(
    "--run-id",
    default=None,
    help="Run identifier (default: benchmark id).",
)
@click.option(
    "--created-at",
    default="1970-01-01T00:00:00Z",
    show_default=True,
    help="RFC 3339 timestamp for artifacts (use fixed value for reproducible JSON).",
)
@click.option(
    "--provider-config",
    type=click.Path(path_type=Path, exists=True, dir_okay=False, readable=True),
    default=None,
    help="Optional providers YAML (defaults same as alwm providers show).",
)
@click.option(
    "--no-fixture-mock",
    is_flag=True,
    help="Do not force mock when ALWM_FIXTURE_MODE=1 (for live integration runs).",
)
@click.option(
    "--prompt-registry",
    "prompt_registry_path",
    type=click.Path(path_type=Path, exists=True, dir_okay=False, readable=True),
    default=None,
    help=(
        "Override prompt registry YAML (defaults to definition.prompt_registry_ref "
        "or prompts/registry.yaml when prompts use prompt_ref)."
    ),
)
def cmd_benchmark_run(
    definition_path: Path,
    output_dir: Path,
    run_id: str | None,
    created_at: str,
    provider_config: Path | None,
    no_fixture_mock: bool,
    prompt_registry_path: Path | None,
) -> None:
    """Execute a benchmark definition: responses, evaluations, matrices, report."""
    repo = Path(os.environ.get("ALWM_REPO_ROOT", ".")).resolve()
    dfn = load_benchmark_definition(definition_path)
    rid = run_id or dfn.id
    output_dir.mkdir(parents=True, exist_ok=True)
    run_benchmark(
        dfn,
        repo_root=repo,
        output_dir=output_dir.resolve(),
        created_at=created_at,
        run_id=rid,
        provider_yaml=provider_config,
        environ=os.environ,
        fixture_mode_force_mock=not no_fixture_mock,
        prompt_registry_path=prompt_registry_path,
    )
    click.echo(f"wrote benchmark run under {output_dir}")


@benchmark_cmd.command("probe")
@click.option(
    "--ollama-host",
    envvar="OLLAMA_HOST",
    default="http://127.0.0.1:11434",
    show_default=True,
    help="Ollama base URL (no trailing path).",
)
@click.option(
    "--openai-base-url",
    envvar="OPENAI_BASE_URL",
    default="http://127.0.0.1:8080/v1",
    show_default=True,
    help="OpenAI-compatible base URL (includes /v1).",
)
@click.option(
    "--ollama-model",
    envvar="OLLAMA_MODEL",
    default="llama3.2",
    show_default=True,
    help="Model name to check in GET /api/tags (when Ollama is up).",
)
def cmd_benchmark_probe(ollama_host: str, openai_base_url: str, ollama_model: str) -> None:
    """Check reachability of Ollama and OpenAI-compatible HTTP APIs (for live benchmarks)."""
    o_api = probe_ollama_api(ollama_host)
    o_model = ollama_model_available(ollama_host, ollama_model) if o_api else False
    oa = probe_openai_compatible_api(openai_base_url)
    payload = {
        "ollama_api_reachable": o_api,
        "ollama_model_available": o_model,
        "openai_compatible_api_reachable": oa,
        "ollama_host": ollama_host,
        "openai_base_url": openai_base_url,
        "ollama_model_checked": ollama_model,
    }
    click.echo(json.dumps(payload, indent=2, sort_keys=True))


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
