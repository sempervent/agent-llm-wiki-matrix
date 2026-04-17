"""Run manifest (JSON) written alongside benchmark artifacts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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
    response_paths: list[str] = Field(description="Paths relative to output directory")
    evaluation_paths: list[str]
    matrix_grid_path: str
    matrix_pairwise_path: str
    report_json_path: str
    report_md_path: str
    matrix_grid_md_path: str
    matrix_pairwise_md_path: str
