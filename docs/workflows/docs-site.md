# Documentation site (MkDocs)

This is the **handbook** for the repository’s **MkDocs**-generated documentation site. It supports the **v0.2.5** mission: **publication-quality evidence packs and final report readability** — the site surfaces campaign, pack, compare, and verification docs in the sidebar without making a second copy of their content.

**Single source of truth:** Markdown under **`docs/`** (plus repository-root **`README.md`**, **`AGENTS.md`**, **`CHANGELOG.md`** for GitHub-first reading). Configuration lives in **`mkdocs.yml`** at the repo root.

---

## Prerequisites (uv)

```bash
uv pip install -e ".[docs]"
```

Full contributor parity (lint, tests, MkDocs):

```bash
uv pip install -e ".[dev,docs]"
```

**Note:** `uv sync --frozen --extra docs` (as in CI) installs **only** the `docs` extra — adequate for **`mkdocs build`**, but **not** for **`just ci`** (you need **`--extra dev`** for Ruff, Mypy, pytest, stubs).

---

## Local commands

| Goal | Command |
| --- | --- |
| **Live preview** | **`just docs`** → `uv run --extra docs mkdocs serve -a 127.0.0.1:8000` |
| **Static build** | **`just docs-build`** → `uv run --extra docs mkdocs build --strict` |

Open the URL MkDocs prints (default **http://127.0.0.1:8000/**). Output of a build is **`site/`** (gitignored).

---

## Configuration and navigation

| Item | Location |
| --- | --- |
| MkDocs config | **`mkdocs.yml`** (repository root) |
| Source Markdown | **`docs/`** |
| **Navigation** | **`nav:`** in **`mkdocs.yml`** — **this is the sidebar**; pages not listed may be omitted from the nav (depending on MkDocs version/settings). |
| Generated output | **`site/`** (do not commit) |
| CI workflow | **`.github/workflows/docs.yml`** |

**Publication nav (v0.2.5):** The **`Publication & reports (v0.2.5)`** sidebar block orders: **E2E checklist** → **tracking v0.2.5** (merge order) → **benchmark campaigns** (pack / `compare-packs` / `compare`) → **campaign walkthrough** → **reporting pipeline** (`alwm report` / matrices) → **verification** (`just ci`, `validate-artifacts`) → **longitudinal** → **v0.2.4 publication audit** → **examples index** (`docs/examples/README.md` → repo `examples/`). **Roadmap theme** for v0.2.5 lives under **Roadmap & milestones** only (not duplicated here). **`tracking/v0.2.5-campaign.md`** appears **only** under **Publication & reports** (not again under **Tracking**, to avoid two sidebar hits for the same URL).

---

## Adding or updating pages

1. Add or edit Markdown under **`docs/`** (e.g. `docs/workflows/my-topic.md`).
2. Add an entry under **`nav:`** in **`mkdocs.yml`** so the page appears in the sidebar (and is discoverable).
3. Run **`just docs-build`** (strict) and fix any issues.
4. Prefer **relative links** between pages under `docs/` (e.g. `[Verification](verification.md)` from `docs/workflows/`).

Do **not** duplicate long procedural content — **link** to [Campaign result pack publication](campaign-result-pack-publication.md) and [Benchmark campaigns](benchmark-campaigns.md).

---

## CI (GitHub Actions)

**`.github/workflows/docs.yml`** runs when **`docs/**`**, **`mkdocs.yml`**, or the workflow file changes (and can be run manually via **Actions → Documentation → Run workflow** on **`main`**):

1. **`uv sync --frozen --extra docs`**
2. **`uv run mkdocs build --strict`**
3. Uploads **`site/`** as a workflow artifact (**`mkdocs-site`**) for debugging and PRs.
4. On **`push` to `main`** (or **`workflow_dispatch`** on **`main`**), uploads the **Pages** artifact and runs **`actions/deploy-pages`** to publish the site.

**GitHub Pages settings (required once per repo):** **Settings → Pages → Build and deployment → Source:** choose **GitHub Actions** (not “Deploy from a branch”). The older **`gh-pages`** branch flow is a different mechanism and does not apply to this workflow.

**Public URL:** **`https://sempervent.github.io/agent-llm-wiki-matrix/`** — **`mkdocs.yml`** sets **`site_url`** to this base so links and theme assets resolve under the project path.

**`just ci`** does **not** run MkDocs; the GitHub workflow is the shared gate for site builds.

---

## Implementation and verification findings

This section records what was learned when implementing and running MkDocs in this repository (not chat-only — update it when behavior changes).

### What succeeded

- **`mkdocs build --strict`** completes reliably (order-of-magnitude **~1–3s** locally for the current page set, depending on cache).
- **Material for MkDocs** theme provides search, tabs, and readable defaults for technical docs.
- **Navigation** groups **Publication & reports (v0.2.5)** at the top with explicit labels for E2E checklist, merge-order tracking, CLI/compare, verification, longitudinal, examples index; **Home** (`docs/index.md`) ties the tip block to sidebar naming and adds an examples row to the glance table.
- **`just docs`** / **`just docs-build`** wrap **`uv run --extra docs`** so an activated venv is optional.
- **Repository on GitHub** nav entries avoid duplicating **`README.md`** / **`CHANGELOG.md`** / **`AGENTS.md`** inside the static site.
- **CI** (`.github/workflows/docs.yml`) matches local build commands: **`uv sync --frozen --extra docs`**, **`uv run mkdocs build --strict`**, path filters **`docs/**`**, **`mkdocs.yml`**, workflow file; artifact name **`mkdocs-site`** (historical label; contains `site/`).

### v0.2.5 docs-site pass (navigation polish)

| Finding | Change |
| --- | --- |
| Top nav name **Publication (v0.2.5)** did not spell out “reports” or CLI compare verbs | Renamed block to **Publication & reports (v0.2.5)**; lengthened child labels (`compare-packs`, `compare`, `validate-artifacts`). |
| **Examples index** sat alone at the bottom of the nav, far from publication flow | Moved **`docs/examples/README.md`** under **Publication & reports** as **Examples index (repo examples/)**; removed duplicate top-level entry. |
| **Roadmap v0.2.5** could be confused with merge-order **tracking** | Kept **roadmap** only under **Roadmap & milestones**; home page tip clarifies theme vs merge-order doc. |
| **Documentation site** handbook label was generic | Renamed nav label to **Documentation site (MkDocs nav & CI)**. |

**Deferred:** duplicate **tracking/v0.2.5** under **Tracking** (would double sidebar links to the same URL); readers use **Publication & reports** or **Home** tip instead.

### What was awkward

- **Links outside `docs/`:** Many existing pages use paths like **`../../README.md`**, **`../../examples/`**, **`../../tests/`** so the same files render correctly on **GitHub**. Those targets are **not** in the MkDocs doc tree. **`mkdocs.yml`** sets **`validation.links.not_found: ignore`** so **`--strict`** builds do not fail on those links. **Trade-off:** the static site does not “fix” those links; readers use GitHub or the nav’s external links.
- **Uv extras:** A **docs-only** install is enough to build the site but **not** to run **`just ci`**. Contributors editing Python and docs should use **`.[dev,docs]`** (or equivalent **`uv sync`** flags).
- **Material noise:** **Material** may print a **MkDocs 2.0** informational banner on **serve** / **build**. The project pins **`mkdocs>=1.6,<2`**; the banner is upstream messaging, not a build failure.
- **Nav vs. duplicate files:** The same `.md` file should not appear twice under **`nav:`** (duplicate sidebar/search hits). **Policy:** **`tracking/v0.2.5-campaign.md`** is listed only under **Publication & reports**; **`roadmap/v0.2.5.md`** only under **Roadmap & milestones**; **`docs/examples/README.md`** only under **Publication & reports** (removed standalone **Examples index** top-level entry to reduce clutter). **`workflows/reporting.md`** appears only under **Publication & reports** (not duplicated under generic **Workflows**).
- **`validation.links.not_found: ignore`** (in **`mkdocs.yml`**) keeps **`--strict`** from failing on **`../../README.md`**-style links that only resolve on GitHub.

### Intentionally deferred

- Running **`mkdocs build`** inside default **`just ci`** (keeps local CI fast; **GitHub Actions** covers docs).
- Tightening **`validation.links`** for *internal* `docs/` links only (would need a custom plugin or disciplined link hygiene).
- Inlining repository-root Markdown into the site (would duplicate source of truth).

**`site_url`** is set in **`mkdocs.yml`** to **`https://sempervent.github.io/agent-llm-wiki-matrix/`** for published Pages builds; update it if the repo is renamed or Pages uses a custom domain.

### Docs that are still hard to surface cleanly

| Content | Why |
| --- | --- |
| **Root `README` / `AGENTS` / `CHANGELOG`** | Not under **`docs_dir`**; kept as **Repository on GitHub** links. |
| **Repo `examples/` trees** | Only **`docs/examples/README.md`** explains the pointer; deep files stay GitHub-only unless mirrored. |
| **`docs/implementation-log.md`** | Large, chronological; listed under **Project** for agents, not duplicated in Publication. |

### Conventions for agents (avoid MkDocs drift)

1. **Nav:** Any new **user-facing** doc under **`docs/`** that should appear in the sidebar must be added to **`mkdocs.yml`** **`nav:`**.
2. **Links:** Prefer **relative** links between `docs/` pages; keep **GitHub**-style `../../` links only when the paragraph is meant to read equally on github.com.
3. **Publication story:** If you add a new **primary** step to the E2E publication flow, update **[campaign-result-pack-publication.md](campaign-result-pack-publication.md)** and consider a one-line pointer on **`docs/index.md`** and/or the **Publication & reports (v0.2.5)** nav block.
4. **CI:** If **`mkdocs.yml`** or **`docs/`** structure changes, confirm **`.github/workflows/docs.yml`** path filters still match.
5. **Handbook:** Update **this file** (`docs-site.md`) when verification steps or known limitations change.

---

## Relation to publication workflows

- **Operator checklist:** [Campaign result pack publication](campaign-result-pack-publication.md)
- **CLI / artifacts:** [Benchmark campaigns](benchmark-campaigns.md)
- **Matrix / `alwm report` (non-campaign):** [Reporting](reporting.md)
- **CI vs drift vs one-off validation:** [Verification](verification.md) — layers **A** (`alwm validate`), **B** (`validate-artifacts`), **C** (`just ci`)
- **Regression views:** [Longitudinal reporting](longitudinal-reporting.md)

The site **indexes** these; it does not replace them.

---

## Filename

Canonical handbook path: **`docs/workflows/docs-site.md`**. Older references to **`mkdocs-site.md`** should be updated to this path.
