"""Execute a benchmark definition end-to-end (responses → evals → matrices → reports)."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Literal, cast

from agent_llm_wiki_matrix.benchmark.definitions import BenchmarkDefinitionV1
from agent_llm_wiki_matrix.benchmark.manifest import (
    BenchmarkCellArtifactPaths,
    BenchmarkRunManifest,
)
from agent_llm_wiki_matrix.benchmark.matrices import (
    grid_inputs_from_scores,
    grid_matrix_from_scores,
    pairwise_inputs_from_scores,
    pairwise_mean_delta_matrix,
)
from agent_llm_wiki_matrix.benchmark.persistence import write_pydantic_json, write_utf8_text
from agent_llm_wiki_matrix.benchmark.prompt_resolution import resolve_benchmark_prompts
from agent_llm_wiki_matrix.models import (
    BenchmarkRequestRecord,
    BenchmarkResponse,
    MatrixGridInputs,
    MatrixPairwiseInputs,
)
from agent_llm_wiki_matrix.pipelines.evaluate import evaluate_text, evaluation_to_json
from agent_llm_wiki_matrix.pipelines.reporting import (
    build_report_from_matrix,
    render_matrix_markdown,
    render_report_markdown,
)
from agent_llm_wiki_matrix.providers.base import CompletionRequest
from agent_llm_wiki_matrix.providers.benchmark_config import (
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

    cells_root = output_dir / "cells"
    matrices_dir = output_dir / "matrices"
    markdown_dir = output_dir / "markdown"
    reports_dir = output_dir / "reports"
    matrices_dir.mkdir(parents=True, exist_ok=True)
    markdown_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

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

            req = CompletionRequest(
                prompt=resolved.rendered_text,
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
                prompt_text=resolved.rendered_text,
                model=variant.backend.model,
                temperature=req.temperature,
                created_at=created_at,
                prompt_source=resolved.prompt_source,
                prompt_registry_id=resolved.prompt_registry_id,
                registry_document_version=resolved.registry_document_version,
                prompt_source_relpath=resolved.prompt_source_relpath,
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
                prompt_text=resolved.rendered_text,
                response_text=normalized_text,
                duration_ms=duration_ms,
                created_at=created_at,
                prompt_source=resolved.prompt_source,
                prompt_registry_id=resolved.prompt_registry_id,
                registry_document_version=resolved.registry_document_version,
                prompt_source_relpath=resolved.prompt_source_relpath,
            )
            aggregate_path = cell_dir / "benchmark_response.json"
            write_pydantic_json(aggregate_path, br)

            rel_cell = Path("cells") / base
            norm_txt = rel_cell / "response.normalized.txt"
            aggregate_relpath = str((rel_cell / "benchmark_response.json").as_posix())
            eval_id = f"eval-{_safe_segment(variant.id)}-{_safe_segment(prompt.id)}"
            ev = evaluate_text(
                subject_ref=aggregate_relpath,
                text=normalized_text,
                rubric_path=rubric_path,
                evaluation_id=eval_id,
                evaluated_at=created_at,
                notes_markdown="Benchmark cell evaluation (rubric hash on normalized response).",
            )
            rel_eval = rel_cell / "evaluation.json"
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
        cells=cell_manifest_rows,
        matrix_grid_path="matrices/grid.json",
        matrix_pairwise_path="matrices/pairwise.json",
        matrix_grid_row_inputs_path="matrices/grid.row_inputs.json",
        matrix_pairwise_row_inputs_path="matrices/pairwise.row_inputs.json",
        report_json_path="reports/report.json",
        report_md_path="reports/report.md",
        matrix_grid_md_path="markdown/matrix.grid.md",
        matrix_pairwise_md_path="markdown/matrix.pairwise.md",
    )
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest.model_dump(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest
