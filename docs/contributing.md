# Contributing

## Operating manual

The full **contribution loop**, decision rules, prompt registry policy, and verification expectations live in **`AGENTS.md`** at the repository root (not duplicated in this site):

- **[AGENTS.md on GitHub](https://github.com/sempervent/agent-llm-wiki-matrix/blob/main/AGENTS.md)**

Use that file as the authoritative guide for coding agents and humans.

## Local setup (uv)

The repository standard is **[uv](https://docs.astral.sh/uv/)** — see **`AGENTS.md`** and [Local development](workflows/local-dev.md).

Install the package with development and documentation extras:

```bash
uv pip install -e ".[dev,docs]"
```

Then run checks and the documentation site:

```bash
uv run just ci
just docs
```

Details: [Documentation site handbook](workflows/docs-site.md). Pull requests that change `docs/**` or `mkdocs.yml` run **`.github/workflows/docs.yml`** (MkDocs strict build; optional **GitHub Pages** deploy from `main`).
