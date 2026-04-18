# Documentation

This site is generated with **[MkDocs](https://www.mkdocs.org/)** and the **[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)** theme. The **source of truth** remains the Markdown files in the repository (`docs/`, plus root `README.md`, `AGENTS.md`, and `CHANGELOG.md`).

!!! tip "Start here — end-to-end publication (v0.2.5)"
    **Operator checklist:** **[Campaign result pack publication](workflows/campaign-result-pack-publication.md)** — *run → validate → pack → compare → publish* with committed examples.

    **Milestone:** **[Roadmap v0.2.5](roadmap/v0.2.5.md)** · **[Tracking v0.2.5](tracking/v0.2.5-campaign.md)** · shipped **[v0.2.4](releases/v0.2.4.md)** · **[Publication workflow audit](audits/v0.2.4-publication-workflow-audit.md)** (evidence-driven gaps).

    **Site handbook (nav, CI, findings):** **[Documentation site](workflows/docs-site.md)**.

## Publication workflow at a glance

| Step | Doc |
| --- | --- |
| **1. CLI & artifact reference** | [Benchmark campaigns](workflows/benchmark-campaigns.md) — `campaign run`, `pack`, `pack-check`, `compare-packs`, `compare` |
| **2. Operator checklist** | [Campaign result pack publication](workflows/campaign-result-pack-publication.md) |
| **3. Matrix & Markdown reports (non-campaign)** | [Reporting pipeline](workflows/reporting.md) — `alwm report`, matrices |
| **4. CI & drift** | [Verification](workflows/verification.md) — `just ci`, `validate-artifacts` |
| **5. Fingerprints & regression** | [Longitudinal reporting](workflows/longitudinal-reporting.md) |
| **6. Walk committed trees** | [Campaign walkthrough](workflows/campaign-walkthrough.md) |

## Milestones & releases

| | |
| --- | --- |
| **Active roadmap** | [v0.2.5](roadmap/v0.2.5.md) |
| **Prior release notes** | [v0.2.4](releases/v0.2.4.md) · [v0.2.3](releases/v0.2.3.md) · [v0.2.2](releases/v0.2.2.md) · [v0.2.1](releases/v0.2.1.md) |
| **Arc (fingerprints & campaigns)** | [v0.2.0 roadmap](roadmap/v0.2.0.md) |

## Browse by area

- **Workflows** — [Benchmarking](workflows/benchmarking.md), [reporting](workflows/reporting.md) (also under **Publication** in the site nav), [local dev](workflows/local-dev.md), [smoke](workflows/smoke.md), [multi-agent parallel](workflows/multi-agent-parallel.md), **[Documentation site handbook](workflows/docs-site.md)** (nav, CI, findings).
- **Architecture** — [Data model](architecture/data-model.md), [browser](architecture/browser.md), [runtime](architecture/runtime.md).
- **Audits** — [Capability classification](audits/capability-classification.md), [schema drift inventory](audits/schema-drift-contracts-inventory.md).
- **Tracking** — [Campaign orchestration](tracking/campaign-orchestration.md), [v0.2.5 tracking](tracking/v0.2.5-campaign.md), [v0.2.4 tracking (closed)](tracking/v0.2.4-campaign.md).

## Repository files on GitHub

Canonical root files are **not** duplicated in this build; open them on GitHub:

- [README.md](https://github.com/sempervent/agent-llm-wiki-matrix/blob/main/README.md)
- [AGENTS.md](https://github.com/sempervent/agent-llm-wiki-matrix/blob/main/AGENTS.md)
- [CHANGELOG.md](https://github.com/sempervent/agent-llm-wiki-matrix/blob/main/CHANGELOG.md)

See [Contributing](contributing.md) for uv setup (`[dev,docs]`) and `just docs`.
