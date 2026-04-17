"""Execute a benchmark definition end-to-end (responses → evals → matrices → reports)."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Literal, cast

from agent_llm_wiki_matrix.benchmark.definitions import BenchmarkDefinitionV1
from agent_llm_wiki_matrix.benchmark.manifest import BenchmarkRunManifest
from agent_llm_wiki_matrix.benchmark.matrices import (
    grid_matrix_from_scores,
    pairwise_mean_delta_matrix,
)
from agent_llm_wiki_matrix.models import BenchmarkResponse
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
) -> BenchmarkRunManifest:
    """Run all variant × prompt cells, write artifacts under ``output_dir``."""
    env: Mapping[str, str] = os.environ if environ is None else environ
    rubric_path = (repo_root / definition.rubric_ref).resolve()
    if not rubric_path.is_file():
        msg = f"Rubric not found: {rubric_path}"
        raise FileNotFoundError(msg)

    responses_dir = output_dir / "responses"
    evals_dir = output_dir / "evaluations"
    responses_dir.mkdir(parents=True, exist_ok=True)
    evals_dir.mkdir(parents=True, exist_ok=True)

    response_paths: list[str] = []
    evaluation_paths: list[str] = []
    scores: dict[tuple[str, str], float] = {}

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
        for prompt in definition.prompts:
            req = CompletionRequest(prompt=prompt.text, model=variant.backend.model)
            text, duration_ms = run_prompt_with_execution_mode(
                provider,
                req,
                variant.execution_mode,
            )
            resp_id = f"resp-{_safe_segment(variant.id)}-{_safe_segment(prompt.id)}"
            base = f"{_safe_segment(variant.id)}__{_safe_segment(prompt.id)}"
            rel_response = Path("responses") / f"{base}.response.json"
            out_response = output_dir / rel_response
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
                prompt_text=prompt.text,
                response_text=text,
                duration_ms=duration_ms,
                created_at=created_at,
            )
            out_response.write_text(
                json.dumps(br.model_dump(), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            response_paths.append(str(rel_response.as_posix()))

            subject_ref = str(rel_response.as_posix())
            eval_id = f"eval-{_safe_segment(variant.id)}-{_safe_segment(prompt.id)}"
            ev = evaluate_text(
                subject_ref=subject_ref,
                text=text,
                rubric_path=rubric_path,
                evaluation_id=eval_id,
                evaluated_at=created_at,
                notes_markdown="Benchmark cell evaluation (rubric hash on response text).",
            )
            rel_eval = Path("evaluations") / f"{base}.eval.json"
            out_eval = output_dir / rel_eval
            out_eval.write_text(evaluation_to_json(ev), encoding="utf-8")
            evaluation_paths.append(str(rel_eval.as_posix()))
            scores[(variant.id, prompt.id)] = ev.total_weighted_score

    grid = grid_matrix_from_scores(
        matrix_id=f"{run_id}-grid",
        title=f"{definition.title} (per-prompt scores)",
        row_labels=variant_ids,
        col_labels=prompt_ids,
        scores=scores,
        metric="total_weighted_rubric_score",
        created_at=created_at,
    )
    pairwise = pairwise_mean_delta_matrix(
        matrix_id=f"{run_id}-pairwise",
        title=f"{definition.title} (mean abs score delta across prompts)",
        variant_ids=variant_ids,
        prompt_ids=prompt_ids,
        scores=scores,
        metric="mean_abs_total_score_delta",
        created_at=created_at,
    )

    grid_path = output_dir / "matrix.grid.json"
    pairwise_path = output_dir / "matrix.pairwise.json"
    grid_md_path = output_dir / "matrix.grid.md"
    pairwise_md_path = output_dir / "matrix.pairwise.md"
    report_json_path = output_dir / "report.json"
    report_md_path = output_dir / "report.md"

    grid_path.write_text(grid.model_dump_json(indent=2, exclude_none=True) + "\n", encoding="utf-8")
    pairwise_path.write_text(
        pairwise.model_dump_json(indent=2, exclude_none=True) + "\n",
        encoding="utf-8",
    )
    grid_md_path.write_text(render_matrix_markdown(grid), encoding="utf-8")
    pairwise_md_path.write_text(render_matrix_markdown(pairwise), encoding="utf-8")

    report = build_report_from_matrix(
        grid,
        report_id=f"{run_id}-report",
        period_start=created_at[:10] if len(created_at) >= 10 else created_at,
        period_end=created_at[:10] if len(created_at) >= 10 else created_at,
        kind="model_comparison",
    )
    report_json_path.write_text(
        report.model_dump_json(indent=2, exclude_none=True) + "\n",
        encoding="utf-8",
    )
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
        response_paths=response_paths,
        evaluation_paths=evaluation_paths,
        matrix_grid_path="matrix.grid.json",
        matrix_pairwise_path="matrix.pairwise.json",
        report_json_path="report.json",
        report_md_path="report.md",
        matrix_grid_md_path="matrix.grid.md",
        matrix_pairwise_md_path="matrix.pairwise.md",
    )
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest.model_dump(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest
