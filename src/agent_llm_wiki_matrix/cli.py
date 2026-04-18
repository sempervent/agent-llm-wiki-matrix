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
from agent_llm_wiki_matrix.benchmark.campaign_definitions import load_benchmark_campaign_definition
from agent_llm_wiki_matrix.benchmark.campaign_directory_compare import (
    compare_campaign_directories_cli,
)
from agent_llm_wiki_matrix.benchmark.campaign_result_pack import (
    assemble_campaign_result_pack,
    validate_campaign_result_pack_directory,
)
from agent_llm_wiki_matrix.benchmark.campaign_result_pack_compare import (
    compare_campaign_result_packs_cli,
)
from agent_llm_wiki_matrix.benchmark.campaign_runner import run_benchmark_campaign
from agent_llm_wiki_matrix.benchmark.definitions import EvalHybridWeights
from agent_llm_wiki_matrix.benchmark.live_probe import (
    ollama_model_available,
    probe_ollama_api,
    probe_openai_compatible_api,
)
from agent_llm_wiki_matrix.benchmark.persistence import write_pydantic_json
from agent_llm_wiki_matrix.browser import (
    MCPBrowserRunner,
    MockBrowserRunner,
    PlaywrightBrowserRunner,
    evidence_to_prompt_block,
    load_browser_evidence,
)
from agent_llm_wiki_matrix.browser.models import BrowserRunRequest
from agent_llm_wiki_matrix.logging_config import configure_logging, get_logger
from agent_llm_wiki_matrix.models import ComparisonMatrix
from agent_llm_wiki_matrix.pipelines.compare import evaluations_to_matrix
from agent_llm_wiki_matrix.pipelines.evaluate import (
    evaluate_subject,
    evaluation_to_json,
    load_evaluation_subject,
)
from agent_llm_wiki_matrix.pipelines.evaluation_backends import (
    JudgeRepeatParams,
    evaluate_with_scoring_backend,
    judge_live_enabled,
)
from agent_llm_wiki_matrix.pipelines.ingest import ingest_markdown_pages
from agent_llm_wiki_matrix.pipelines.longitudinal import (
    analyze_longitudinal,
    discover_manifest_paths,
    load_run_snapshots,
    write_longitudinal_bundle,
)
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
from agent_llm_wiki_matrix.providers.benchmark_config import load_judge_provider_config
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
    """Browser evidence: mock/file fixtures, `run-mcp` fixture bridge, or Playwright."""


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
    """Run PlaywrightBrowserRunner and print JSON (needs `uv pip install -e ".[browser]"`)."""
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


@browser_grp.command("run-mcp")
@click.option(
    "--stdio",
    is_flag=True,
    help="Use MCP stdio transport (requires ALWM_MCP_BROWSER_COMMAND; see browser.md).",
)
@click.option(
    "--scenario-id",
    default=None,
    help="Load fixtures/browser_evidence/v1/<id>.json under ALWM_REPO_ROOT.",
)
@click.option(
    "--fixture",
    "fixture_relpath",
    default=None,
    help="Repo-relative path to a browser_evidence JSON file.",
)
@click.option(
    "--start-url",
    default=None,
    help="Optional URL for MCP tool arguments (with --stdio).",
)
@click.option(
    "--step",
    "steps",
    multiple=True,
    help="Optional step labels for MCP tool arguments (with --stdio).",
)
def cmd_browser_run_mcp(
    stdio: bool,
    scenario_id: str | None,
    fixture_relpath: str | None,
    start_url: str | None,
    steps: tuple[str, ...],
) -> None:
    """Run MCPBrowserRunner: fixture JSON and/or MCP stdio (see docs/architecture/browser.md)."""
    repo = Path(os.environ.get("ALWM_REPO_ROOT", ".")).resolve()
    if stdio:
        if scenario_id or fixture_relpath:
            raise click.ClickException("Do not combine --stdio with --scenario-id or --fixture.")
        if not os.environ.get("ALWM_MCP_BROWSER_COMMAND", "").strip():
            raise click.ClickException(
                "Set ALWM_MCP_BROWSER_COMMAND to the MCP server argv (e.g. "
                "'python fixtures/mcp_servers/stdio_browser_evidence_server.py')."
            )
        req = BrowserRunRequest(start_url=start_url, steps=list(steps))
    else:
        if not scenario_id and not fixture_relpath:
            raise click.ClickException(
                "Specify --scenario-id or --fixture, or use --stdio with "
                "ALWM_MCP_BROWSER_COMMAND for MCP stdio."
            )
        if scenario_id and fixture_relpath:
            raise click.ClickException("Use either --scenario-id or --fixture, not both.")
        req = BrowserRunRequest(
            scenario_id=scenario_id,
            fixture_relpath=fixture_relpath,
        )
    runner = MCPBrowserRunner(repo)
    try:
        result = runner.run(req)
    except (RuntimeError, FileNotFoundError) as e:
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
@click.option(
    "--scoring-backend",
    type=click.Choice(["deterministic", "semantic_judge", "hybrid"]),
    default="deterministic",
    show_default=True,
    help=(
        "deterministic=byte-hash (default); semantic_judge/hybrid use LLM judge "
        "(mock in fixture mode unless --judge-live)."
    ),
)
@click.option(
    "--judge-provider-config",
    type=click.Path(path_type=Path, exists=True, dir_okay=False, readable=True),
    default=None,
    help="Providers YAML for the judge (defaults env / built-in when omitted).",
)
@click.option(
    "--judge-live",
    is_flag=True,
    help=(
        "Opt-in live judge: use real provider even when ALWM_FIXTURE_MODE=1 "
        "(local experimentation)."
    ),
)
@click.option(
    "--hybrid-deterministic-weight",
    default=0.5,
    show_default=True,
    type=float,
    help="For hybrid: weight on deterministic scores (semantic gets 1 minus this).",
)
@click.option(
    "--judge-repeats",
    default=1,
    show_default=True,
    type=int,
    help="Semantic/hybrid: number of judge runs (aggregated per criterion).",
)
@click.option(
    "--semantic-aggregation",
    type=click.Choice(["mean", "median", "trimmed_mean"]),
    default="mean",
    show_default=True,
    help="How to aggregate scores across judge repeats.",
)
@click.option(
    "--trim-fraction",
    default=0.1,
    show_default=True,
    type=float,
    help="For trimmed_mean: fraction trimmed from each tail before averaging.",
)
@click.option(
    "--judge-max-criterion-range",
    type=float,
    default=None,
    help="Optional: flag low confidence if max criterion range across runs exceeds this.",
)
@click.option(
    "--judge-max-criterion-stdev",
    type=float,
    default=None,
    help="Optional: flag low confidence if any criterion stdev across runs exceeds this.",
)
@click.option(
    "--judge-max-mean-criterion-stdev",
    type=float,
    default=None,
    help="Optional: flag low confidence if mean criterion stdev exceeds this.",
)
@click.option(
    "--judge-max-total-weighted-stdev",
    type=float,
    default=None,
    help="Optional: flag low confidence if stdev of total weighted score exceeds this.",
)
def cmd_evaluate(
    subject_path: Path,
    rubric_path: Path,
    out_path: Path,
    evaluation_id: str | None,
    evaluated_at: str,
    scoring_backend: str,
    judge_provider_config: Path | None,
    judge_live: bool,
    hybrid_deterministic_weight: float,
    judge_repeats: int,
    semantic_aggregation: str,
    trim_fraction: float,
    judge_max_criterion_range: float | None,
    judge_max_criterion_stdev: float | None,
    judge_max_mean_criterion_stdev: float | None,
    judge_max_total_weighted_stdev: float | None,
) -> None:
    """Run rubric scoring (deterministic default; optional semantic or hybrid judge)."""
    repo = Path(os.environ.get("ALWM_REPO_ROOT", ".")).resolve()
    rubric_abs = rubric_path if rubric_path.is_absolute() else (repo / rubric_path).resolve()
    eid = evaluation_id or f"eval-{subject_path.stem}-{rubric_path.stem}"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        eval_ref = str(out_path.resolve().relative_to(repo).as_posix())
    except ValueError:
        eval_ref = str(out_path.resolve())

    if scoring_backend == "deterministic":
        ev = evaluate_subject(
            subject_path,
            rubric_path,
            evaluation_id=eid,
            evaluated_at=evaluated_at,
        )
        out_path.write_text(evaluation_to_json(ev), encoding="utf-8")
        click.echo(f"wrote {out_path}")
        return

    subject_ref, text = load_evaluation_subject(subject_path)
    jl = judge_live or judge_live_enabled(os.environ)
    jcfg = load_judge_provider_config(
        yaml_path=judge_provider_config,
        environ=os.environ,
        judge_live=jl,
    )
    hw = None
    if scoring_backend == "hybrid":
        hw = EvalHybridWeights(
            deterministic_weight=hybrid_deterministic_weight,
            semantic_weight=1.0 - hybrid_deterministic_weight,
        )
    assert scoring_backend in ("semantic_judge", "hybrid")
    sb = cast(Literal["semantic_judge", "hybrid"], scoring_backend)
    jr = JudgeRepeatParams(
        count=judge_repeats,
        strategy=cast(Literal["mean", "median", "trimmed_mean"], semantic_aggregation),
        trim_fraction=trim_fraction,
        max_criterion_range=judge_max_criterion_range,
        max_criterion_stdev=judge_max_criterion_stdev,
        max_mean_criterion_stdev=judge_max_mean_criterion_stdev,
        max_total_weighted_stdev=judge_max_total_weighted_stdev,
    )
    ev, prov, _metrics = evaluate_with_scoring_backend(
        subject_ref=subject_ref,
        text=text,
        rubric_path=rubric_abs,
        evaluation_id=eid,
        evaluated_at=evaluated_at,
        scoring_backend=sb,
        hybrid_weights=hw,
        judge_provider_cfg=jcfg,
        judge_live=jl,
        evaluation_json_relpath=eval_ref,
        judge_repeat=jr,
    )
    prov_path = out_path.parent / f"{out_path.stem}_judge_provenance.json"
    try:
        jp_rel = str(prov_path.resolve().relative_to(repo).as_posix())
    except ValueError:
        jp_rel = str(prov_path.resolve())
    ev = ev.model_copy(update={"judge_provenance_relpath": jp_rel})
    out_path.write_text(evaluation_to_json(ev), encoding="utf-8")
    write_pydantic_json(prov_path, prov)
    click.echo(f"wrote {out_path}")
    click.echo(f"wrote {prov_path}")


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
@click.option(
    "--eval-scoring-backend",
    "eval_scoring_backend",
    type=click.Choice(["deterministic", "semantic_judge", "hybrid"]),
    default=None,
    help="Override benchmark eval_scoring.backend (default: definition or deterministic).",
)
@click.option(
    "--judge-provider-config",
    "judge_provider_config",
    type=click.Path(path_type=Path, exists=True, dir_okay=False, readable=True),
    default=None,
    help=(
        "Providers YAML for semantic/hybrid judge "
        "(defaults to --provider-config or eval_scoring.judge_provider_ref)."
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
    eval_scoring_backend: str | None,
    judge_provider_config: Path | None,
) -> None:
    """Execute a benchmark definition: responses, evaluations, matrices, report.

    Browser-backed variants (``execution_mode: browser_mock``) run the configured
    browser runner, write ``cells/.../browser_evidence.json``, and prepend evidence
    to the provider prompt. For ``browser.runner: playwright``, set
    ``ALWM_BENCHMARK_PLAYWRIGHT=1`` and install the optional ``[browser]`` extra.
    """
    repo = Path(os.environ.get("ALWM_REPO_ROOT", ".")).resolve()
    dfn = load_benchmark_definition(definition_path)
    rid = run_id or dfn.id
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        def_rel = str(definition_path.resolve().relative_to(repo))
    except ValueError:
        def_rel = str(definition_path.resolve())
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
        definition_source_relpath=def_rel,
        eval_scoring_backend=eval_scoring_backend,
        judge_provider_yaml=judge_provider_config,
        judge_live=None,
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
    default="gpt-oss:20b",
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


@benchmark_cmd.group("campaign")
def benchmark_campaign_cmd() -> None:
    """Sweep benchmark suites across providers, scoring backends, and browser configs."""


@benchmark_campaign_cmd.command("run")
@click.option(
    "--definition",
    "definition_path",
    type=click.Path(path_type=Path, exists=True, dir_okay=False, readable=True),
    required=True,
    help="Campaign YAML or JSON (see examples/campaigns/v1/).",
)
@click.option(
    "--output-dir",
    "output_dir",
    type=click.Path(path_type=Path, file_okay=False, writable=True),
    required=True,
)
@click.option(
    "--created-at",
    default="1970-01-01T00:00:00Z",
    show_default=True,
    help="RFC 3339 timestamp for member runs and the campaign manifest.",
)
@click.option(
    "--no-fixture-mock",
    is_flag=True,
    help="Do not force mock providers when ALWM_FIXTURE_MODE=1 (for live integration runs).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Plan sweep only: write campaign-dry-run.json (no member benchmark runs).",
)
def cmd_benchmark_campaign_run(
    definition_path: Path,
    output_dir: Path,
    created_at: str,
    no_fixture_mock: bool,
    dry_run: bool,
) -> None:
    """Execute a campaign sweep: campaign manifest, per-run benchmark manifests, summaries."""
    repo = Path(os.environ.get("ALWM_REPO_ROOT", ".")).resolve()
    campaign = load_benchmark_campaign_definition(definition_path)
    out = output_dir.resolve()
    manifest = run_benchmark_campaign(
        repo_root=repo,
        campaign=campaign,
        campaign_definition_path=definition_path.resolve(),
        output_dir=out,
        created_at=created_at,
        environ=os.environ,
        fixture_mode_force_mock=not no_fixture_mock,
        dry_run=dry_run,
    )
    if dry_run:
        click.echo(
            f"dry-run: planned {manifest.run_count} run(s); "
            f"see {out / 'campaign-dry-run.json'} and {out / 'manifest.json'}",
        )
    else:
        click.echo(f"wrote campaign with {len(manifest.runs)} run(s) under {out}")


@benchmark_campaign_cmd.command("plan")
@click.option(
    "--definition",
    "definition_path",
    type=click.Path(path_type=Path, exists=True, dir_okay=False, readable=True),
    required=True,
    help="Campaign YAML or JSON (see examples/campaigns/v1/).",
)
@click.option(
    "--output-dir",
    "output_dir",
    type=click.Path(path_type=Path, file_okay=False, writable=True),
    required=True,
)
@click.option(
    "--created-at",
    default="1970-01-01T00:00:00Z",
    show_default=True,
    help="RFC 3339 timestamp stamped on planned manifest and summaries.",
)
def cmd_benchmark_campaign_plan(
    definition_path: Path,
    output_dir: Path,
    created_at: str,
) -> None:
    """Plan a campaign sweep without executing member runs (manifest + dry-run plan)."""
    repo = Path(os.environ.get("ALWM_REPO_ROOT", ".")).resolve()
    campaign = load_benchmark_campaign_definition(definition_path)
    out = output_dir.resolve()
    manifest = run_benchmark_campaign(
        repo_root=repo,
        campaign=campaign,
        campaign_definition_path=definition_path.resolve(),
        output_dir=out,
        created_at=created_at,
        environ=os.environ,
        fixture_mode_force_mock=True,
        dry_run=True,
    )
    planned = manifest.run_count if manifest.run_count is not None else 0
    click.echo(f"planned {planned} run(s); wrote dry-run manifest under {out}")


@benchmark_campaign_cmd.command("pack")
@click.argument(
    "campaign_dir",
    type=click.Path(file_okay=False, path_type=Path, exists=True),
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(file_okay=False, path_type=Path),
    required=True,
    help="Directory to write the pack (created if missing).",
)
@click.option(
    "--pack-id",
    required=True,
    help="Stable identifier for this pack (e.g. minimal-offline-pack).",
)
@click.option(
    "--title",
    default=None,
    help="Override pack title (default: title from the campaign manifest).",
)
@click.option(
    "--source-label",
    default=None,
    help=(
        "Optional repo-relative label stored in the pack "
        "(e.g. examples/campaign_runs/minimal_offline)."
    ),
)
@click.option(
    "--created-at",
    default="1970-01-01T00:00:00Z",
    show_default=True,
    help="RFC 3339 timestamp for the pack manifest.",
)
@click.option(
    "--member-depth",
    type=click.Choice(["full", "manifest"]),
    default="full",
    show_default=True,
    help="Copy full per-run trees or only manifest.json per member.",
)
@click.option(
    "--run-index",
    "run_indices",
    multiple=True,
    type=int,
    help="Include only these member run indices (0-based; repeatable).",
)
@click.option(
    "--include-failed-members",
    is_flag=True,
    help="Include member runs that did not succeed (default: succeeded only).",
)
@click.option(
    "--record-source-abspath",
    is_flag=True,
    help="Record absolute source path in pack JSON (default off for git-friendly bundles).",
)
@click.option("--notes", default=None, help="Optional operator notes stored in the pack.")
def cmd_benchmark_campaign_pack(
    campaign_dir: Path,
    output_dir: Path,
    pack_id: str,
    title: str | None,
    source_label: str | None,
    created_at: str,
    member_depth: Literal["full", "manifest"],
    run_indices: tuple[int, ...],
    include_failed_members: bool,
    record_source_abspath: bool,
    notes: str | None,
) -> None:
    """Assemble a markdown-first campaign result pack from a completed campaign directory."""
    idx_set: set[int] | None = set(run_indices) if run_indices else None
    pack = assemble_campaign_result_pack(
        campaign_dir=campaign_dir.resolve(),
        pack_dir=output_dir.resolve(),
        pack_id=pack_id,
        title=title,
        created_at=created_at,
        run_indices=idx_set,
        member_depth=member_depth,
        source_campaign_relpath=source_label,
        notes=notes,
        only_succeeded_members=not include_failed_members,
        record_source_abspath=record_source_abspath,
    )
    out = output_dir.resolve()
    click.echo(
        f"wrote result pack {pack.pack_id} with {len(pack.member_runs)} member run(s) under {out}",
    )


@benchmark_campaign_cmd.command("pack-check")
@click.argument(
    "pack_dir",
    type=click.Path(file_okay=False, path_type=Path, exists=True),
)
@click.option(
    "--strict",
    "strict_portability",
    is_flag=True,
    help="Treat portability hints (e.g. manifest-only members) as errors.",
)
def cmd_benchmark_campaign_pack_check(pack_dir: Path, strict_portability: bool) -> None:
    """Validate pack completeness: files on disk, schema/kinds, manifest/summary consistency."""
    result = validate_campaign_result_pack_directory(
        pack_dir.resolve(),
        strict_portability=strict_portability,
    )
    for line in result.errors:
        click.echo(line, err=True)
    for line in result.warnings:
        click.echo(line, err=True)
    if not result.ok(strict_portability=strict_portability):
        raise SystemExit(1)
    click.echo("pack-check: ok")


@benchmark_campaign_cmd.command("compare-packs")
@click.argument(
    "left_pack",
    type=click.Path(file_okay=False, path_type=Path, exists=True),
)
@click.argument(
    "right_pack",
    type=click.Path(file_okay=False, path_type=Path, exists=True),
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(file_okay=False, path_type=Path),
    required=True,
    help="Directory for pack-compare.json and pack-compare-report.md (created if missing).",
)
@click.option(
    "--left-label",
    default=None,
    help="Display label for the left pack (default: path string).",
)
@click.option(
    "--right-label",
    default=None,
    help="Display label for the right pack (default: path string).",
)
@click.option(
    "--repo-root",
    type=click.Path(file_okay=False, path_type=Path, exists=True),
    default=None,
    help=(
        "If set, store pack paths in JSON/Markdown relative to this directory "
        "(portable committed reports; default: absolute paths)."
    ),
)
def cmd_benchmark_campaign_compare_packs(
    left_pack: Path,
    right_pack: Path,
    output_dir: Path,
    left_label: str | None,
    right_label: str | None,
    repo_root: Path | None,
) -> None:
    """Compare two campaign result packs: fingerprints, artifacts, scores, FT-*, portability."""
    jp, mp = compare_campaign_result_packs_cli(
        left_pack,
        right_pack,
        output_dir=output_dir,
        left_label=left_label,
        right_label=right_label,
        repo_root=repo_root,
    )
    click.echo(f"wrote {jp}")
    click.echo(f"wrote {mp}")


@benchmark_campaign_cmd.command("compare")
@click.argument(
    "left_campaign",
    type=click.Path(file_okay=False, path_type=Path, exists=True),
)
@click.argument(
    "right_campaign",
    type=click.Path(file_okay=False, path_type=Path, exists=True),
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(file_okay=False, path_type=Path),
    required=True,
    help="Directory for campaign-compare.json and campaign-compare-report.md.",
)
@click.option(
    "--left-label",
    default=None,
    help="Display label for the left campaign (default: path string).",
)
@click.option(
    "--right-label",
    default=None,
    help="Display label for the right campaign (default: path string).",
)
@click.option(
    "--repo-root",
    type=click.Path(file_okay=False, path_type=Path, exists=True),
    default=None,
    help=(
        "If set, store campaign paths in JSON/Markdown relative to this directory "
        "(portable committed reports; default: absolute paths)."
    ),
)
@click.option(
    "--created-at",
    default=None,
    help="RFC 3339 timestamp for the comparison manifest (default: now; use fixed for repro).",
)
def cmd_benchmark_campaign_compare(
    left_campaign: Path,
    right_campaign: Path,
    output_dir: Path,
    left_label: str | None,
    right_label: str | None,
    repo_root: Path | None,
    created_at: str | None,
) -> None:
    """Compare two completed campaign directories (manifests, summaries, analysis, semantics)."""
    jp, mp = compare_campaign_directories_cli(
        left_campaign,
        right_campaign,
        output_dir=output_dir,
        left_label=left_label,
        right_label=right_label,
        repo_root=repo_root,
        created_at=created_at,
    )
    click.echo(f"wrote {jp}")
    click.echo(f"wrote {mp}")


@benchmark_cmd.command("longitudinal")
@click.option(
    "--runs-glob",
    required=True,
    help=(
        "Glob for benchmark manifests, relative to repo root "
        "(e.g. fixtures/longitudinal/paired/*/manifest.json)."
    ),
)
@click.option(
    "--out-dir",
    type=click.Path(path_type=Path, file_okay=False, writable=True),
    required=True,
    help="Output directory for the longitudinal bundle (Markdown + summary.json).",
)
@click.option(
    "--title",
    default="Longitudinal benchmark analysis",
    show_default=True,
    help="Title line in longitudinal.md.",
)
@click.option(
    "--regression-delta",
    default=0.03,
    type=float,
    show_default=True,
    help="Min absolute score drop (per cell) to flag regression vs prior run.",
)
@click.option(
    "--low-score",
    default=0.55,
    type=float,
    show_default=True,
    help="Scores below this trigger FT-ABS-LOW; recurring uses --min-recurring.",
)
@click.option(
    "--min-recurring",
    default=2,
    type=int,
    show_default=True,
    help="Min distinct runs below --low-score to flag FT-RECUR-LOW.",
)
@click.option(
    "--mode-gap",
    default=0.12,
    type=float,
    show_default=True,
    help="Min spread across execution modes (same prompt, one run) for FT-MODE-GAP.",
)
@click.option(
    "--semantic-stdev-threshold",
    default=0.12,
    type=float,
    show_default=True,
    help="Flag FT-JUDGE-UNSTABLE when repeat total_weighted_stdev exceeds this.",
)
@click.option(
    "--semantic-range-threshold",
    default=0.22,
    type=float,
    show_default=True,
    help="Flag FT-JUDGE-UNSTABLE when max_range_across_criteria exceeds this.",
)
@click.option(
    "--series-swing-threshold",
    default=0.06,
    type=float,
    show_default=True,
    help="Flag FT-SERIES-SWING when population stdev of total scores exceeds this (≥3 runs).",
)
@click.option(
    "--min-runs-for-swing",
    default=3,
    type=int,
    show_default=True,
    help="Minimum snapshots per cell to evaluate FT-SERIES-SWING.",
)
def cmd_benchmark_longitudinal(
    runs_glob: str,
    out_dir: Path,
    title: str,
    regression_delta: float,
    low_score: float,
    min_recurring: int,
    mode_gap: float,
    semantic_stdev_threshold: float,
    semantic_range_threshold: float,
    series_swing_threshold: float,
    min_runs_for_swing: int,
) -> None:
    """Build weekly, longitudinal, regression, and provider Markdown plus failure atlas."""
    repo = Path(os.environ.get("ALWM_REPO_ROOT", ".")).resolve()
    paths = discover_manifest_paths(repo, runs_glob)
    if not paths:
        msg = f"No manifests matched {runs_glob!r} under {repo}"
        raise click.ClickException(msg)
    snaps = load_run_snapshots(repo, paths)
    analysis = analyze_longitudinal(
        snaps,
        regression_delta=regression_delta,
        low_score=low_score,
        min_recurring=min_recurring,
        mode_gap_threshold=mode_gap,
        semantic_stdev_threshold=semantic_stdev_threshold,
        semantic_range_threshold=semantic_range_threshold,
        series_swing_threshold=series_swing_threshold,
        min_runs_for_swing=min_runs_for_swing,
    )
    out = out_dir.resolve()
    write_longitudinal_bundle(repo, analysis, out, title=title)
    click.echo(f"wrote longitudinal bundle under {out} ({len(snaps)} run(s))")


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
