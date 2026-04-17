"""Run manifest (JSON) written alongside benchmark artifacts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BenchmarkCellArtifactPaths(BaseModel):
    """Relative paths for one variant × prompt cell (sorted by cell_id in the manifest)."""

    model_config = ConfigDict(extra="forbid")

    cell_id: str = Field(description="Stable slug: safe(variant)__safe(prompt)")
    request_relpath: str
    raw_response_relpath: str
    normalized_response_relpath: str
    aggregate_response_relpath: str
    evaluation_relpath: str


class BenchmarkRunManifest(BaseModel):
    """Summary of a benchmark run output directory."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    run_id: str = Field(min_length=1)
    benchmark_id: str = Field(min_length=1)
    title: str
    rubric_ref: str
    created_at: str
    variant_ids: list[str]
    prompt_ids: list[str]
    cells: list[BenchmarkCellArtifactPaths] = Field(
        description="Per-cell artifact paths (lexicographically sorted by cell_id)",
    )
    matrix_grid_path: str
    matrix_pairwise_path: str
    matrix_grid_row_inputs_path: str
    matrix_pairwise_row_inputs_path: str
    report_json_path: str
    report_md_path: str
    matrix_grid_md_path: str
    matrix_pairwise_md_path: str
