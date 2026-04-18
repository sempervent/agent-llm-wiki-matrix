"""Execute a benchmark campaign: sweep suites × providers × eval scoring × browser configs."""

from __future__ import annotations

import json
import os
import subprocess
import time
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from agent_llm_wiki_matrix.benchmark.campaign_definitions import BenchmarkCampaignDefinitionV1
from agent_llm_wiki_matrix.benchmark.campaign_reporting import (
    merge_generated_report_paths,
    render_campaign_at_a_glance_markdown,
    write_campaign_comparative_artifacts,
)
from agent_llm_wiki_matrix.benchmark.campaign_semantic_summary import (
    write_campaign_semantic_summary_artifacts,
)
from agent_llm_wiki_matrix.benchmark.definitions import (
    BenchmarkDefinitionV1,
    BrowserBenchConfig,
    EvalScoringSpec,
    load_benchmark_definition,
)
from agent_llm_wiki_matrix.benchmark.fingerprints import build_campaign_experiment_fingerprints
from agent_llm_wiki_matrix.benchmark.observability import (
    render_campaign_aggregated_runtime_markdown,
)
from agent_llm_wiki_matrix.benchmark.persistence import (
    write_benchmark_campaign_manifest,
    write_json_sorted,
    write_utf8_text,
)
from agent_llm_wiki_matrix.benchmark.runner import run_benchmark
from agent_llm_wiki_matrix.models import (
    BenchmarkCampaignManifest,
    BenchmarkCampaignRunEntry,
    BenchmarkRunManifest,
    CampaignAggregatedRuntimeV1,
    CampaignFailureRecord,
    CampaignGeneratedReportPaths,
    CampaignRunStatusSummary,
    CampaignSemanticSummaryV1,
    CampaignSummaryV1,
)
from agent_llm_wiki_matrix.pipelines.longitudinal import LongitudinalAnalysis, RunSnapshot


def _eval_label(opt: EvalScoringSpec | None) -> str:
    if opt is None:
        return "suite_default"
    return opt.backend


def _filter_execution_modes(
    dfn: BenchmarkDefinitionV1,
    modes: list[Literal["cli", "browser_mock", "repo_governed"]] | None,
) -> BenchmarkDefinitionV1:
    if not modes:
        return dfn
    allow = frozenset(modes)
    kept = [v for v in dfn.variants if v.execution_mode in allow]
    if not kept:
        msg = (
            f"No variants left after execution_modes filter {sorted(allow)!r} "
            f"for benchmark {dfn.id!r}"
        )
        raise ValueError(msg)
    return dfn.model_copy(update={"variants": kept})


def _merge_eval(dfn: BenchmarkDefinitionV1, opt: EvalScoringSpec | None) -> BenchmarkDefinitionV1:
    if opt is None:
        return dfn
    return dfn.model_copy(update={"eval_scoring": opt})


def _merge_browser(
    dfn: BenchmarkDefinitionV1,
    browser: BrowserBenchConfig | None,
) -> BenchmarkDefinitionV1:
    if browser is None:
        return dfn
    new_variants = []
    for v in dfn.variants:
        if v.execution_mode == "browser_mock":
            new_variants.append(v.model_copy(update={"browser": browser}))
        else:
            new_variants.append(v)
    return dfn.model_copy(update={"variants": new_variants})


def _merge_campaign_tags(
    dfn: BenchmarkDefinitionV1,
    campaign_id: str,
    extra_tags: list[str],
    run_index: int,
) -> BenchmarkDefinitionV1:
    tags = [
        *dfn.tags,
        f"campaign:{campaign_id}",
        f"campaign_run:{run_index:04d}",
        *extra_tags,
    ]
    return dfn.model_copy(update={"tags": tags})


def _merge_prompt_registry(
    dfn: BenchmarkDefinitionV1,
    override: str | None,
) -> BenchmarkDefinitionV1:
    if override is None:
        return dfn
    return dfn.model_copy(update={"prompt_registry_ref": override})


def _has_browser_mock(dfn: BenchmarkDefinitionV1) -> bool:
    return any(v.execution_mode == "browser_mock" for v in dfn.variants)


def mean_score_for_benchmark_run(run_dir: Path) -> tuple[float | None, int]:
    """Mean of per-cell total_weighted_score from evaluation.json files."""
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.is_file():
        return None, 0
    raw_m = json.loads(manifest_path.read_text(encoding="utf-8"))
    cells = raw_m.get("cells", [])
    if not isinstance(cells, list):
        return None, 0
    total = 0.0
    n = 0
    for cell in cells:
        er = cell.get("evaluation_relpath")
        if not isinstance(er, str):
            continue
        ep = run_dir / er
        if not ep.is_file():
            continue
        ev = json.loads(ep.read_text(encoding="utf-8"))
        total += float(ev["total_weighted_score"])
        n += 1
    if n == 0:
        return None, 0
    return total / n, n


def _git_meta(repo_root: Path) -> tuple[str | None, str | None]:
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        desc = subprocess.run(
            ["git", "describe", "--tags", "--always", "--dirty"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        commit = sha.stdout.strip() if sha.returncode == 0 and sha.stdout.strip() else None
        d = desc.stdout.strip() if desc.returncode == 0 and desc.stdout.strip() else None
        return commit, d
    except (OSError, subprocess.TimeoutExpired):
        return None, None


def _utc_now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def render_campaign_summary_markdown(
    manifest: BenchmarkCampaignManifest,
    *,
    longitudinal_bundle: tuple[list[RunSnapshot], LongitudinalAnalysis] | None = None,
    semantic_summary: CampaignSemanticSummaryV1 | None = None,
) -> str:
    """Human-readable summary for campaign-summary.md."""
    lines = [
        f"# Campaign summary: `{manifest.campaign_id}`",
        "",
        "One-page index: **metadata**, **snapshot digest** (headline signals), **member runs**, "
        "and pointers to generated reports.",
        "",
        "## Metadata",
        "",
        f"- **Title:** {manifest.title}",
        f"- **Created:** `{manifest.created_at}`",
        f"- **Definition:** `{manifest.definition_source_relpath}`",
    ]
    if manifest.campaign_definition_fingerprint:
        lines.append(f"- **Definition fingerprint:** `{manifest.campaign_definition_fingerprint}`")
    if manifest.campaign_experiment_fingerprints is not None:
        cef = manifest.campaign_experiment_fingerprints
        lines.extend(
            [
                "",
                "## Experiment fingerprints (six axes)",
                "",
                "Stable per-axis hashes for longitudinal grouping and comparability checks "
                "(see `docs/workflows/longitudinal-reporting.md`).",
                "",
                f"- **campaign_definition:** `{cef.campaign_definition}`",
                f"- **suite_definitions:** `{cef.suite_definitions}`",
                f"- **provider_configs:** `{cef.provider_configs}`",
                f"- **scoring_configs:** `{cef.scoring_configs}`",
                f"- **browser_configs:** `{cef.browser_configs}`",
                f"- **prompt_registry_state:** `{cef.prompt_registry_state}`",
            ],
        )
    lines.extend(
        [
            "",
            "## Execution context",
            "",
            f"- **fixture_mode_force_mock:** `{manifest.fixture_mode_force_mock}`",
            f"- **dry_run:** `{manifest.dry_run}`",
            f"- **Planned runs:** {len(manifest.runs)}",
        ],
    )
    if manifest.run_status_summary:
        rs = manifest.run_status_summary
        lines.append(f"- **Succeeded / failed:** {rs.succeeded} / {rs.failed}")
    if manifest.git_commit_sha:
        lines.append(f"- **git_commit:** `{manifest.git_commit_sha}`")
    if manifest.git_describe:
        lines.append(f"- **git_describe:** `{manifest.git_describe}`")
    if manifest.aggregated_runtime is not None:
        lines.append(render_campaign_aggregated_runtime_markdown(manifest.aggregated_runtime))
    at_a_glance = render_campaign_at_a_glance_markdown(
        manifest,
        longitudinal_bundle=longitudinal_bundle,
        semantic_summary=semantic_summary,
    )
    lines.append("")
    lines.append(at_a_glance.rstrip())
    lines.extend(
        [
            "",
            "## Member run index",
            "",
            "One row per planned member benchmark run (including failures). **Mean score** is the "
            "run-level mean of total weighted cell scores when present.",
            "",
            (
                "| # | run_id | suite | benchmark_id | eval axis | modes filter | "
                "status | mean score | cells |"
            ),
            "| ---: | --- | --- | --- | --- | --- | --- | ---: | ---: |",
        ],
    )
    for r in manifest.runs:
        mf = r.execution_modes_filter
        modes_s = ",".join(mf) if mf else "—"
        if r.mean_total_weighted_score is not None:
            mean_s = f"{r.mean_total_weighted_score:.6f}"
        else:
            mean_s = "—"
        lines.append(
            f"| {r.run_index} | `{r.run_id}` | `{r.suite_ref}` | `{r.benchmark_id}` | "
            f"{r.eval_scoring_label} | {modes_s} | {r.status} | {mean_s} | {r.cell_count} |",
        )
    if manifest.failures:
        lines.extend(["", "## Failures", ""])
        for f in manifest.failures:
            lines.append(f"- **{f.run_id}** (index {f.run_index}): {f.message}")
    if manifest.generated_report_paths:
        gp = manifest.generated_report_paths
        if (
            gp.campaign_comparative_report_md
            or gp.campaign_analysis_json
            or gp.campaign_semantic_summary_json
            or gp.campaign_semantic_summary_md
        ):
            lines.extend(["", "## Generated reports", ""])
            if gp.campaign_comparative_report_md:
                lines.append(
                    f"- **Comparative:** `{gp.campaign_comparative_report_md}` "
                    "(narrative + fingerprint + failure atlas)",
                )
            if gp.campaign_analysis_json:
                lines.append(f"- **Analysis JSON:** `{gp.campaign_analysis_json}`")
            if gp.campaign_semantic_summary_json or gp.campaign_semantic_summary_md:
                lines.extend(["", "### Semantic / hybrid judge rollup", ""])
                if gp.campaign_semantic_summary_md:
                    lines.append(f"- **Markdown:** `{gp.campaign_semantic_summary_md}`")
                if gp.campaign_semantic_summary_json:
                    lines.append(f"- **JSON:** `{gp.campaign_semantic_summary_json}`")
    lines.extend(
        [
            "",
            "## Longitudinal follow-up",
            "",
            "Each **succeeded** row is a standard benchmark tree under `runs/runNNNN/`. Point "
            "**`alwm benchmark longitudinal`** (or other tooling) at `runs/*/manifest.json` under "
            "this campaign root. See **`docs/workflows/longitudinal-reporting.md`**.",
            "",
        ],
    )
    return "\n".join(lines)


def _inputs_snapshot(campaign: BenchmarkCampaignDefinitionV1) -> dict[str, object]:
    return {
        "suite_refs": list(campaign.suite_refs),
        "provider_config_refs": list(campaign.provider_config_refs),
        "eval_scoring_options": [
            o.model_dump(mode="json") if o is not None else None
            for o in campaign.eval_scoring_options
        ],
        "execution_modes": campaign.execution_modes,
        "browser_configs": [
            b.model_dump(mode="json") if b is not None else None for b in campaign.browser_configs
        ],
        "prompt_registry_ref": campaign.prompt_registry_ref,
    }


def run_benchmark_campaign(
    *,
    repo_root: Path,
    campaign: BenchmarkCampaignDefinitionV1,
    campaign_definition_path: Path,
    output_dir: Path,
    created_at: str,
    environ: Mapping[str, str] | None = None,
    fixture_mode_force_mock: bool = True,
    dry_run: bool = False,
) -> BenchmarkCampaignManifest:
    """Execute the Cartesian sweep and write campaign manifest + per-run benchmark trees."""
    repo_root = repo_root.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    runs_root = output_dir / "runs"
    if not dry_run:
        runs_root.mkdir(parents=True, exist_ok=True)

    try:
        def_rel = str(campaign_definition_path.resolve().relative_to(repo_root))
    except ValueError:
        def_rel = str(campaign_definition_path.resolve())

    experiment_fp = build_campaign_experiment_fingerprints(repo_root, campaign)
    fp = experiment_fp.campaign_definition
    env: Mapping[str, str] = os.environ if environ is None else environ
    started = _utc_now_iso()
    t0 = time.perf_counter()
    git_sha, git_desc = _git_meta(repo_root)

    entries: list[BenchmarkCampaignRunEntry] = []
    failures: list[CampaignFailureRecord] = []
    agg_rt = CampaignAggregatedRuntimeV1()
    run_index = 0

    planned_count = 0
    for suite_ref in campaign.suite_refs:
        suite_path = repo_root / suite_ref
        base = load_benchmark_definition(suite_path)
        base = _merge_prompt_registry(base, campaign.prompt_registry_ref)
        base = _filter_execution_modes(base, campaign.execution_modes)
        browser_axis = campaign.browser_configs if _has_browser_mock(base) else [None]

        for prov in campaign.provider_config_refs:
            provider_yaml: Path | None
            if prov is None:
                provider_yaml = None
            else:
                provider_yaml = (repo_root / prov).resolve()
                if not provider_yaml.is_file():
                    msg = f"Campaign provider_config_ref not found: {prov}"
                    raise FileNotFoundError(msg)

            for evo in campaign.eval_scoring_options:
                for bcfg in browser_axis:
                    planned_count += 1
                    if dry_run:
                        run_index += 1
                        continue

                    dfn = _merge_eval(base, evo)
                    dfn = _merge_browser(dfn, bcfg)
                    dfn = _merge_campaign_tags(dfn, campaign.id, campaign.campaign_tags, run_index)

                    run_id = f"{campaign.id}__{run_index:04d}"
                    run_dir = runs_root / f"run{run_index:04d}"
                    run_dir.mkdir(parents=True, exist_ok=True)

                    pr_path: Path | None = None
                    if campaign.prompt_registry_ref:
                        pr_path = (repo_root / campaign.prompt_registry_ref).resolve()

                    t_run0 = time.perf_counter()
                    err_msg: str | None = None
                    try:
                        run_benchmark(
                            dfn,
                            repo_root=repo_root,
                            output_dir=run_dir,
                            created_at=created_at,
                            run_id=run_id,
                            provider_yaml=provider_yaml,
                            environ=env,
                            fixture_mode_force_mock=fixture_mode_force_mock,
                            prompt_registry_path=pr_path,
                            definition_source_relpath=suite_ref,
                            eval_scoring_backend=None,
                            judge_provider_yaml=None,
                            judge_live=None,
                        )
                    except Exception as e:
                        err_msg = f"{type(e).__name__}: {e}"
                        failures.append(
                            CampaignFailureRecord(
                                run_index=run_index,
                                run_id=run_id,
                                message=err_msg,
                            ),
                        )
                        err_path = run_dir / "campaign_run_error.json"
                        err_path.write_text(
                            json.dumps({"error": err_msg}, indent=2) + "\n",
                            encoding="utf-8",
                        )
                    run_elapsed = time.perf_counter() - t_run0

                    out_rel = f"runs/run{run_index:04d}"
                    man_rel = f"{out_rel}/manifest.json"
                    mean: float | None = None
                    n_cells = 0
                    st: Literal["succeeded", "failed"] = "succeeded"
                    cf = None
                    if err_msg:
                        st = "failed"
                    else:
                        mean, n_cells = mean_score_for_benchmark_run(run_dir)
                        member_mf = BenchmarkRunManifest.model_validate(
                            json.loads((run_dir / "manifest.json").read_text(encoding="utf-8")),
                        )
                        cf = member_mf.comparison_fingerprints
                        if member_mf.runtime_summary is not None:
                            rs = member_mf.runtime_summary
                            agg_rt.total_browser_phase_seconds += rs.browser_phase_seconds
                            agg_rt.total_provider_completion_seconds += (
                                rs.provider_completion_seconds
                            )
                            agg_rt.total_evaluation_phase_seconds += rs.evaluation_phase_seconds
                            agg_rt.total_judge_phase_seconds += rs.judge_phase_seconds
                            agg_rt.member_runs_timed += 1
                        if member_mf.retry_summary is not None:
                            rr = member_mf.retry_summary
                            agg_rt.total_judge_invocations += rr.total_judge_invocations
                            agg_rt.cells_with_judge_parse_fallback += (
                                rr.cells_with_judge_parse_fallback
                            )
                    entries.append(
                        BenchmarkCampaignRunEntry(
                            run_index=run_index,
                            run_id=run_id,
                            suite_ref=suite_ref,
                            benchmark_id=dfn.id,
                            provider_config_ref=prov,
                            eval_scoring_label=_eval_label(evo),
                            execution_modes_filter=list(campaign.execution_modes)
                            if campaign.execution_modes
                            else None,
                            browser_config_applied=bcfg is not None,
                            status=st,
                            error=err_msg,
                            duration_seconds=round(run_elapsed, 6),
                            output_relpath=out_rel,
                            manifest_relpath=man_rel,
                            comparison_fingerprints=cf,
                            mean_total_weighted_score=mean,
                            cell_count=n_cells,
                        ),
                    )
                    run_index += 1

    if dry_run:
        finished = _utc_now_iso()
        dur = time.perf_counter() - t0
        manifest = BenchmarkCampaignManifest(
            schema_version=1,
            campaign_id=campaign.id,
            title=campaign.title,
            created_at=created_at,
            definition_source_relpath=def_rel,
            fixture_mode_force_mock=fixture_mode_force_mock,
            campaign_definition_fingerprint=fp,
            campaign_experiment_fingerprints=experiment_fp,
            campaign_version=campaign.campaign_version,
            description=campaign.description,
            owner=campaign.owner,
            definition_created_at=campaign.created_at,
            tags=list(campaign.campaign_tags),
            notes=campaign.notes,
            expected_artifact_kinds=list(campaign.expected_artifact_kinds),
            retry_policy=campaign.retry_policy,
            time_budget_seconds=campaign.time_budget_seconds,
            token_budget=campaign.token_budget,
            dry_run=True,
            run_status_summary=CampaignRunStatusSummary(succeeded=0, failed=0),
            run_count=planned_count,
            started_at_utc=started,
            finished_at_utc=finished,
            duration_seconds=round(dur, 6),
            failures=[],
            generated_report_paths=CampaignGeneratedReportPaths(),
            git_commit_sha=git_sha,
            git_describe=git_desc,
            inputs_snapshot=_inputs_snapshot(campaign),
            runs=[],
        )
        write_benchmark_campaign_manifest(output_dir / "manifest.json", manifest)
        plan = {
            "schema_version": 1,
            "campaign_id": campaign.id,
            "planned_run_count": planned_count,
            "inputs": _inputs_snapshot(campaign),
            "campaign_definition_fingerprint": fp,
            "campaign_experiment_fingerprints": experiment_fp.model_dump(mode="json"),
        }
        write_json_sorted(output_dir / "campaign-dry-run.json", plan)
        summary = CampaignSummaryV1(
            schema_version=1,
            campaign_id=campaign.id,
            title=campaign.title,
            created_at=created_at,
            definition_source_relpath=def_rel,
            fixture_mode_force_mock=fixture_mode_force_mock,
            campaign_definition_fingerprint=fp,
            campaign_experiment_fingerprints=experiment_fp,
            campaign_version=campaign.campaign_version,
            run_count=planned_count,
            run_status_summary=CampaignRunStatusSummary(succeeded=0, failed=0),
            dry_run=True,
            failures=[],
            git_commit_sha=git_sha,
            git_describe=git_desc,
            runs=[],
        )
        _write_campaign_summary(
            output_dir,
            summary,
            manifest,
            longitudinal_bundle=None,
            semantic_summary=None,
        )
        return manifest

    succeeded = sum(1 for e in entries if e.status == "succeeded")
    failed = sum(1 for e in entries if e.status == "failed")
    finished = _utc_now_iso()
    dur = time.perf_counter() - t0
    aggregated_runtime = agg_rt if agg_rt.member_runs_timed > 0 else None

    manifest = BenchmarkCampaignManifest(
        schema_version=1,
        campaign_id=campaign.id,
        title=campaign.title,
        created_at=created_at,
        definition_source_relpath=def_rel,
        fixture_mode_force_mock=fixture_mode_force_mock,
        campaign_definition_fingerprint=fp,
        campaign_experiment_fingerprints=experiment_fp,
        campaign_version=campaign.campaign_version,
        description=campaign.description,
        owner=campaign.owner,
        definition_created_at=campaign.created_at,
        tags=list(campaign.campaign_tags),
        notes=campaign.notes,
        expected_artifact_kinds=list(campaign.expected_artifact_kinds),
        retry_policy=campaign.retry_policy,
        time_budget_seconds=campaign.time_budget_seconds,
        token_budget=campaign.token_budget,
        dry_run=False,
        run_status_summary=CampaignRunStatusSummary(succeeded=succeeded, failed=failed),
        run_count=len(entries),
        started_at_utc=started,
        finished_at_utc=finished,
        duration_seconds=round(dur, 6),
        failures=failures,
        generated_report_paths=CampaignGeneratedReportPaths(),
        git_commit_sha=git_sha,
        git_describe=git_desc,
        inputs_snapshot=_inputs_snapshot(campaign),
        runs=entries,
        aggregated_runtime=aggregated_runtime,
    )
    semantic_paths, semantic_model = write_campaign_semantic_summary_artifacts(
        repo_root=repo_root,
        campaign_dir=output_dir,
        manifest=manifest,
    )
    manifest = manifest.model_copy(
        update={
            "generated_report_paths": merge_generated_report_paths(
                manifest.generated_report_paths,
                semantic_paths,
            ),
        },
    )
    extra_paths, longitudinal_bundle = write_campaign_comparative_artifacts(
        repo_root,
        output_dir,
        manifest,
        semantic_summary=semantic_model,
    )
    manifest = manifest.model_copy(
        update={
            "generated_report_paths": merge_generated_report_paths(
                manifest.generated_report_paths,
                extra_paths,
            ),
        },
    )
    write_benchmark_campaign_manifest(output_dir / "manifest.json", manifest)

    run_rows: list[dict[str, Any]] = [e.model_dump(mode="json", exclude_none=True) for e in entries]
    summary = CampaignSummaryV1(
        schema_version=1,
        campaign_id=campaign.id,
        title=campaign.title,
        created_at=created_at,
        definition_source_relpath=def_rel,
        fixture_mode_force_mock=fixture_mode_force_mock,
        campaign_definition_fingerprint=fp,
        campaign_experiment_fingerprints=experiment_fp,
        campaign_version=campaign.campaign_version,
        run_count=len(entries),
        run_status_summary=CampaignRunStatusSummary(succeeded=succeeded, failed=failed),
        dry_run=False,
        failures=failures,
        git_commit_sha=git_sha,
        git_describe=git_desc,
        runs=run_rows,
    )
    _write_campaign_summary(
        output_dir,
        summary,
        manifest,
        longitudinal_bundle=longitudinal_bundle,
        semantic_summary=semantic_model,
    )
    return manifest


def _write_campaign_summary(
    output_dir: Path,
    summary: CampaignSummaryV1,
    manifest: BenchmarkCampaignManifest,
    *,
    longitudinal_bundle: tuple[list[RunSnapshot], LongitudinalAnalysis] | None = None,
    semantic_summary: CampaignSemanticSummaryV1 | None = None,
) -> None:
    from agent_llm_wiki_matrix.schema import load_schema, validate_json

    data = summary.model_dump(mode="json", exclude_none=True)
    validate_json(data, load_schema("schemas/v1/campaign_summary.schema.json"))
    write_json_sorted(output_dir / "campaign-summary.json", data)
    write_utf8_text(
        output_dir / "campaign-summary.md",
        render_campaign_summary_markdown(
            manifest,
            longitudinal_bundle=longitudinal_bundle,
            semantic_summary=semantic_summary,
        ),
    )
