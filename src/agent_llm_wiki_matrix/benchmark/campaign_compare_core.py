"""Shared helpers for comparing campaign outputs (packs or raw campaign directories)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent_llm_wiki_matrix.models import CampaignExperimentFingerprints


def read_json_optional(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else None


def experiment_fingerprint_axes(
    cef: CampaignExperimentFingerprints | None,
) -> dict[str, str | None]:
    if cef is None:
        return {}
    d = cef.model_dump(mode="json", exclude_none=False)
    return {k: (str(v) if v is not None else None) for k, v in d.items()}


def index_backend_mean_scores(rows: list[dict[str, Any]] | None) -> dict[str, float]:
    if not rows:
        return {}
    out: dict[str, float] = {}
    for r in rows:
        k = str(r.get("backend_kind", ""))
        if k and "mean_score" in r:
            out[k] = float(r["mean_score"])
    return out


def index_semantic_instability(rows: list[dict[str, Any]] | None) -> dict[str, int]:
    if not rows:
        return {}
    out: dict[str, int] = {}
    for r in rows:
        sb = str(r.get("scoring_backend", ""))
        if sb and "unstable_cell_events" in r:
            out[sb] = int(r["unstable_cell_events"])
    return out


def failure_tags_map(rows: list[dict[str, Any]] | None) -> dict[str, int]:
    if not rows:
        return {}
    out: dict[str, int] = {}
    for r in rows:
        c = r.get("code")
        n = r.get("signal_count")
        if c is not None and n is not None:
            out[str(c)] = int(n)
    return out


def semantic_summary_totals_slice(sem: dict[str, Any] | None) -> dict[str, Any] | None:
    if sem is None:
        return None
    t = sem.get("totals")
    if not isinstance(t, dict):
        return None
    keys = (
        "cells_total",
        "cells_semantic_or_hybrid",
        "cells_with_repeat_judge",
        "low_confidence_cells",
        "cells_flagged_judge_low_confidence",
        "cells_flagged_repeat_confidence_low",
        "max_range_across_campaign",
    )
    return {k: t.get(k) for k in keys if k in t}


def _browser_evidence_member_rows(analysis: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not analysis:
        return []
    raw = analysis.get("browser_evidence_member_cells")
    if not isinstance(raw, list):
        return []
    return [x for x in raw if isinstance(x, dict)]


def _cell_key_for_browser_row(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("suite_ref") or ""),
        str(row.get("cell_id") or ""),
        str(row.get("benchmark_id") or ""),
    )


def _index_browser_evidence_by_cell_key(
    rows: list[dict[str, Any]],
) -> tuple[dict[tuple[str, str, str], dict[str, Any]], list[str]]:
    """One row per (suite_ref, cell_id, benchmark_id); later duplicates are skipped with a note."""
    out: dict[tuple[str, str, str], dict[str, Any]] = {}
    notes: list[str] = []
    for row in rows:
        k = _cell_key_for_browser_row(row)
        if k in out:
            notes.append(
                "duplicate browser_evidence_member_cells row for "
                f"suite_ref={k[0]!r} cell_id={k[1]!r} benchmark_id={k[2]!r}; "
                f"keeping run_id={out[k].get('run_id')!r}, "
                f"skipping run_id={row.get('run_id')!r}",
            )
            continue
        out[k] = row
    return out, notes


def build_browser_evidence_member_cells_comparison_block(
    left: dict[str, Any] | None,
    right: dict[str, Any] | None,
) -> dict[str, Any]:
    """Pair ``browser_evidence_member_cells`` rows by (suite_ref, cell_id, benchmark_id).

    Counts and digests come from deterministic fixture/mock traces in analysis JSON.
    **Playwright** is optional for live capture; when **runner** appears in
    ``extension_keys``, inspect raw ``browser_evidence`` artifacts for **mcp_stdio**
    vs other runners (local MCP uses a **stdio JSON bridge**, not a remote session).
    """
    lrows = _browser_evidence_member_rows(left)
    rrows = _browser_evidence_member_rows(right)
    li, lnotes = _index_browser_evidence_by_cell_key(lrows)
    ri, rnotes = _index_browser_evidence_by_cell_key(rrows)
    index_notes = [*lnotes, *rnotes]

    all_keys = set(li) | set(ri)
    paired_rows: list[dict[str, Any]] = []
    for key in sorted(all_keys):
        suite_ref, cell_id, benchmark_id = key
        lrow = li.get(key)
        rrow = ri.get(key)
        entry: dict[str, Any] = {
            "suite_ref": suite_ref,
            "cell_id": cell_id,
            "benchmark_id": benchmark_id,
        }
        if lrow and rrow:
            entry["pairing"] = "both"
            ld = int(lrow.get("dom_excerpt_count") or 0)
            rd = int(rrow.get("dom_excerpt_count") or 0)
            ls = int(lrow.get("screenshot_count") or 0)
            rs_ = int(rrow.get("screenshot_count") or 0)
            lext = set(lrow.get("extension_keys") or [])
            rext = set(rrow.get("extension_keys") or [])
            entry.update(
                {
                    "run_id_left": lrow.get("run_id"),
                    "run_id_right": rrow.get("run_id"),
                    "evidence_id_left": lrow.get("evidence_id"),
                    "evidence_id_right": rrow.get("evidence_id"),
                    "evidence_id_match": lrow.get("evidence_id") == rrow.get("evidence_id"),
                    "browser_runner_left": lrow.get("browser_runner"),
                    "browser_runner_right": rrow.get("browser_runner"),
                    "browser_runner_match": lrow.get("browser_runner")
                    == rrow.get("browser_runner"),
                    "dom_excerpt_count_left": ld,
                    "dom_excerpt_count_right": rd,
                    "dom_delta_right_minus_left": rd - ld,
                    "screenshot_count_left": ls,
                    "screenshot_count_right": rs_,
                    "screenshot_delta_right_minus_left": rs_ - ls,
                    "signals_digest_left": lrow.get("signals_digest"),
                    "signals_digest_right": rrow.get("signals_digest"),
                    "extension_digest_left": lrow.get("extension_digest"),
                    "extension_digest_right": rrow.get("extension_digest"),
                    "extension_keys_only_left": sorted(lext - rext),
                    "extension_keys_only_right": sorted(rext - lext),
                    "extension_keys_intersection": sorted(lext & rext),
                    "has_dom_snapshot_ref_left": lrow.get("has_dom_snapshot_ref"),
                    "has_dom_snapshot_ref_right": rrow.get("has_dom_snapshot_ref"),
                    "runner_extension_key_left": "runner" in lext,
                    "runner_extension_key_right": "runner" in rext,
                },
            )
        elif lrow:
            entry["pairing"] = "left_only"
            entry["run_id_left"] = lrow.get("run_id")
            entry["evidence_id_left"] = lrow.get("evidence_id")
            entry["browser_runner_left"] = lrow.get("browser_runner")
            entry["dom_excerpt_count_left"] = int(lrow.get("dom_excerpt_count") or 0)
            entry["screenshot_count_left"] = int(lrow.get("screenshot_count") or 0)
            entry["signals_digest_left"] = lrow.get("signals_digest")
            entry["extension_digest_left"] = lrow.get("extension_digest")
            entry["extension_keys_left"] = sorted(lrow.get("extension_keys") or [])
            entry["runner_extension_key_left"] = "runner" in set(lrow.get("extension_keys") or [])
        else:
            entry["pairing"] = "right_only"
            rrow = ri[key]
            entry["run_id_right"] = rrow.get("run_id")
            entry["evidence_id_right"] = rrow.get("evidence_id")
            entry["browser_runner_right"] = rrow.get("browser_runner")
            entry["dom_excerpt_count_right"] = int(rrow.get("dom_excerpt_count") or 0)
            entry["screenshot_count_right"] = int(rrow.get("screenshot_count") or 0)
            entry["signals_digest_right"] = rrow.get("signals_digest")
            entry["extension_digest_right"] = rrow.get("extension_digest")
            entry["extension_keys_right"] = sorted(rrow.get("extension_keys") or [])
            entry["runner_extension_key_right"] = "runner" in set(
                rrow.get("extension_keys") or [],
            )
        paired_rows.append(entry)

    l_run_ids = {str(x.get("run_id")) for x in lrows if x.get("run_id")}
    r_run_ids = {str(x.get("run_id")) for x in rrows if x.get("run_id")}

    lt_dom = sum(int(x.get("dom_excerpt_count") or 0) for x in lrows)
    rt_dom = sum(int(x.get("dom_excerpt_count") or 0) for x in rrows)
    lt_sh = sum(int(x.get("screenshot_count") or 0) for x in lrows)
    rt_sh = sum(int(x.get("screenshot_count") or 0) for x in rrows)

    return {
        "left_row_count": len(lrows),
        "right_row_count": len(rrows),
        "left_unique_cell_keys": len(li),
        "right_unique_cell_keys": len(ri),
        "aggregate": {
            "left_total_dom_excerpts": lt_dom,
            "right_total_dom_excerpts": rt_dom,
            "left_total_screenshots": lt_sh,
            "right_total_screenshots": rt_sh,
            "delta_dom_excerpts_right_minus_left": rt_dom - lt_dom,
            "delta_screenshots_right_minus_left": rt_sh - lt_sh,
        },
        "run_ids": {
            "left": sorted(l_run_ids),
            "right": sorted(r_run_ids),
            "only_in_left": sorted(l_run_ids - r_run_ids),
            "only_in_right": sorted(r_run_ids - l_run_ids),
        },
        "paired_rows": paired_rows,
        "keys_only_in_left": sorted(
            {" / ".join(k) for k in (set(li) - set(ri))},
        ),
        "keys_only_in_right": sorted(
            {" / ".join(k) for k in (set(ri) - set(li))},
        ),
        "index_notes": index_notes,
        "has_any_evidence": bool(lrows or rrows),
    }


def render_browser_evidence_member_cells_comparison_markdown(
    be: dict[str, Any] | None,
    *,
    top_heading_level: int = 3,
) -> str:
    """Markdown subsection for pack/directory compare reports.

    Use ``top_heading_level=3`` under **## Comparative analysis** (pack compare);
    use ``top_heading_level=2`` as a top-level section in directory compare.
    """
    if not be or not be.get("has_any_evidence"):
        return ""
    prefix = "#" * max(1, min(top_heading_level, 6))
    lines = [
        f"{prefix} Browser evidence (`browser_evidence_member_cells`)",
        "",
        (
            "Deterministic **DOM excerpt counts**, **screenshot counts**, "
            "**signals/extension digests** (per cell), and **extension key** sets from each "
            "side's `campaign-analysis.json`. These reflect **fixture/mock** traces unless you "
            "ran a live browser — **Playwright** remains optional. When **`runner`** appears "
            "under **extension keys**, inspect the cell's **`browser_evidence`** JSON for "
            "**`extensions.runner`** (e.g. **`mcp_stdio`**) — that is a **local MCP stdio** "
            "JSON bridge, not a hosted remote browser."
        ),
        "",
    ]
    agg = be.get("aggregate") or {}
    lines.extend(
        [
            "**Rollups (analysis rows, not scored cells):**",
            "",
            f"- **Left:** {be['left_row_count']} row(s), **Σ DOM excerpts:** "
            f"{agg.get('left_total_dom_excerpts', 0)}, **Σ screenshots:** "
            f"{agg.get('left_total_screenshots', 0)}",
            f"- **Right:** {be['right_row_count']} row(s), **Σ DOM excerpts:** "
            f"{agg.get('right_total_dom_excerpts', 0)}, **Σ screenshots:** "
            f"{agg.get('right_total_screenshots', 0)}",
            f"- **Δ (R−L):** DOM excerpts **{agg.get('delta_dom_excerpts_right_minus_left', 0)}**, "
            f"screenshots **{agg.get('delta_screenshots_right_minus_left', 0)}**",
            "",
        ],
    )
    rid = be.get("run_ids") or {}
    oil = rid.get("only_in_left") or []
    oir = rid.get("only_in_right") or []
    if oil:
        lines.append(
            f"- **Member run_ids with evidence only on left:** "
            f"{', '.join(f'`{x}`' for x in oil)}",
        )
    if oir:
        lines.append(
            f"- **Member run_ids with evidence only on right:** "
            f"{', '.join(f'`{x}`' for x in oir)}",
        )
    if oil or oir:
        lines.append("")

    notes = be.get("index_notes") or []
    if notes:
        lines.append("_Indexing notes:_")
        for n in notes:
            lines.append(f"- {n}")
        lines.append("")

    pr = be.get("paired_rows") or []
    lines.extend(
        [
            "**Per-cell pairing** uses `(suite_ref, cell_id, benchmark_id)`. "
            "**Signals** = navigation/console/DOM/screenshot counts; **extension digest** "
            "summarizes network/a11y/**trace_digest** (opaque hash of captured stdio/tooling), "
            "not remote IDE MCP.",
            "",
            "| suite_ref | cell_id | Pairing | L DOM | R DOM | Δ DOM | L shot | R shot | Δ shot | "
            "Runner L | Runner R | Signals (L / R) | Extension digest (L / R) |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |",
        ],
    )
    for row in pr:
        suite = row.get("suite_ref") or "—"
        cid = row.get("cell_id") or "—"
        pairing = row.get("pairing") or "—"
        if pairing == "both":
            ld = row.get("dom_excerpt_count_left")
            rd = row.get("dom_excerpt_count_right")
            ddom = row.get("dom_delta_right_minus_left")
            ls = row.get("screenshot_count_left")
            rs_ = row.get("screenshot_count_right")
            ds = row.get("screenshot_delta_right_minus_left")
            brl = row.get("browser_runner_left") or "—"
            brr = row.get("browser_runner_right") or "—"
            sig_l = row.get("signals_digest_left") or "—"
            sig_r = row.get("signals_digest_right") or "—"
            ext_l = row.get("extension_digest_left") or "—"
            ext_r = row.get("extension_digest_right") or "—"
            lines.append(
                f"| `{suite}` | `{cid}` | both | {ld} | {rd} | {ddom} | {ls} | {rs_} | {ds} | "
                f"`{brl}` | `{brr}` | {sig_l} / {sig_r} | {ext_l} / {ext_r} |",
            )
        elif pairing == "left_only":
            ld = row.get("dom_excerpt_count_left")
            ls = row.get("screenshot_count_left")
            sig_l = row.get("signals_digest_left") or "—"
            ext_l = row.get("extension_digest_left") or "—"
            brl = row.get("browser_runner_left") or "—"
            lines.append(
                f"| `{suite}` | `{cid}` | left only | {ld} | — | — | {ls} | — | — | "
                f"`{brl}` | — | {sig_l} / — | {ext_l} / — |",
            )
        else:
            rd = row.get("dom_excerpt_count_right")
            rs_ = row.get("screenshot_count_right")
            sig_r = row.get("signals_digest_right") or "—"
            ext_r = row.get("extension_digest_right") or "—"
            brr = row.get("browser_runner_right") or "—"
            lines.append(
                f"| `{suite}` | `{cid}` | right only | — | {rd} | — | — | {rs_} | — | "
                f"— | `{brr}` | — / {sig_r} | — / {ext_r} |",
            )

    kol = be.get("keys_only_in_left") or []
    kor = be.get("keys_only_in_right") or []
    if kol or kor:
        lines.append("")
        lines.append("**Unpaired cell keys** (present on one side only): ")
        parts: list[str] = []
        if kol:
            parts.append("left → " + ", ".join(f"`{x}`" for x in kol))
        if kor:
            parts.append("right → " + ", ".join(f"`{x}`" for x in kor))
        lines.append("; ".join(parts))

    lines.append("")
    return "\n".join(lines)


def build_analysis_comparison_block(
    left: dict[str, Any] | None,
    right: dict[str, Any] | None,
) -> dict[str, Any]:
    """Diff pooled backend means, semantic instability counts, extremes flag from analysis JSON."""
    lb = index_backend_mean_scores(left.get("backend_performance") if left else None)
    rb = index_backend_mean_scores(right.get("backend_performance") if right else None)
    backends = sorted(set(lb) | set(rb))
    backend_rows: list[dict[str, Any]] = []
    for bk in backends:
        lv, rv = lb.get(bk), rb.get(bk)
        delta = None
        if lv is not None and rv is not None:
            delta = round(rv - lv, 6)
        backend_rows.append(
            {
                "backend_kind": bk,
                "left_mean_score": lv,
                "right_mean_score": rv,
                "delta_right_minus_left": delta,
            },
        )

    ls = index_semantic_instability(
        left.get("semantic_instability_by_scoring_backend") if left else None,
    )
    rs = index_semantic_instability(
        right.get("semantic_instability_by_scoring_backend") if right else None,
    )
    sbs = sorted(set(ls) | set(rs))
    inst_rows: list[dict[str, Any]] = []
    for sb in sbs:
        a, b = ls.get(sb), rs.get(sb)
        inst_rows.append(
            {
                "scoring_backend": sb,
                "left_unstable_events": a,
                "right_unstable_events": b,
                "delta_right_minus_left": (None if a is None or b is None else b - a),
            },
        )

    l_ext = left.get("mean_score_extremes_by_sweep_axis") if left else None
    r_ext = right.get("mean_score_extremes_by_sweep_axis") if right else None
    comparable = None
    if isinstance(l_ext, dict) and isinstance(r_ext, dict):
        comparable = l_ext.get("comparable") == r_ext.get("comparable")

    return {
        "left_present": left is not None,
        "right_present": right is not None,
        "backend_performance": backend_rows,
        "semantic_instability_by_scoring_backend": inst_rows,
        "mean_score_extremes_comparable_flag_match": comparable,
        "browser_evidence_comparison": build_browser_evidence_member_cells_comparison_block(
            left,
            right,
        ),
    }


def build_semantic_comparison_block(
    left: dict[str, Any] | None,
    right: dict[str, Any] | None,
) -> dict[str, Any]:
    lt = semantic_summary_totals_slice(left)
    rt = semantic_summary_totals_slice(right)
    deltas: dict[str, Any] = {}
    if lt and rt:
        keys = sorted(set(lt) & set(rt))
        for k in keys:
            a, b = lt.get(k), rt.get(k)
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                deltas[k] = round(float(b) - float(a), 6)
            elif a != b:
                deltas[k] = {"left": a, "right": b}
    return {
        "left_totals": lt,
        "right_totals": rt,
        "numeric_deltas_right_minus_left": deltas,
    }


def build_failure_tag_comparison_block(
    left: dict[str, Any] | None,
    right: dict[str, Any] | None,
) -> dict[str, Any]:
    lm = failure_tags_map(left.get("failure_tag_counts") if left else None)
    rm = failure_tags_map(right.get("failure_tag_counts") if right else None)
    codes = sorted(set(lm) | set(rm))
    rows: list[dict[str, Any]] = []
    for c in codes:
        a, b = lm.get(c), rm.get(c)
        rows.append(
            {
                "code": c,
                "left_signal_count": a,
                "right_signal_count": b,
                "delta_right_minus_left": (None if a is None or b is None else b - a),
            },
        )
    return {
        "codes_compared": rows,
        "only_in_left": sorted([c for c in lm if c not in rm]),
        "only_in_right": sorted([c for c in rm if c not in lm]),
    }


def member_run_ids_diff(left_ids: set[str], right_ids: set[str]) -> dict[str, Any]:
    return {
        "left_count": len(left_ids),
        "right_count": len(right_ids),
        "run_ids_only_in_left": sorted(left_ids - right_ids),
        "run_ids_only_in_right": sorted(right_ids - left_ids),
        "run_ids_in_both": sorted(left_ids & right_ids),
    }
