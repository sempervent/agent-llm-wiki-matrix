# Local development workflow

## Python

1. Use Python **3.11+** (matches Docker). On macOS with Homebrew: `/opt/homebrew/bin/python3.11`.
2. Create a venv: `python3.11 -m venv .venv && source .venv/bin/activate`.
3. Install: `pip install -e ".[dev]"`.
4. Run checks: `make ci`.
5. CLI: `alwm version`, `alwm info`.

## Docker

```bash
cp .env.example .env   # optional
docker build -t agent-llm-wiki-matrix:local -f Dockerfile .
docker run --rm agent-llm-wiki-matrix:local version
```

## Docker Compose profiles

The `orchestrator` service is assigned to profiles so a bare `docker compose up` does not surprise-run workloads.

| Profile | Intended use |
| --- | --- |
| `dev` | Interactive CLI against mounted repo |
| `test` | Future: run test suite in container |
| `benchmark` | Future: benchmark harness entrypoints |

Example:

```bash
docker compose --profile dev run --rm orchestrator version
```

## Buildx Bake

- Multi-arch: `docker buildx bake` (see `docker-bake.hcl`).
- Faster single-arch: `docker buildx bake orchestrator-amd64` or `orchestrator-arm64`.

Other ARM variants (for example `linux/arm/v7`) are **not** assumed; add explicit targets and base-image validation before advertising support.
