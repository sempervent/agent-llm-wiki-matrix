"""Assemble a campaign result pack (publishable slice of a campaign output directory)."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from agent_llm_wiki_matrix.artifacts import load_artifact_file
from agent_llm_wiki_matrix.benchmark.fingerprints import sha256_canonical
from agent_llm_wiki_matrix.benchmark.persistence import write_json_sorted, write_utf8_text
from agent_llm_wiki_matrix.models import (
    BenchmarkCampaignManifest,
    CampaignResultPackArtifacts,
    CampaignResultPackMemberRun,
    CampaignResultPackV1,
)
from agent_llm_wiki_matrix.schema import load_schema, validate_json


def _utc_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _alwm_package_version() -> str | None:
    try:
        from importlib.metadata import version

        return version("agent-llm-wiki-matrix")
    except Exception:
        return None


def pack_identity_payload(pack: CampaignResultPackV1) -> dict[str, Any]:
    """Canonical JSON-serializable payload for :func:`compute_pack_identity_fingerprint`.

    Excludes volatile or display-only fields (pack assembly time, ``pack_id``, notes,
    absolute paths, tool version, and the fingerprint field itself).
    """
    cef = pack.campaign_experiment_fingerprints
    artifacts = pack.artifacts.model_dump(mode="json", exclude_none=True)
    members = sorted(
        (m.model_dump(mode="json") for m in pack.member_runs),
        key=lambda row: row["run_index"],
    )
    return {
        "campaign_id": pack.campaign_id,
        "campaign_created_at": pack.campaign_created_at,
        "definition_source_relpath": pack.definition_source_relpath,
        "fixture_mode_force_mock": pack.fixture_mode_force_mock,
        "member_depth": pack.member_depth,
        "longitudinal_member_glob": pack.longitudinal_member_glob,
        "artifacts": artifacts,
        "member_runs": members,
        "campaign_definition_fingerprint": pack.campaign_definition_fingerprint,
        "campaign_experiment_fingerprints": (
            cef.model_dump(mode="json") if cef is not None else None
        ),
        "git_commit_sha": pack.git_commit_sha,
        "git_describe": pack.git_describe,
        "source_campaign_relpath": pack.source_campaign_relpath,
        "campaign_run_count": pack.campaign_run_count,
        "included_member_count": pack.included_member_count,
    }


def compute_pack_identity_fingerprint(pack: CampaignResultPackV1) -> str:
    """Stable fingerprint for comparing whether two packs bundle the same logical experiment."""
    return sha256_canonical(pack_identity_payload(pack))


MembershipScope = Literal["all_runs", "subset", "unknown"]


def derive_pack_publication_hints(
    pack: CampaignResultPackV1,
) -> tuple[MembershipScope, list[str]]:
    """Derive membership scope and optional layer ids (not part of pack fingerprint)."""
    art = pack.artifacts
    layers: list[str] = []
    if art.campaign_semantic_summary_json:
        layers.append("semantic_summary")
    if art.campaign_comparative_report_md:
        layers.append("comparative_report")
    if art.campaign_analysis_json:
        layers.append("comparative_analysis")
    if art.campaign_dry_run_json:
        layers.append("dry_run_plan")
    layers.sort()

    crc = pack.campaign_run_count
    imc = pack.included_member_count
    if crc is None or imc is None:
        return "unknown", layers
    if crc > 0 and imc < crc:
        return "subset", layers
    if crc > 0 and imc == crc:
        return "all_runs", layers
    return "unknown", layers


def _effective_publication_hints(
    pack: CampaignResultPackV1,
) -> tuple[MembershipScope, list[str]]:
    """Use stored fields when present; otherwise derive (legacy packs)."""
    scope, layers = derive_pack_publication_hints(pack)
    if pack.membership_scope is not None:
        scope = pack.membership_scope
    if pack.optional_layers_present is not None:
        layers = list(pack.optional_layers_present)
    return scope, layers


@dataclass
class CampaignPackValidationResult:
    """Result of :func:`validate_campaign_result_pack_directory`."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def ok(self, *, strict_portability: bool) -> bool:
        return not self.errors and not (strict_portability and bool(self.warnings))


def validate_campaign_result_pack_directory(
    pack_dir: Path,
    *,
    strict_portability: bool = False,
) -> CampaignPackValidationResult:
    """Check schema, required files, artifact paths, and optional portability rules.

    Loads JSON artifacts with registered kinds. ``strict_portability`` turns portability
    warnings into errors (for CI gates on publishable bundles).
    """
    out = CampaignPackValidationResult()
    root = pack_dir.resolve()
    pack_json = root / "campaign-result-pack.json"
    if not pack_json.is_file():
        out.errors.append(f"missing pack manifest: {pack_json}")
        return out

    try:
        raw_pack = json.loads(pack_json.read_text(encoding="utf-8"))
        pack = CampaignResultPackV1.model_validate(raw_pack)
    except Exception as e:
        out.errors.append(f"invalid campaign-result-pack.json: {e}")
        return out

    try:
        load_artifact_file(pack_json, "campaign_result_pack")
    except Exception as e:
        out.errors.append(f"campaign_result_pack schema/kind validation failed: {e}")

    idx_path = root / pack.artifacts.index_md
    if not idx_path.is_file():
        out.errors.append(f"missing INDEX: {idx_path}")

    art = pack.artifacts

    def _need(rel: str | None, label: str) -> None:
        if rel is None:
            return
        p = root / rel
        if not p.is_file():
            out.errors.append(f"missing {label}: {p}")

    _need(art.campaign_manifest, "campaign manifest")
    _need(art.campaign_summary_json, "campaign summary JSON")
    _need(art.campaign_summary_md, "campaign summary Markdown")
    _need(art.campaign_semantic_summary_json, "campaign semantic summary JSON")
    _need(art.campaign_semantic_summary_md, "campaign semantic summary Markdown")
    _need(art.campaign_comparative_report_md, "comparative report")
    _need(art.campaign_analysis_json, "comparative analysis JSON")
    _need(art.campaign_dry_run_json, "campaign dry-run JSON")
    _need(art.campaign_result_pack_json, "pack manifest (self)")
    _need(art.index_md, "INDEX.md")

    for m in pack.member_runs:
        mp = root / m.manifest_relpath
        if not mp.is_file():
            out.errors.append(f"missing member manifest: {mp}")

    if not out.errors:
        try:
            cm_path = root / art.campaign_manifest
            cm = load_artifact_file(cm_path, "campaign_manifest")
            if getattr(cm, "campaign_id", None) != pack.campaign_id:
                out.errors.append(
                    "campaign_id mismatch between campaign-result-pack.json and manifest.json",
                )
        except Exception as e:
            out.errors.append(f"campaign manifest load: {e}")

        try:
            cs_path = root / art.campaign_summary_json
            cs = load_artifact_file(cs_path, "campaign_summary")
            if getattr(cs, "campaign_id", None) != pack.campaign_id:
                out.errors.append(
                    "campaign_id mismatch between campaign-result-pack.json and "
                    "campaign-summary.json",
                )
        except Exception as e:
            out.errors.append(f"campaign summary load: {e}")

    if pack.source_campaign_dir:
        out.warnings.append(
            "source_campaign_dir is set (absolute path); omit --record-source-abspath "
            "for portable packs",
        )
    if pack.member_depth == "manifest":
        out.warnings.append(
            "member_depth is manifest-only; longitudinal tooling may not load per-cell evaluations",
        )
    if pack.included_member_count is not None and pack.included_member_count == 0:
        out.errors.append("pack includes zero member runs")

    if strict_portability:
        for w in list(out.warnings):
            out.errors.append(f"portability: {w}")
        out.warnings.clear()

    return out


def _copy_if_exists(src: Path, dst: Path) -> bool:
    if not src.is_file():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def _copy_tree_if_exists(src: Path, dst: Path) -> bool:
    if not src.is_dir():
        return False
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    return True


def assemble_campaign_result_pack(
    *,
    campaign_dir: Path,
    pack_dir: Path,
    pack_id: str,
    title: str | None = None,
    created_at: str | None = None,
    run_indices: set[int] | None = None,
    member_depth: Literal["full", "manifest"] = "full",
    source_campaign_relpath: str | None = None,
    notes: str | None = None,
    only_succeeded_members: bool = True,
    record_source_abspath: bool = False,
) -> CampaignResultPackV1:
    """Copy campaign artifacts and selected member runs into ``pack_dir``; write pack + INDEX.

    Layout matches a normal campaign output tree (``manifest.json`` at pack root,
    ``runs/runNNNN/``, …) so tooling and globs stay familiar.
    **member_depth=full** copies full per-run trees (required for
    ``alwm benchmark longitudinal`` to load evaluations).
    **manifest** copies only ``manifest.json`` per run (smaller; longitudinal cell loads may fail).
    """
    campaign_dir = campaign_dir.resolve()
    pack_dir = pack_dir.resolve()
    pack_dir.mkdir(parents=True, exist_ok=True)

    cm_path = campaign_dir / "manifest.json"
    if not cm_path.is_file():
        msg = f"Campaign manifest not found: {cm_path}"
        raise FileNotFoundError(msg)
    raw = json.loads(cm_path.read_text(encoding="utf-8"))
    cm = BenchmarkCampaignManifest.model_validate(raw)

    ts = created_at or _utc_iso()
    pack_title = title or cm.title

    # Copy campaign-level artifacts (same layout as source).
    for name in (
        "manifest.json",
        "campaign-summary.json",
        "campaign-summary.md",
        "campaign-semantic-summary.json",
        "campaign-semantic-summary.md",
        "campaign-dry-run.json",
    ):
        _copy_if_exists(campaign_dir / name, pack_dir / name)

    semantic_json = pack_dir / "campaign-semantic-summary.json"
    has_semantic = semantic_json.is_file()
    comp_md = campaign_dir / "reports" / "campaign-report.md"
    has_comp = comp_md.is_file()
    analysis_json = campaign_dir / "reports" / "campaign-analysis.json"
    has_analysis = analysis_json.is_file()
    dry_json = pack_dir / "campaign-dry-run.json"
    has_dry_run = dry_json.is_file()

    if has_comp or has_analysis:
        (pack_dir / "reports").mkdir(parents=True, exist_ok=True)
        _copy_if_exists(comp_md, pack_dir / "reports" / "campaign-report.md")
        _copy_if_exists(analysis_json, pack_dir / "reports" / "campaign-analysis.json")

    member_runs: list[CampaignResultPackMemberRun] = []
    runs_root = campaign_dir / "runs"
    if runs_root.is_dir():
        for row in cm.runs:
            if only_succeeded_members and row.status != "succeeded":
                continue
            if run_indices is not None and row.run_index not in run_indices:
                continue
            rel = row.output_relpath
            src_run = campaign_dir / rel
            dst_run = pack_dir / rel
            if member_depth == "full":
                if not src_run.is_dir():
                    continue
                _copy_tree_if_exists(src_run, dst_run)
            else:
                manifest_only = src_run / "manifest.json"
                if manifest_only.is_file():
                    dst_run.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(manifest_only, dst_run / "manifest.json")
                else:
                    continue
            member_runs.append(
                CampaignResultPackMemberRun(
                    run_id=row.run_id,
                    run_index=row.run_index,
                    status=row.status,
                    manifest_relpath=f"{rel}/manifest.json",
                    suite_ref=row.suite_ref,
                    benchmark_id=row.benchmark_id,
                ),
            )

    member_runs.sort(key=lambda x: x.run_index)

    artifacts = CampaignResultPackArtifacts(
        campaign_manifest="manifest.json",
        campaign_summary_json="campaign-summary.json",
        campaign_summary_md="campaign-summary.md",
        campaign_semantic_summary_json="campaign-semantic-summary.json" if has_semantic else None,
        campaign_semantic_summary_md="campaign-semantic-summary.md" if has_semantic else None,
        campaign_comparative_report_md="reports/campaign-report.md" if has_comp else None,
        campaign_analysis_json="reports/campaign-analysis.json" if has_analysis else None,
        campaign_dry_run_json="campaign-dry-run.json" if has_dry_run else None,
        campaign_result_pack_json="campaign-result-pack.json",
        index_md="INDEX.md",
    )

    pack = CampaignResultPackV1(
        schema_version=1,
        layout_version=1,
        pack_id=pack_id,
        created_at=ts,
        source_campaign_relpath=source_campaign_relpath,
        campaign_id=cm.campaign_id,
        title=pack_title,
        campaign_created_at=cm.created_at,
        definition_source_relpath=cm.definition_source_relpath,
        fixture_mode_force_mock=cm.fixture_mode_force_mock,
        campaign_run_count=len(cm.runs),
        included_member_count=len(member_runs),
        alwm_version=_alwm_package_version(),
        campaign_definition_fingerprint=cm.campaign_definition_fingerprint,
        campaign_experiment_fingerprints=cm.campaign_experiment_fingerprints,
        git_commit_sha=cm.git_commit_sha,
        git_describe=cm.git_describe,
        source_campaign_dir=str(campaign_dir) if record_source_abspath else None,
        member_depth=member_depth,
        longitudinal_member_glob="runs/*/manifest.json",
        artifacts=artifacts,
        member_runs=member_runs,
        notes=notes,
    )
    pack = pack.model_copy(
        update={"pack_identity_fingerprint": compute_pack_identity_fingerprint(pack)},
    )
    ms, ol = derive_pack_publication_hints(pack)
    pack = pack.model_copy(
        update={"membership_scope": ms, "optional_layers_present": ol},
    )

    data = pack.model_dump(mode="json", exclude_none=True)
    validate_json(data, load_schema("schemas/v1/campaign_result_pack.schema.json"))
    write_json_sorted(pack_dir / "campaign-result-pack.json", data)

    write_utf8_text(pack_dir / "INDEX.md", _render_pack_index_md(pack))

    return pack


_LAYER_BLURBS: dict[str, str] = {
    "semantic_summary": "`campaign-semantic-summary.{json,md}` — hybrid / judge rollups",
    "comparative_report": "`reports/campaign-report.md` — narrative + fingerprint interpretation",
    "comparative_analysis": "`reports/campaign-analysis.json` — structured analysis mirror "
    "(not an `alwm validate` kind)",
    "dry_run_plan": "`campaign-dry-run.json` — plan-only campaign (no executed member trees)",
}


def _render_pack_index_md(pack: CampaignResultPackV1) -> str:
    """Markdown overview for manual inspection and publishing."""
    art = pack.artifacts
    scope, opt_layers = _effective_publication_hints(pack)
    crc = pack.campaign_run_count
    imc = pack.included_member_count
    subset = (
        crc is not None
        and imc is not None
        and imc < crc
    )

    lines = [
        f"# Campaign result pack: `{pack.pack_id}`",
        "",
        f"**campaign_id:** `{pack.campaign_id}` · **title:** {pack.title}",
        "",
        "## For reviewers (read this first)",
        "",
        (
            "**What this is:** A **frozen, portable slice** of a finished campaign—the same "
            "directory layout as a harness output tree, plus **`campaign-result-pack.json`** "
            f"(machine index) and this **`{art.index_md}`**. Use it to **review, cite, archive, "
            "or attach** results — preferred handoff, not only the raw campaign folder."
        ),
        "",
        "**Suggested reading order** (about 10–20 minutes for a typical pack):",
        "",
        "1. **`campaign-summary.md`** — Rollups, sweep overview, headline scores.",
        "2. **`reports/campaign-report.md`** — When present: narrative comparative report and "
        "fingerprint-axis interpretation.",
        "3. **`campaign-semantic-summary.md`** — When present: hybrid / judge instability and "
        "confidence rollups.",
        "4. **`reports/campaign-analysis.json`** — When present: machine-readable analysis mirror.",
        "5. **`runs/runNNNN/`** — Per-run manifests, cells, matrices, and reports.",
        "",
        (
            f"**Machine index:** `{art.campaign_result_pack_json}` records "
            "`pack_identity_fingerprint`, member inventory, optional layer paths, and "
            "`membership_scope` / `optional_layers_present` when emitted by this tool version."
        ),
        "",
        "## Scope of this bundle",
        "",
        "| | |",
        "| --- | --- |",
    ]
    if pack.member_depth == "full":
        mdepth_cell = (
            "`full` — full per-run trees (default; needed for longitudinal cell loads)."
        )
    else:
        mdepth_cell = (
            "`manifest` — only `manifest.json` per member (smaller; evaluations may not load)."
        )
    lines.append(f"| **member_depth** | {mdepth_cell} |")
    if crc is not None and imc is not None:
        lines.append(
            f"| **Member runs** | **{imc}** copied **of {crc}** campaign manifest row(s) · "
            f"`membership_scope`: **`{scope}`** |",
        )
    else:
        lines.append("| **Member runs** | See **`Member runs included`** below. |")
    lines.extend(
        [
            f"| **Pack assembled** | `{pack.created_at}` |",
            "",
        ],
    )
    if pack.campaign_created_at:
        lines.append(f"- **Campaign manifest timestamp:** `{pack.campaign_created_at}`")
    if pack.definition_source_relpath:
        lines.append(f"- **Campaign definition:** `{pack.definition_source_relpath}`")
    if pack.fixture_mode_force_mock is not None:
        lines.append(
            f"- **Fixture mode (forced mock):** `{str(pack.fixture_mode_force_mock).lower()}`",
        )
    if pack.pack_identity_fingerprint:
        lines.append(f"- **pack_identity_fingerprint:** `{pack.pack_identity_fingerprint}`")
    if pack.alwm_version:
        lines.append(f"- **alwm_version (assembler):** `{pack.alwm_version}`")
    lines.append("")

    if scope == "all_runs":
        lines.append(
            "_Every campaign manifest member row is represented in this pack "
            "(`included_member_count` equals `campaign_run_count`)._",
        )
    elif scope == "subset":
        lines.append(
            "> **Subset:** Fewer member runs than the campaign manifest lists—filters, "
            "`--run-index`, excluding failed members, or other selection. See **Member runs "
            "included** and **Notes** (if any).",
        )
    else:
        lines.append(
            "_Membership scope is **unknown** from counts alone; compare `campaign_run_count` "
            "and `included_member_count` in `campaign-result-pack.json`._",
        )
    lines.append("")

    if subset and pack.notes is None:
        lines.append(
            "_Tip: add `--notes \"…\"` when assembling a subset pack so reviewers know why runs "
            "were omitted._",
        )
        lines.append("")

    lines.extend(
        [
            "## What is included",
            "",
            "**Core (always in a pack):** `manifest.json`, `campaign-summary.json`, "
            "`campaign-summary.md`, `campaign-result-pack.json`, this index, and the member run "
            "trees listed under **Member runs included** (or manifest stubs when "
            "`member_depth` is `manifest`).",
            "",
            "**Optional layers in this directory:**",
            "",
        ],
    )
    if opt_layers:
        for key in sorted(opt_layers):
            lines.append(f"- {_LAYER_BLURBS.get(key, key)}")
    else:
        lines.append(
            "_None beyond core summaries and members (no semantic, comparative report, analysis "
            "JSON, or dry-run plan in this bundle)._",
        )
    lines.extend(["", "## Publication workflow", ""])

    lines.extend(
        [
            "1. **Validate** — `alwm validate` on the pack manifest and key kinds; "
            "`alwm benchmark campaign pack-check .` for on-disk consistency.",
            "2. **Compare** (optional) — `alwm benchmark campaign compare-packs` vs another pack.",
            "3. **Publish** — commit, archive, or attach this directory.",
            "",
            "Full operator checklist: **`docs/workflows/campaign-result-pack-publication.md`** "
            "(in the repository).",
            "",
            "## Publish-ready checklist",
            "",
            "- [ ] `alwm validate campaign-result-pack.json campaign_result_pack`",
            "- [ ] `alwm validate manifest.json campaign_manifest`",
            "- [ ] `alwm validate campaign-summary.json campaign_summary`",
            "- [ ] `alwm benchmark campaign pack-check .` (`--strict` if warnings must fail CI)",
            "- [ ] **Optional layers:** validate semantic JSON when present "
            "(`alwm validate campaign-semantic-summary.json campaign_semantic_summary`)",
            "- [ ] **Portability:** no accidental `source_campaign_dir` unless intended",
            "- [ ] **Subset:** if filtered, **`notes`** or cover text explains omissions",
            "- [ ] **Secrets:** spot-check `cells/`, `request.json`, `browser_evidence.json`",
            "",
            "## Provenance",
            "",
        ],
    )
    if pack.source_campaign_dir:
        lines.append(f"- **Source directory:** `{pack.source_campaign_dir}`")
    if pack.source_campaign_relpath:
        lines.append(f"- **Source label (repo-relative):** `{pack.source_campaign_relpath}`")
    if pack.git_commit_sha:
        lines.append(f"- **git_commit:** `{pack.git_commit_sha}`")
    if pack.git_describe:
        lines.append(f"- **git_describe:** `{pack.git_describe}`")
    if pack.campaign_definition_fingerprint:
        lines.append(f"- **definition_fingerprint:** `{pack.campaign_definition_fingerprint}`")
    if not (
        pack.source_campaign_dir
        or pack.source_campaign_relpath
        or pack.git_commit_sha
        or pack.git_describe
        or pack.campaign_definition_fingerprint
    ):
        lines.append("_No source path or git pointers recorded on this pack._")
    lines.extend(["", "## Fingerprints (experiment axes)", ""])
    if pack.campaign_experiment_fingerprints is not None:
        cef = pack.campaign_experiment_fingerprints
        lines.extend(
            [
                f"- **campaign_definition:** `{cef.campaign_definition}`",
                f"- **suite_definitions:** `{cef.suite_definitions}`",
                f"- **provider_configs:** `{cef.provider_configs}`",
                f"- **scoring_configs:** `{cef.scoring_configs}`",
                f"- **browser_configs:** `{cef.browser_configs}`",
                f"- **prompt_registry_state:** `{cef.prompt_registry_state}`",
            ],
        )
    else:
        lines.append("_No campaign experiment fingerprints on the source manifest._")

    lines.extend(
        [
            "",
            "## Member runs included",
            "",
            "| run_index | run_id | suite | benchmark_id | manifest in pack |",
            "| ---: | --- | --- | --- | --- |",
        ],
    )
    for m in pack.member_runs:
        lines.append(
            f"| {m.run_index} | `{m.run_id}` | `{m.suite_ref}` | `{m.benchmark_id}` | "
            f"`{m.manifest_relpath}` |",
        )
    if not pack.member_runs:
        lines.append("| — | — | — | — | — |")

    lines.extend(
        [
            "",
            "## Comparing two packs",
            "",
            "1. **Identity:** `pack_identity_fingerprint` matches when the same logical bundle "
            "was assembled (ignores `pack_id`, pack `created_at`, `notes`).",
            "2. **Experiment:** same **`campaign_experiment_fingerprints`** ⇒ same sweep inputs.",
            "3. **Results:** diff summaries, `reports/campaign-report.md`, semantic summary, "
            "`reports/campaign-analysis.json`.",
            "4. **Members:** compare `runs/runNNNN/` trees.",
            "5. **Tree:** `diff -ru packA packB` (skip `INDEX.md` if only timestamp churn).",
            "",
            "## Validate",
            "",
            "```bash",
            "alwm validate campaign-result-pack.json campaign_result_pack",
            "alwm validate manifest.json campaign_manifest",
            "alwm validate campaign-summary.json campaign_summary",
            "alwm benchmark campaign pack-check .",
            "alwm benchmark campaign pack-check . --strict",
            "```",
            "",
            "## Longitudinal analysis",
            "",
            "`alwm benchmark longitudinal` uses **`ALWM_REPO_ROOT`** (default: cwd). "
            "For a standalone pack, `cd` into it or pass a repo-relative glob.",
            "",
            "```bash",
            "cd /path/to/this/pack",
            (
                'ALWM_REPO_ROOT="$(pwd)" alwm benchmark longitudinal '
                f"--runs-glob '{pack.longitudinal_member_glob}' --out-dir /tmp/out"
            ),
            "```",
            "",
            "```bash",
            "alwm benchmark longitudinal --runs-glob "
            f"'examples/campaign_result_packs/<pack>/{pack.longitudinal_member_glob}' "
            "--out-dir /tmp/out",
            "```",
            "",
        ],
    )
    if pack.member_depth == "manifest":
        lines.extend(
            [
                "> **`member_depth` is manifest-only:** may miss `evaluation.json` / per-cell "
                "artifacts. Re-pack with **`--member-depth full`** for full cell trees.",
                "",
            ],
        )
    if pack.notes:
        lines.extend(["## Notes", "", pack.notes, ""])
    return "\n".join(lines)
