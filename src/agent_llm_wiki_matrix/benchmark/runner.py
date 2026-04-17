"""Execute a benchmark definition end-to-end (responses → evals → matrices → reports)."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Literal, cast

from agent_llm_wiki_matrix.benchmark.browser_execution import (
    augment_prompt_with_browser_evidence,
    run_benchmark_browser_phase,
)
from agent_llm_wiki_matrix.benchmark.definitions import BenchmarkDefinitionV1, EvalHybridWeights
from agent_llm_wiki_matrix.benchmark.matrices import (
    grid_inputs_from_scores,
    grid_matrix_from_scores,
    pairwise_inputs_from_scores,
    pairwise_mean_delta_matrix,
)
from agent_llm_wiki_matrix.benchmark.persistence import (
    write_benchmark_manifest,
    write_pydantic_json,
    write_utf8_text,
)
from agent_llm_wiki_matrix.benchmark.prompt_resolution import (
    resolve_benchmark_prompts,
    resolve_registry_yaml_path,
)
from agent_llm_wiki_matrix.models import (
    BenchmarkCellArtifactPaths,
    BenchmarkRequestRecord,
    BenchmarkResponse,
    BenchmarkRunManifest,
    MatrixGridInputs,
    MatrixPairwiseInputs,
)
from agent_llm_wiki_matrix.pipelines.evaluate import evaluate_text, evaluation_to_json
from agent_llm_wiki_matrix.pipelines.evaluation_backends import (
    ScoringBackendName,
    evaluate_with_scoring_backend,
    judge_live_enabled,
)
from agent_llm_wiki_matrix.pipelines.reporting import (
    build_report_from_matrix,
    render_matrix_markdown,
    render_report_markdown,
)
from agent_llm_wiki_matrix.providers.base import CompletionRequest
from agent_llm_wiki_matrix.providers.benchmark_config import (
    load_judge_provider_config,
    load_provider_config_for_benchmark_variant,
)
from agent_llm_wiki_matrix.providers.execution import run_prompt_with_execution_mode
from agent_llm_wiki_matrix.providers.factory import create_provider

BackendKind = Literal["mock", "ollama", "openai_compatible"]


def _safe_segment(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", s)


def _stable_request_record_id(run_id: str, cell_id: str) -> str:
    return f"req__{_safe_segment(run_id)}__{cell_id}"


def run_benchmark(
    definition: BenchmarkDefinitionV1,
    *,
    repo_root: Path,
    output_dir: Path,
    created_at: str,
    run_id: str,
    provider_yaml: Path | None = None,
    environ: Mapping[str, str] | None = None,
    fixture_mode_force_mock: bool = True,
    prompt_registry_path: Path | None = None,
    definition_source_relpath: str | None = None,
    eval_scoring_backend: str | None = None,
    judge_provider_yaml: Path | None = None,
    judge_live: bool | None = None,
) -> BenchmarkRunManifest:
    """Run all variant × prompt cells, write artifacts under ``output_dir``."""
    env: Mapping[str, str] = os.environ if environ is None else environ
    repo_root = repo_root.resolve()
    rubric_path = (repo_root / definition.rubric_ref).resolve()
    if not rubric_path.is_file():
        msg = f"Rubric not found: {rubric_path}"
        raise FileNotFoundError(msg)

    resolved_prompts = resolve_benchmark_prompts(
        repo_root,
        definition,
        prompt_registry_path=prompt_registry_path,
    )

    prompt_registry_effective_ref: str | None = None
    if any(p.prompt_ref is not None for p in definition.prompts):
        reg_abs = resolve_registry_yaml_path(
            repo_root=repo_root,
            definition=definition,
            prompt_registry_path=prompt_registry_path,
        )
        try:
            prompt_registry_effective_ref = str(reg_abs.relative_to(repo_root))
        except ValueError:
            prompt_registry_effective_ref = str(reg_abs)

    cells_root = output_dir / "cells"
    matrices_dir = output_dir / "matrices"
    markdown_dir = output_dir / "markdown"
    reports_dir = output_dir / "reports"
    matrices_dir.mkdir(parents=True, exist_ok=True)
    markdown_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    scoring_backend = "deterministic"
    hybrid_weights: EvalHybridWeights | None = None
    judge_ref_path: Path | None = None
    if definition.eval_scoring is not None:
        scoring_backend = definition.eval_scoring.backend
        hybrid_weights = definition.eval_scoring.hybrid
        if definition.eval_scoring.judge_provider_ref:
            judge_ref_path = (repo_root / definition.eval_scoring.judge_provider_ref).resolve()
    if eval_scoring_backend is not None:
        scoring_backend = eval_scoring_backend
    if scoring_backend == "hybrid" and hybrid_weights is None:
        hybrid_weights = EvalHybridWeights(deterministic_weight=0.5, semantic_weight=0.5)

    jl = judge_live_enabled(env) if judge_live is None else judge_live
    judge_yaml_effective = (
        judge_provider_yaml if judge_provider_yaml is not None else judge_ref_path
    )
    judge_cfg = None
    if scoring_backend in ("semantic_judge", "hybrid"):
        judge_cfg = load_judge_provider_config(
            yaml_path=judge_yaml_effective or provider_yaml,
            environ=env,
            judge_live=jl,
        )

    scores: dict[tuple[str, str], float] = {}
    evaluation_relpaths: dict[tuple[str, str], str] = {}
    cell_manifest_rows: list[BenchmarkCellArtifactPaths] = []

    variant_ids = [v.id for v in definition.variants]
    prompt_ids = [p.id for p in definition.prompts]

    for variant in definition.variants:
        cfg = load_provider_config_for_benchmark_variant(
            yaml_path=provider_yaml,
            environ=env,
            backend_kind=variant.backend.kind,
            backend_model=variant.backend.model,
            fixture_mode_force_mock=fixture_mode_force_mock,
        )
        provider = create_provider(cfg)
        for prompt, resolved in zip(definition.prompts, resolved_prompts, strict=True):
            base = f"{_safe_segment(variant.id)}__{_safe_segment(prompt.id)}"
            cell_dir = cells_root / base
            cell_dir.mkdir(parents=True, exist_ok=True)
            rel_cell = Path("cells") / base

            effective_prompt = resolved.rendered_text
            browser_runner_name: str | None = None
            browser_evidence_relpath: str | None = None
            if variant.execution_mode == "browser_mock":
                br_result, block = run_benchmark_browser_phase(
                    repo_root=repo_root,
                    variant=variant,
                    prompt_id=prompt.id,
                    environ=env,
                )
                effective_prompt = augment_prompt_with_browser_evidence(
                    resolved.rendered_text,
                    runner_name=br_result.runner,
                    block=block,
                )
                browser_runner_name = br_result.runner
                write_pydantic_json(cell_dir / "browser_evidence.json", br_result.evidence)
                browser_evidence_relpath = str((rel_cell / "browser_evidence.json").as_posix())

            req = CompletionRequest(
                prompt=effective_prompt,
                model=variant.backend.model,
                temperature=None,
            )
            raw_text, normalized_text, duration_ms = run_prompt_with_execution_mode(
                provider,
                req,
                variant.execution_mode,
            )

            req_rec = BenchmarkRequestRecord(
                schema_version=1,
                id=_stable_request_record_id(run_id, base),
                run_id=run_id,
                cell_id=base,
                benchmark_id=definition.id,
                variant_id=variant.id,
                prompt_id=prompt.id,
                prompt_text=effective_prompt,
                model=variant.backend.model,
                temperature=req.temperature,
                created_at=created_at,
                prompt_source=resolved.prompt_source,
                prompt_registry_id=resolved.prompt_registry_id,
                registry_document_version=resolved.registry_document_version,
                prompt_source_relpath=resolved.prompt_source_relpath,
                browser_runner=browser_runner_name,
                browser_evidence_relpath=browser_evidence_relpath,
            )
            write_pydantic_json(cell_dir / "request.json", req_rec)
            write_utf8_text(cell_dir / "response.raw.txt", raw_text)
            write_utf8_text(cell_dir / "response.normalized.txt", normalized_text)

            resp_id = f"resp-{_safe_segment(variant.id)}-{_safe_segment(prompt.id)}"
            br = BenchmarkResponse(
                schema_version=1,
                id=resp_id,
                benchmark_id=definition.id,
                variant_id=variant.id,
                prompt_id=prompt.id,
                agent_stack=variant.agent_stack,
                execution_mode=variant.execution_mode,
                backend_kind=cast(BackendKind, cfg.kind),
                backend_model=variant.backend.model,
                prompt_text=effective_prompt,
                response_text=normalized_text,
                duration_ms=duration_ms,
                created_at=created_at,
                prompt_source=resolved.prompt_source,
                prompt_registry_id=resolved.prompt_registry_id,
                registry_document_version=resolved.registry_document_version,
                prompt_source_relpath=resolved.prompt_source_relpath,
                browser_runner=browser_runner_name,
                browser_evidence_relpath=browser_evidence_relpath,
            )
            aggregate_path = cell_dir / "benchmark_response.json"
            write_pydantic_json(aggregate_path, br)

            aggregate_relpath = str((rel_cell / "benchmark_response.json").as_posix())
            norm_txt = rel_cell / "response.normalized.txt"
            eval_id = f"eval-{_safe_segment(variant.id)}-{_safe_segment(prompt.id)}"
            rel_eval = rel_cell / "evaluation.json"
            evaluation_json_relpath = str(rel_eval.as_posix())
            judge_provenance_cell_relpath: str | None = None

            if scoring_backend == "deterministic":
                ev = evaluate_text(
                    subject_ref=aggregate_relpath,
                    text=normalized_text,
                    rubric_path=rubric_path,
                    evaluation_id=eval_id,
                    evaluated_at=created_at,
                    notes_markdown=(
                        "Benchmark cell evaluation (rubric hash on normalized response)."
                    ),
                )
            else:
                ev, prov = evaluate_with_scoring_backend(
                    subject_ref=aggregate_relpath,
                    text=normalized_text,
                    rubric_path=rubric_path,
                    evaluation_id=eval_id,
                    evaluated_at=created_at,
                    scoring_backend=cast(ScoringBackendName, scoring_backend),
                    hybrid_weights=hybrid_weights,
                    judge_provider_cfg=judge_cfg,
                    judge_live=jl,
                    evaluation_json_relpath=evaluation_json_relpath,
                )
                jp = rel_cell / "evaluation_judge_provenance.json"
                judge_provenance_cell_relpath = str(jp.as_posix())
                write_pydantic_json(output_dir / jp, prov)
                ev = ev.model_copy(
                    update={
                        "notes_markdown": (
                            "Benchmark cell evaluation (see evaluation_judge_provenance.json)."
                        ),
                        "judge_provenance_relpath": judge_provenance_cell_relpath,
                    },
                )

            eval_path = output_dir / rel_eval
            eval_path.write_text(evaluation_to_json(ev), encoding="utf-8")
            scores[(variant.id, prompt.id)] = ev.total_weighted_score
            evaluation_relpaths[(variant.id, prompt.id)] = str(rel_eval.as_posix())

            cell_manifest_rows.append(
                BenchmarkCellArtifactPaths(
                    cell_id=base,
                    request_relpath=str((rel_cell / "request.json").as_posix()),
                    raw_response_relpath=str((rel_cell / "response.raw.txt").as_posix()),
                    normalized_response_relpath=str(norm_txt.as_posix()),
                    aggregate_response_relpath=aggregate_relpath,
                    evaluation_relpath=str(rel_eval.as_posix()),
                    browser_evidence_relpath=browser_evidence_relpath,
                    judge_provenance_relpath=judge_provenance_cell_relpath,
                )
            )

    cell_manifest_rows.sort(key=lambda c: c.cell_id)

    grid_mid = f"{run_id}-grid"
    pairwise_mid = f"{run_id}-pairwise"
    metric_grid = "total_weighted_rubric_score"
    metric_pw = "mean_abs_total_score_delta"

    grid = grid_matrix_from_scores(
        matrix_id=grid_mid,
        title=f"{definition.title} (per-prompt scores)",
        row_labels=variant_ids,
        col_labels=prompt_ids,
        scores=scores,
        metric=metric_grid,
        created_at=created_at,
    )
    pairwise = pairwise_mean_delta_matrix(
        matrix_id=pairwise_mid,
        title=f"{definition.title} (mean abs score delta across prompts)",
        variant_ids=variant_ids,
        prompt_ids=prompt_ids,
        scores=scores,
        metric=metric_pw,
        created_at=created_at,
    )

    grid_inputs: MatrixGridInputs = grid_inputs_from_scores(
        run_id=run_id,
        benchmark_id=definition.id,
        matrix_id=grid_mid,
        metric=metric_grid,
        created_at=created_at,
        row_labels=variant_ids,
        col_labels=prompt_ids,
        scores=scores,
        evaluation_relpaths=evaluation_relpaths,
    )
    pairwise_inputs: MatrixPairwiseInputs = pairwise_inputs_from_scores(
        run_id=run_id,
        benchmark_id=definition.id,
        matrix_id=pairwise_mid,
        metric=metric_pw,
        created_at=created_at,
        variant_ids=variant_ids,
        prompt_ids=prompt_ids,
        scores=scores,
    )

    grid_path = matrices_dir / "grid.json"
    pairwise_path = matrices_dir / "pairwise.json"
    grid_inputs_path = matrices_dir / "grid.row_inputs.json"
    pairwise_inputs_path = matrices_dir / "pairwise.row_inputs.json"
    grid_md_path = markdown_dir / "matrix.grid.md"
    pairwise_md_path = markdown_dir / "matrix.pairwise.md"
    report_json_path = reports_dir / "report.json"
    report_md_path = reports_dir / "report.md"

    write_pydantic_json(grid_path, grid)
    write_pydantic_json(pairwise_path, pairwise)
    write_pydantic_json(grid_inputs_path, grid_inputs)
    write_pydantic_json(pairwise_inputs_path, pairwise_inputs)
    grid_md_path.write_text(render_matrix_markdown(grid), encoding="utf-8")
    pairwise_md_path.write_text(render_matrix_markdown(pairwise), encoding="utf-8")

    report = build_report_from_matrix(
        grid,
        report_id=f"{run_id}-report",
        period_start=created_at[:10] if len(created_at) >= 10 else created_at,
        period_end=created_at[:10] if len(created_at) >= 10 else created_at,
        kind="model_comparison",
    )
    write_pydantic_json(report_json_path, report)
    report_md_path.write_text(render_report_markdown(report), encoding="utf-8")

    manifest = BenchmarkRunManifest(
        schema_version=1,
        run_id=run_id,
        benchmark_id=definition.id,
        title=definition.title,
        rubric_ref=definition.rubric_ref,
        created_at=created_at,
        variant_ids=variant_ids,
        prompt_ids=prompt_ids,
        definition_source_relpath=definition_source_relpath,
        prompt_registry_effective_ref=prompt_registry_effective_ref,
        cells=cell_manifest_rows,
        matrix_grid_path="matrices/grid.json",
        matrix_pairwise_path="matrices/pairwise.json",
        matrix_grid_row_inputs_path="matrices/grid.row_inputs.json",
        matrix_pairwise_row_inputs_path="matrices/pairwise.row_inputs.json",
        report_json_path="reports/report.json",
        report_md_path="reports/report.md",
        matrix_grid_md_path="markdown/matrix.grid.md",
        matrix_pairwise_md_path="markdown/matrix.pairwise.md",
        taxonomy=definition.taxonomy,
        time_budget_seconds=definition.time_budget_seconds,
        token_budget=definition.token_budget,
        retry_policy=definition.retry_policy,
        tags=definition.tags,
        expected_artifact_kinds=definition.expected_artifact_kinds,
    )
    write_benchmark_manifest(output_dir / "manifest.json", manifest)
    return manifest
