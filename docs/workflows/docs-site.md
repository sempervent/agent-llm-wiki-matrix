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

**Publication nav (v0.2.5):** The **`Publication (v0.2.5)`** nav block orders: **result-pack checklist** → **tracking v0.2.5** (merge order) → **benchmark campaigns** → **campaign walkthrough** → **reporting pipeline** (`alwm report` / matrices) → **verification** → **longitudinal** → **publication audit**. **`tracking/v0.2.5-campaign.md`** appears **only** here (not duplicated under **Tracking**, to avoid two sidebar entries to the same URL). Closed **`tracking/v0.2.4-campaign.md`** is listed under **Tracking** for history.

---

## Adding or updating pages

1. Add or edit Markdown under **`docs/`** (e.g. `docs/workflows/my-topic.md`).
2. Add an entry under **`nav:`** in **`mkdocs.yml`** so the page appears in the sidebar (and is discoverable).
3. Run **`just docs-build`** (strict) and fix any issues.
4. Prefer **relative links** between pages under `docs/` (e.g. `[Verification](verification.md)` from `docs/workflows/`).

Do **not** duplicate long procedural content — **link** to [Campaign result pack publication](campaign-result-pack-publication.md) and [Benchmark campaigns](benchmark-campaigns.md).

---

## CI (GitHub Actions)

**`.github/workflows/docs.yml`** runs when **`docs/**`**, **`mkdocs.yml`**, or the workflow file changes:

1. **`uv sync --frozen --extra docs`**
2. **`uv run mkdocs build --strict`**
3. Uploads **`site/`** as a workflow artifact
4. On **`push` to `main`**, deploys to the **`gh-pages`** branch (optional **GitHub Pages** — enable in repo settings)

**`just ci`** does **not** run MkDocs; the GitHub workflow is the shared gate for site builds.

---

## Implementation and verification findings

This section records what was learned when implementing and running MkDocs in this repository (not chat-only — update it when behavior changes).

### What succeeded

- **`mkdocs build --strict`** completes reliably (order-of-magnitude **~1–3s** locally for the current page set, depending on cache).
- **Material for MkDocs** theme provides search, tabs, and readable defaults for technical docs.
- **Navigation** groups **publication + reports** workflows at the top; **Home** (`docs/index.md`) uses a tip admonition pointing at the operator checklist and links the handbook.
- **`just docs`** / **`just docs-build`** wrap **`uv run --extra docs`** so an activated venv is optional.
- **Repository on GitHub** nav entries avoid duplicating **`README.md`** / **`CHANGELOG.md`** / **`AGENTS.md`** inside the static site.
- **CI** (`.github/workflows/docs.yml`) matches local build commands: **`uv sync --frozen --extra docs`**, **`uv run mkdocs build --strict`**, path filters **`docs/**`**, **`mkdocs.yml`**, workflow file; artifact name **`mkdocs-site`** (historical label; contains `site/`).

### What was awkward

- **Links outside `docs/`:** Many existing pages use paths like **`../../README.md`**, **`../../examples/`**, **`../../tests/`** so the same files render correctly on **GitHub**. Those targets are **not** in the MkDocs doc tree. **`mkdocs.yml`** sets **`validation.links.not_found: ignore`** so **`--strict`** builds do not fail on those links. **Trade-off:** the static site does not “fix” those links; readers use GitHub or the nav’s external links.
- **Uv extras:** A **docs-only** install is enough to build the site but **not** to run **`just ci`**. Contributors editing Python and docs should use **`.[dev,docs]`** (or equivalent **`uv sync`** flags).
- **Material noise:** **Material** may print a **MkDocs 2.0** informational banner on **serve** / **build**. The project pins **`mkdocs>=1.6,<2`**; the banner is upstream messaging, not a build failure.
- **Nav vs. duplicate files:** The same `.md` file should not appear twice under **`nav:`** (duplicate sidebar/search hits). **Resolved:** **`tracking/v0.2.5-campaign.md`** is listed only under **Publication (v0.2.5)**; **`workflows/reporting.md`** is listed only under **Publication** (removed from the generic **Workflows** list to avoid duplication). **Roadmap** lists **v0.2.5 (active)** and prior milestones.
- **`validation.links.not_found: ignore`** (in **`mkdocs.yml`**) keeps **`--strict`** from failing on **`../../README.md`**-style links that only resolve on GitHub.

### Intentionally deferred

- Running **`mkdocs build`** inside default **`just ci`** (keeps local CI fast; **GitHub Actions** covers docs).
- Tightening **`validation.links`** for *internal* `docs/` links only (would need a custom plugin or disciplined link hygiene).
- Setting **`site_url`** in **`mkdocs.yml`** until a canonical public Pages URL is fixed.
- Inlining repository-root Markdown into the site (would duplicate source of truth).

### Docs that are still hard to surface cleanly

| Content | Why |
| --- | --- |
| **Root `README` / `AGENTS` / `CHANGELOG`** | Not under **`docs_dir`**; kept as **Repository on GitHub** links. |
| **Repo `examples/` trees** | Only **`docs/examples/README.md`** explains the pointer; deep files stay GitHub-only unless mirrored. |
| **`docs/implementation-log.md`** | Large, chronological; listed under **Project** for agents, not duplicated in Publication. |

### Conventions for agents (avoid MkDocs drift)

1. **Nav:** Any new **user-facing** doc under **`docs/`** that should appear in the sidebar must be added to **`mkdocs.yml`** **`nav:`**.
2. **Links:** Prefer **relative** links between `docs/` pages; keep **GitHub**-style `../../` links only when the paragraph is meant to read equally on github.com.
3. **Publication story:** If you add a new **primary** step to the E2E publication flow, update **[campaign-result-pack-publication.md](campaign-result-pack-publication.md)** and consider a one-line pointer on **`docs/index.md`** and/or the **Publication** nav block.
4. **CI:** If **`mkdocs.yml`** or **`docs/`** structure changes, confirm **`.github/workflows/docs.yml`** path filters still match.
5. **Handbook:** Update **this file** (`docs-site.md`) when verification steps or known limitations change.

---

## Relation to publication workflows

- **Operator checklist:** [Campaign result pack publication](campaign-result-pack-publication.md)
- **CLI / artifacts:** [Benchmark campaigns](benchmark-campaigns.md)
- **Matrix / `alwm report` (non-campaign):** [Reporting](reporting.md)
- **CI matrix:** [Verification](verification.md)
- **Regression views:** [Longitudinal reporting](longitudinal-reporting.md)

The site **indexes** these; it does not replace them.

---

## Filename

Canonical handbook path: **`docs/workflows/docs-site.md`**. Older references to **`mkdocs-site.md`** should be updated to this path.
